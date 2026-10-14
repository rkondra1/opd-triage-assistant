# OPD Triage Assistant

A safe, end-to-end triage assistant for an overloaded government-hospital
outpatient department (OPD). From a short intake form and a free-text complaint,
it assigns a **triage priority (1–5)**, recommends a **department**, and flags
**red-flag symptoms** — while being deliberately biased towards *not* missing
emergencies.

> **Problem (H1):** An OPD sees ~800 walk-ins/day with 2 doctors, seen
> first-come-first-served, so a chest-pain patient waits behind 40 mild fevers.
> The triage call is made by an overworked nurse in ~30 seconds. Make that call
> safer — without labs, imaging, or ECG, using only the intake form.

## Why this project is interesting

The naive approach (train a classifier, maximise accuracy) **fails safely-but-
uselessly**: it nails the 96% of easy cases and quietly under-triages the ~4%
true emergencies that matter. This project is built around that trap:

| Requirement | Where it lives |
|-------------|----------------|
| Triage level + department + red flags | `src/predict.py` |
| **Asymmetric safety** — under-triage penalised ~20× over-triage | `src/costs.py`, `src/evaluate.py` |
| **Hard-coded escalation rules** overriding the model on critical vitals | `src/escalation_rules.py` |
| **Emergency sensitivity/recall** reported separately | `src/evaluate.py` |
| **Abstention** — “cannot assess — send to nurse now” | `src/predict.py` |
| Handles missing / mis-entered vitals (0 BP, temp 96 °C) | `src/escalation_rules.py` |
| **Stretch:** wait-time reduction vs FCFS | `src/waittime.py` |
| Near-instant nurse UI | `app/streamlit_app.py` |

## Run it online — no install, nothing to download

The easiest way to try it: open the hosted demo in a browser (phone or laptop).

1. Go to **https://share.streamlit.io/deploy?repository=rkondra1/opd-triage-assistant&branch=main&mainModule=app/streamlit_app.py**
2. Sign in with GitHub and click **Deploy**.
3. In ~1–2 minutes you get a public URL like `https://opd-triage-assistant-xxxx.streamlit.app`
   that anyone can open — no Python, no setup. (First open takes ~15 s while it
   builds the model once.)

> This repo is public and the app **self-builds** (it generates the synthetic
> data and trains the model on first run), so the hosted deploy works out of the
> box.

## Quick start (run locally)

Works on **Windows, macOS and Linux** (pure Python — no OS-specific code).

**macOS / Linux**

```bash
# 0. get the code
git clone https://github.com/rkondra1/opd-triage-assistant.git
cd opd-triage-assistant

# 1. (recommended) create a virtual env
python3 -m venv .venv && source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the whole pipeline: data -> train -> evaluate -> wait-time sim
python run_all.py

# 4. launch the interactive demo
streamlit run app/streamlit_app.py
```

**Windows (PowerShell)**

```powershell
# 0. get the code (install Git for Windows if needed)
git clone https://github.com/rkondra1/opd-triage-assistant.git
cd opd-triage-assistant

# 1. create a virtual env  (install Python 3.9+ from python.org first,
#    ticking "Add Python to PATH")
python -m venv .venv
.venv\Scripts\Activate.ps1          # in cmd.exe use: .venv\Scripts\activate.bat

# 2. install dependencies
pip install -r requirements.txt

# 3. run the whole pipeline: data -> train -> evaluate -> wait-time sim
python run_all.py

# 4. launch the interactive demo
streamlit run app/streamlit_app.py
```

> Tip: the bundled `models/*.joblib` were trained on another machine. If
> `pip` installs a slightly different scikit-learn version you may see a
> warning when loading them — just run `python run_all.py` once to retrain
> fresh on your laptop (~10 seconds).

Prefer to run the steps individually:

```bash
python -m src.generate_data --n 30000 --seed 7   # writes data/*.csv
python -m src.train                              # writes models/*.joblib
python -m src.evaluate                           # the real score
python -m src.waittime                           # stretch goal
python -m src.predict                            # smoke test on 3 cases
```

## How it works (the safety pipeline)

For every patient, `TriageEngine.predict_one()` does:

1. **Clean vitals.** Implausible values (0 BP, SpO2 0, temp 96 °C) become
   *missing* instead of being trusted; Fahrenheit-in-Celsius is auto-corrected.
2. **Model probabilities.** A logistic-regression pipeline (TF-IDF on the
   complaint text + scaled vitals) produces P(level = 1..5).
3. **Cost-optimal decision.** Instead of `argmax`, it picks the action that
   minimises the **asymmetric expected cost** (`src/costs.py`). Because
   under-triage costs 20×, this leans urgent and **abstains** when genuinely
   uncertain about a possible emergency.
4. **Hard escalation rules.** `src/escalation_rules.py` can only make a case
   *more* urgent — e.g. `SpO2 < 85 → Level 1`, chest pain / stroke keywords →
   Level 1–2. Every fired rule is shown to the nurse.
5. **Output.** Level, department, red flags, fired rules, data warnings, and
   confidence.

## Scoring

`src/evaluate.py` is the graded metric. It reports:

- **TOTAL / MEAN asymmetric cost** — the real score (lower is better)
- **Plain accuracy** — shown *only* to demonstrate it is misleading
- **Under- vs over-triage** counts
- **Emergency sensitivity/recall** on the hidden true-emergency set
- **Abstention stats** — including how many under-triages abstention prevented

## Project layout

```
opd-triage-assistant/
├── run_all.py                # one-command pipeline
├── requirements.txt
├── data/                     # generated CSVs (gitignored)
├── models/                   # trained models (gitignored)
├── docs/DOMAIN_PRIMER.md     # triage scale + red flags + safety philosophy
├── app/streamlit_app.py      # nurse-facing demo UI
└── src/
    ├── triage_rubric.py      # 5-level scale + departments (source of truth)
    ├── conditions.py         # condition archetypes for synthetic data
    ├── generate_data.py      # 30k synthetic records + hidden labels + arrivals
    ├── escalation_rules.py   # vitals cleaning + hard red-flag overrides
    ├── features.py           # shared feature engineering
    ├── train.py              # train triage + department models
    ├── costs.py              # the 20× asymmetric cost model
    ├── predict.py            # inference: decision + rules + abstention
    ├── evaluate.py           # the graded metric
    └── waittime.py           # FCFS vs triage-priority simulation
```

## Notes & assumptions

- The dataset is **synthetic** (generated here) because the real challenge data
  wasn’t provided. The generator mimics the described distribution: ~4% true
  emergencies, multilingual/transliterated complaint text, and messy vitals.
  To plug in the real data later, match the column names in
  `src/generate_data.py` (`FEATURE_COLUMNS` / `LABEL_COLUMNS`).
- No labs/imaging/ECG are used — only the intake form, as specified.
- This is decision *support*. A nurse always has the final say, and the system
  is designed to escalate or abstain rather than gamble on an emergency.
```
