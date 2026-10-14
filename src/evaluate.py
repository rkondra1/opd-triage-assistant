"""
evaluate.py - score the triage system the way the challenge demands.

    python -m src.evaluate

Reads data/intake_test.csv (features) + data/labels_test.csv (HIDDEN labels),
runs the full TriageEngine, and reports:

    1. TOTAL and MEAN asymmetric cost  <-- the real score (lower is better)
    2. Plain accuracy                  <-- shown ONLY to prove it is misleading
    3. Under-triage vs over-triage breakdown
    4. Emergency sensitivity / recall on the hidden true-emergency set
       (reported separately and prominently, as required)
    5. Abstention statistics (how often, and was it used wisely)

Teams that optimise plain accuracy score badly here - discovering that is part
of the exercise.
"""

from __future__ import annotations

import os

import pandas as pd

from .costs import ABSTAIN_COST, abstain_cost, triage_cost
from .predict import TriageEngine
from .triage_rubric import ABSTAIN

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "data")


def _fmt_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def evaluate() -> dict:
    feats_path = os.path.join(DATA_DIR, "intake_test.csv")
    labels_path = os.path.join(DATA_DIR, "labels_test.csv")
    if not (os.path.exists(feats_path) and os.path.exists(labels_path)):
        raise SystemExit("Missing test data. Run `python -m src.generate_data` first.")

    feats = pd.read_csv(feats_path)
    labels = pd.read_csv(labels_path).set_index("patient_id")

    engine = TriageEngine.load()
    results = engine.predict_frame(feats)

    n = len(results)
    total_cost = 0.0
    correct = 0
    under = over = exact = 0
    abstentions = 0
    abstain_on_emergency = 0
    abstain_would_under = 0

    # emergency set metrics
    emerg_total = 0
    emerg_caught = 0          # true emergency -> predicted level 1 or 2
    emerg_abstained = 0       # true emergency -> abstained (safe: nurse sees now)
    emerg_missed = 0          # true emergency -> predicted level >= 3 (DANGEROUS)

    dept_correct = 0
    dept_considered = 0

    for feat_row, res in zip(feats.itertuples(index=False), results):
        pid = feat_row.patient_id
        true_level = int(labels.loc[pid, "triage_level"])
        is_emerg = bool(labels.loc[pid, "is_true_emergency"])
        true_dept = labels.loc[pid, "department"]

        if res.triage_level == ABSTAIN:
            abstentions += 1
            total_cost += abstain_cost(true_level, is_emerg)
            if is_emerg:
                abstain_on_emergency += 1
            # was abstaining better than the model's own (pre-rule) guess?
            if res.model_level > true_level:
                abstain_would_under += 1
        else:
            pred = int(res.triage_level)
            total_cost += triage_cost(true_level, pred, is_emerg)
            if pred == true_level:
                exact += 1
                correct += 1
            elif pred > true_level:
                under += 1
            else:
                over += 1
            # department accuracy (only when we actually routed)
            dept_considered += 1
            if res.department == true_dept:
                dept_correct += 1

        # emergency accounting
        if is_emerg:
            emerg_total += 1
            if res.triage_level == ABSTAIN:
                emerg_abstained += 1
            elif int(res.triage_level) <= 2:
                emerg_caught += 1
            else:
                emerg_missed += 1

    mean_cost = total_cost / n
    accuracy = exact / max(1, (n - abstentions))

    # "safe handling" of emergencies = caught OR abstained (both get a human fast)
    emerg_sensitivity = emerg_caught / max(1, emerg_total)
    emerg_safe = (emerg_caught + emerg_abstained) / max(1, emerg_total)

    report = {
        "n_cases": n,
        "TOTAL_COST": round(total_cost, 1),
        "MEAN_COST": round(mean_cost, 3),
        "plain_accuracy": round(accuracy, 4),
        "exact": exact,
        "under_triage": under,
        "over_triage": over,
        "abstentions": abstentions,
        "abstain_on_emergency": abstain_on_emergency,
        "abstain_prevented_under_triage": abstain_would_under,
        "emergency_total": emerg_total,
        "emergency_caught_L1_L2": emerg_caught,
        "emergency_abstained": emerg_abstained,
        "emergency_MISSED": emerg_missed,
        "emergency_sensitivity": round(emerg_sensitivity, 4),
        "emergency_safely_handled": round(emerg_safe, 4),
        "department_accuracy": round(dept_correct / max(1, dept_considered), 4),
    }

    # -------- pretty print ----------------------------------------------
    print("=" * 64)
    print("  OPD TRIAGE ASSISTANT - EVALUATION")
    print("=" * 64)
    print(f"  Cases evaluated           : {n}")
    print("-" * 64)
    print("  PRIMARY SCORE (asymmetric cost, lower = better)")
    print(f"    TOTAL cost              : {report['TOTAL_COST']}")
    print(f"    MEAN cost per patient   : {report['MEAN_COST']}")
    print("-" * 64)
    print("  Decision breakdown")
    print(f"    Exact triage level      : {exact}")
    print(f"    Over-triaged  (safe)    : {over}")
    print(f"    Under-triaged (danger)  : {under}")
    print(f"    Abstained (-> nurse)    : {abstentions} "
          f"(prevented {abstain_would_under} under-triages)")
    print("-" * 64)
    print("  !!! EMERGENCY SENSITIVITY (hidden true-emergency set) !!!")
    print(f"    True emergencies        : {emerg_total}")
    print(f"    Caught as L1/L2         : {emerg_caught}")
    print(f"    Abstained (safe)        : {emerg_abstained}")
    print(f"    MISSED (L3-L5, DANGER)  : {emerg_missed}")
    print(f"    Sensitivity/recall      : {_fmt_pct(emerg_sensitivity)}")
    print(f"    Safely handled          : {_fmt_pct(emerg_safe)}")
    print("-" * 64)
    print(f"  Department accuracy       : {_fmt_pct(report['department_accuracy'])}")
    print(f"  Plain accuracy (MISLEADING): {_fmt_pct(accuracy)}")
    print("=" * 64)
    print("  NOTE: plain accuracy ignores that one missed emergency can cost")
    print("  more than hundreds of correct mild cases. Optimise MEAN_COST and")
    print("  emergency sensitivity, not accuracy.")
    print("=" * 64)

    return report


if __name__ == "__main__":
    evaluate()
