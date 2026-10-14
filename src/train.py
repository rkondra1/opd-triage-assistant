"""
Train the triage-level and department models.

    python -m src.train

Saves to models/:
    triage_model.joblib        pipeline: preprocessor + LogisticRegression (levels 1-5)
    department_model.joblib    pipeline: preprocessor + LogisticRegression (dept)
    meta.json                  class order + training summary

Design choices that matter for SAFETY (not just accuracy):
  - class_weight="balanced" so the rare emergency levels are not drowned out
  - we keep the predicted PROBABILITIES, because the abstention mechanism and
    the asymmetric decision rule in predict.py need calibrated-ish scores, not
    just the argmax label.
"""

from __future__ import annotations

import json
import os

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .features import build_preprocessor, prepare_frame

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "data")
MODEL_DIR = os.path.join(ROOT, "models")


def _make_pipeline() -> Pipeline:
    return Pipeline([
        ("pre", build_preprocessor()),
        ("clf", LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            C=4.0,
        )),
    ])


def main() -> None:
    train_path = os.path.join(DATA_DIR, "intake_train.csv")
    if not os.path.exists(train_path):
        raise SystemExit(
            "data/intake_train.csv not found. Run `python -m src.generate_data` first."
        )

    df = pd.read_csv(train_path)
    df = prepare_frame(df)

    os.makedirs(MODEL_DIR, exist_ok=True)

    # --- triage level model ---------------------------------------------
    triage_pipe = _make_pipeline()
    triage_pipe.fit(df, df["triage_level"])
    joblib.dump(triage_pipe, os.path.join(MODEL_DIR, "triage_model.joblib"))

    # --- department model -----------------------------------------------
    dept_pipe = _make_pipeline()
    dept_pipe.fit(df, df["department"])
    joblib.dump(dept_pipe, os.path.join(MODEL_DIR, "department_model.joblib"))

    meta = {
        "triage_classes": [int(c) for c in triage_pipe.named_steps["clf"].classes_],
        "department_classes": list(dept_pipe.named_steps["clf"].classes_),
        "n_train": int(len(df)),
        "triage_level_distribution": df["triage_level"].value_counts().sort_index().to_dict(),
    }
    with open(os.path.join(MODEL_DIR, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2, default=str)

    print(f"Trained on {len(df)} records.")
    print(f"Triage classes: {meta['triage_classes']}")
    print(f"Departments:   {meta['department_classes']}")
    print(f"Saved models to {MODEL_DIR}/")


if __name__ == "__main__":
    main()
