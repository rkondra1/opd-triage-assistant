"""
Streamlit demo UI for the OPD Triage Assistant.

Run from the project root:
    streamlit run app/streamlit_app.py

Designed for a nurse with <=60 seconds per patient: large colour-coded result,
the red flags detected, which hard rules fired, and any data-quality warnings.
"""

from __future__ import annotations

import os
import sys

import streamlit as st

# allow `from src...` when run via `streamlit run app/streamlit_app.py`
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.predict import TriageEngine  # noqa: E402
from src.triage_rubric import DEPARTMENTS, TRIAGE_LEVELS  # noqa: E402

LEVEL_COLOR = {1: "#b71c1c", 2: "#e64a19", 3: "#f9a825", 4: "#2e7d32", 5: "#1565c0"}

st.set_page_config(page_title="OPD Triage Assistant", page_icon="+", layout="centered")


@st.cache_resource
def get_engine():
    """Load the model; if it isn't built yet (e.g. a fresh cloud deploy),
    generate the data and train it once, automatically."""
    model_path = os.path.join(PROJECT_ROOT, "models", "triage_model.joblib")
    try:
        if not os.path.exists(model_path):
            from src import generate_data, train
            with st.spinner("First run: generating synthetic data and training "
                            "the model (~15 seconds). This happens only once."):
                data_path = os.path.join(PROJECT_ROOT, "data", "intake_train.csv")
                if not os.path.exists(data_path):
                    generate_data.generate(n=30000, seed=7)
                train.main()
        return TriageEngine.load()
    except Exception as exc:  # pragma: no cover - surfaced in the UI
        return exc


engine = get_engine()

st.title("OPD Triage Assistant")
st.caption("Decision support for an overloaded outpatient department. "
           "Not a diagnosis - a nurse always has the final say.")

if isinstance(engine, Exception):
    st.error(
        "Model not found. Run these once from the project root:\n\n"
        "```\npython -m src.generate_data\npython -m src.train\n```"
    )
    st.stop()

with st.form("intake"):
    st.subheader("Patient intake")
    c1, c2, c3 = st.columns(3)
    age = c1.number_input("Age", min_value=0, max_value=120, value=45)
    sex = c2.selectbox("Sex", ["M", "F"])
    spo2 = c3.number_input("SpO2 (%)", min_value=0, max_value=100, value=98)

    c4, c5, c6 = st.columns(3)
    bp_sys = c4.number_input("BP systolic", min_value=0, max_value=300, value=120)
    bp_dia = c5.number_input("BP diastolic", min_value=0, max_value=200, value=80)
    pulse = c6.number_input("Pulse", min_value=0, max_value=300, value=78)

    temp = st.number_input("Temperature (C)", min_value=0.0, max_value=110.0,
                           value=37.0, step=0.1,
                           help="If someone typed a Fahrenheit value it will be auto-corrected.")

    complaint = st.text_area(
        "Chief complaint (free text - any language / Hinglish is fine)",
        value="seene mein dard aur pasina aa raha hai",
        height=80,
    )
    c7, c8 = st.columns(2)
    conditions = c7.text_input("Known conditions (semicolon-separated)", value="diabetes")
    meds = c8.text_input("Medications (semicolon-separated)", value="metformin")

    submitted = st.form_submit_button("Assess triage", use_container_width=True)

if submitted:
    record = {
        "age": age, "sex": sex, "bp_systolic": bp_sys, "bp_diastolic": bp_dia,
        "pulse": pulse, "temp_c": temp, "spo2": spo2,
        "chief_complaint": complaint, "known_conditions": conditions or "none",
        "medications": meds or "none",
    }
    r = engine.predict_one(record)

    if r.abstained:
        st.markdown(
            "<div style='background:#4a148c;color:white;padding:18px;"
            "border-radius:10px;font-size:22px;font-weight:700;'>"
            "CANNOT ASSESS - SEND TO NURSE NOW</div>",
            unsafe_allow_html=True,
        )
        st.info(r.abstain_reason)
    else:
        lvl = int(r.triage_level)
        color = LEVEL_COLOR[lvl]
        st.markdown(
            f"<div style='background:{color};color:white;padding:18px;"
            f"border-radius:10px;font-size:22px;font-weight:700;'>"
            f"TRIAGE LEVEL {lvl} - {r.level_name}<br>"
            f"<span style='font-size:16px;font-weight:400;'>Target: see within "
            f"{TRIAGE_LEVELS[lvl]['target_minutes']} min</span></div>",
            unsafe_allow_html=True,
        )
        st.subheader(f"Recommended department: {r.department}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Red flags detected**")
        if r.red_flags:
            for f in r.red_flags:
                st.markdown(f"- :red[{f}]")
        else:
            st.markdown("_none_")

        st.markdown("**Hard escalation rules fired**")
        if r.rules_fired:
            for rule in r.rules_fired:
                st.markdown(f"- {rule}")
        else:
            st.markdown("_none - model decision used directly_")

    with col_b:
        st.markdown("**Data-quality warnings**")
        if r.data_flags:
            for d in r.data_flags:
                st.markdown(f"- :orange[{d}]")
        else:
            st.markdown("_vitals look clean_")

        st.markdown("**Model confidence & probabilities**")
        st.write(f"Top confidence: {r.confidence:.0%}  (model alone: L{r.model_level})")
        st.bar_chart({f"L{k}": v for k, v in sorted(r.probabilities.items())})

    st.caption(
        "Safety: hard rules can only make a case MORE urgent, never less. "
        "When the model is unsure about a possible emergency, it abstains."
    )

with st.expander("Triage scale reference"):
    for lvl, info in TRIAGE_LEVELS.items():
        st.markdown(f"**Level {lvl} - {info['name']}** "
                    f"(<= {info['target_minutes']} min): {info['definition']}")
with st.expander("Departments"):
    st.write(", ".join(DEPARTMENTS))
