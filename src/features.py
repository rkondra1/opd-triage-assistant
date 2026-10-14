"""
Feature engineering shared by training and inference.

Keeps a single definition of how raw intake rows become model features so the
Streamlit app, training script and evaluator cannot drift apart.
"""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .escalation_rules import clean_vitals

NUMERIC_COLS = ["age", "bp_systolic", "bp_diastolic", "pulse", "temp_c", "spo2"]
TEXT_COL = "text_blob"
CAT_COLS = ["sex"]


def clean_row_vitals(row: dict) -> dict:
    """Clean one record's vitals (implausible -> None) for model input."""
    clean, _flags = clean_vitals({
        "bp_systolic": row.get("bp_systolic"),
        "bp_diastolic": row.get("bp_diastolic"),
        "pulse": row.get("pulse"),
        "temp_c": row.get("temp_c"),
        "spo2": row.get("spo2"),
    })
    return clean


def prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with cleaned numeric vitals and a combined text column."""
    df = df.copy()

    # Clean vitals row-by-row so implausible entries become NaN (imputed later)
    cleaned = df.apply(
        lambda r: pd.Series(clean_row_vitals(r.to_dict())), axis=1
    )
    for col in ["bp_systolic", "bp_diastolic", "pulse", "temp_c", "spo2"]:
        df[col] = pd.to_numeric(cleaned[col], errors="coerce")

    df["age"] = pd.to_numeric(df.get("age"), errors="coerce")
    df["sex"] = df.get("sex", "U").fillna("U").astype(str)

    # Combine all free text the patient/nurse provided into one blob
    def blob(r):
        parts = [
            str(r.get("chief_complaint", "") or ""),
            "cond_" + str(r.get("known_conditions", "none") or "none").replace(";", " cond_"),
            "med_" + str(r.get("medications", "none") or "none").replace(";", " med_"),
        ]
        return " ".join(parts).lower()

    df[TEXT_COL] = df.apply(blob, axis=1)
    return df


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    text = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=3,
        max_features=5000,
        sublinear_tf=True,
    )
    return ColumnTransformer([
        ("num", numeric, NUMERIC_COLS),
        ("cat", categorical, CAT_COLS),
        ("txt", text, TEXT_COL),
    ])
