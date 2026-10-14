"""
Inference: turn one intake record into a safe triage decision.

Pipeline for every patient:
    1. Clean vitals (implausible -> missing), collecting data-quality flags.
    2. ML model -> probability distribution over triage levels 1..5.
    3. Cost-optimal decision: pick the level (or ABSTAIN) that minimises the
       ASYMMETRIC expected cost from costs.py. Because under-triage costs 20x,
       this naturally leans urgent and abstains when genuinely uncertain.
    4. Hard escalation rules (escalation_rules.py) can only make it MORE urgent.
    5. Emit level, department, red flags, fired rules, abstention + reasons.

Use programmatically:
    from src.predict import TriageEngine
    engine = TriageEngine.load()
    result = engine.predict_one({...intake dict...})
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field

import joblib
import numpy as np
import pandas as pd

from .costs import abstain_cost, triage_cost
from .escalation_rules import apply_escalation, clean_vitals
from .features import prepare_frame
from .triage_rubric import ABSTAIN, TRIAGE_LEVELS

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

# Abstain when the model's single most likely level is below this confidence.
LOW_CONFIDENCE = 0.34


@dataclass
class TriageResult:
    triage_level: object                 # int 1-5, or "ABSTAIN"
    level_name: str
    department: str
    red_flags: list[str] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)
    data_flags: list[str] = field(default_factory=list)
    abstained: bool = False
    abstain_reason: str = ""
    confidence: float = 0.0
    model_level: int = 0                 # what the model alone said
    probabilities: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class TriageEngine:
    def __init__(self, triage_model, department_model):
        self.triage_model = triage_model
        self.department_model = department_model
        self.triage_classes = list(triage_model.named_steps["clf"].classes_)

    @classmethod
    def load(cls, model_dir: str = MODEL_DIR) -> "TriageEngine":
        t = joblib.load(os.path.join(model_dir, "triage_model.joblib"))
        d = joblib.load(os.path.join(model_dir, "department_model.joblib"))
        return cls(t, d)

    # -- batch probability helpers --------------------------------------
    def _level_proba(self, frame: pd.DataFrame) -> np.ndarray:
        return self.triage_model.predict_proba(frame)

    def _cost_optimal_action(self, probs: dict) -> object:
        """Choose level 1..5 or ABSTAIN minimising expected asymmetric cost."""
        levels = sorted(probs)
        best_action, best_cost = None, float("inf")
        for cand in levels:
            exp = 0.0
            for true_level, p in probs.items():
                # treat levels 1-2 as emergencies for the cost calculation
                exp += p * triage_cost(true_level, cand, is_emergency=true_level <= 2)
            if exp < best_cost:
                best_cost, best_action = exp, cand
        # abstention competes as its own action
        exp_abstain = sum(p * abstain_cost() for p in probs.values())
        if exp_abstain < best_cost:
            best_action = ABSTAIN
        return best_action

    # -- public API ------------------------------------------------------
    def predict_frame(self, raw_df: pd.DataFrame) -> list[TriageResult]:
        frame = prepare_frame(raw_df)
        level_probs = self._level_proba(frame)
        dept_pred = self.department_model.predict(frame)

        results = []
        for i, (_, raw_row) in enumerate(raw_df.iterrows()):
            probs = {int(c): float(level_probs[i][j])
                     for j, c in enumerate(self.triage_classes)}
            results.append(self._finalise(raw_row.to_dict(), probs, dept_pred[i]))
        return results

    def predict_one(self, record: dict) -> TriageResult:
        return self.predict_frame(pd.DataFrame([record]))[0]

    # -- core decision assembly -----------------------------------------
    def _finalise(self, raw: dict, probs: dict, model_dept: str) -> TriageResult:
        clean_v, data_flags = clean_vitals(raw)
        complaint = raw.get("chief_complaint", "")

        model_level = max(probs, key=probs.get)
        confidence = probs[model_level]
        action = self._cost_optimal_action(probs)

        abstained = False
        abstain_reason = ""
        if action == ABSTAIN:
            abstained = True
            abstain_reason = "Model uncertain and risk of under-triage too high."
            working_level = model_level  # used only if a hard rule overrides
        else:
            working_level = int(action)

        # Low-confidence abstention safety net (unless clearly non-urgent)
        if (not abstained and confidence < LOW_CONFIDENCE
                and working_level >= 3
                and (probs.get(1, 0) + probs.get(2, 0)) >= 0.15):
            abstained = True
            abstain_reason = (
                f"Low confidence ({confidence:.0%}) with non-trivial emergency "
                "probability."
            )

        # --- hard escalation rules (can only increase urgency) ----------
        esc = apply_escalation(working_level, clean_v, complaint, model_dept)

        if esc.overridden:
            # a definitive red flag: we must act, so never abstain here
            final_level = esc.final_level
            abstained = False
            abstain_reason = ""
        elif abstained:
            final_level = ABSTAIN
        else:
            final_level = esc.final_level

        # department routing
        department = esc.forced_department or model_dept
        if final_level == 1 and department not in ("Emergency",):
            department = "Emergency"

        level_name = (TRIAGE_LEVELS[final_level]["name"]
                      if isinstance(final_level, int) else "Send to nurse now")

        return TriageResult(
            triage_level=final_level,
            level_name=level_name,
            department=department if not abstained else "Nurse re-assessment",
            red_flags=esc.red_flags,
            rules_fired=esc.rules_fired,
            data_flags=data_flags,
            abstained=abstained,
            abstain_reason=abstain_reason,
            confidence=round(confidence, 3),
            model_level=int(model_level),
            probabilities={int(k): round(v, 3) for k, v in probs.items()},
        )


if __name__ == "__main__":
    # quick smoke test on a couple of hand-written cases
    engine = TriageEngine.load()
    samples = [
        {"age": 58, "sex": "M", "bp_systolic": 150, "bp_diastolic": 95, "pulse": 110,
         "temp_c": 37.0, "spo2": 94, "chief_complaint": "seene mein dard aur pasina",
         "known_conditions": "diabetes", "medications": "metformin"},
        {"age": 25, "sex": "F", "bp_systolic": 118, "bp_diastolic": 76, "pulse": 80,
         "temp_c": 37.1, "spo2": 99, "chief_complaint": "runny nose and sore throat",
         "known_conditions": "none", "medications": "none"},
        {"age": 70, "sex": "M", "bp_systolic": 0, "bp_diastolic": 0, "pulse": 48,
         "temp_c": 96.0, "spo2": 86, "chief_complaint": "feeling very weak and drowsy",
         "known_conditions": "hypertension", "medications": "amlodipine"},
    ]
    for s in samples:
        r = engine.predict_one(s)
        print("\n", s["chief_complaint"])
        print("  ->", r.triage_level, r.level_name, "| dept:", r.department)
        print("     red_flags:", r.red_flags, "| rules:", r.rules_fired)
        print("     data_flags:", r.data_flags, "| abstained:", r.abstained)
