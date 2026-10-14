"""
Synthetic data generator for the OPD Triage Assistant.

Produces ~30k intake records plus hidden ground-truth labels, mimicking what
the challenge organisers "provide". Run:

    python -m src.generate_data --n 30000 --seed 7

Outputs (in data/):
    intake_train.csv   features + labels (for training / development)
    intake_test.csv    features only (what the deployed system sees)
    labels_test.csv    HIDDEN labels for evaluate.py (triage, dept, emergency)
    arrival_log.csv    arrival timestamps for the wait-time stretch goal

Realistic messiness injected on purpose:
    - ~6% of records have a missing vital
    - ~2% have a mis-entered vital (0 BP, temp of 96 "C", SpO2 of 0, etc.)
    - complaint text mixes English, Hindi transliteration and Hinglish
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from datetime import datetime, timedelta

from .conditions import ARCHETYPES, Archetype, total_weight
from .triage_rubric import KNOWN_CONDITIONS, MEDICATIONS

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

FEATURE_COLUMNS = [
    "patient_id",
    "age",
    "sex",
    "bp_systolic",
    "bp_diastolic",
    "pulse",
    "temp_c",
    "spo2",
    "chief_complaint",
    "known_conditions",
    "medications",
]
LABEL_COLUMNS = ["patient_id", "triage_level", "department", "is_true_emergency"]


def _pick_archetype(rng: random.Random) -> Archetype:
    r = rng.uniform(0, total_weight())
    upto = 0.0
    for a in ARCHETYPES:
        upto += a.weight
        if r <= upto:
            return a
    return ARCHETYPES[-1]


def _maybe_corrupt_vitals(rng: random.Random, v: dict) -> dict:
    """Inject missing values and plausible data-entry mistakes."""
    v = dict(v)
    # clamp to sane-ish ranges first
    v["spo2"] = max(60, min(100, v["spo2"]))
    v["pulse"] = max(30, v["pulse"])
    v["bp_systolic"] = max(50, v["bp_systolic"])
    v["bp_diastolic"] = max(30, v["bp_diastolic"])

    roll = rng.random()
    if roll < 0.06:
        # missing a random vital (empty string in CSV)
        field = rng.choice(["bp_systolic", "bp_diastolic", "pulse", "temp_c", "spo2"])
        v[field] = ""
    elif roll < 0.08:
        # mis-entry: classic bad values the problem statement warns about
        kind = rng.choice(["bp0", "tempF", "spo0", "temp96"])
        if kind == "bp0":
            v["bp_systolic"] = 0
            v["bp_diastolic"] = 0
        elif kind == "tempF":
            # nurse typed Fahrenheit value into the Celsius field
            v["temp_c"] = round(v["temp_c"] * 9 / 5 + 32, 1)
        elif kind == "spo0":
            v["spo2"] = 0
        elif kind == "temp96":
            v["temp_c"] = 96.0
    return v


def _sample_history(rng: random.Random, arch: Archetype) -> tuple[str, str]:
    conds = []
    if arch.common_conditions and rng.random() < 0.7:
        conds.append(rng.choice([c for c in arch.common_conditions if c != "none"] or ["none"]))
    if rng.random() < 0.2:
        conds.append(rng.choice(KNOWN_CONDITIONS))
    conds = [c for c in dict.fromkeys(conds) if c and c != "none"]
    cond_str = ";".join(conds) if conds else "none"

    meds = []
    if conds and rng.random() < 0.6:
        meds.append(rng.choice([m for m in MEDICATIONS if m != "none"]))
    med_str = ";".join(dict.fromkeys(meds)) if meds else "none"
    return cond_str, med_str


def _sample_patient(rng: random.Random, pid: int) -> tuple[dict, dict]:
    arch = _pick_archetype(rng)
    age = rng.randint(*arch.age_range)
    sex = rng.choice(["M", "F"])
    if arch.key == "pregnancy_issue":
        sex = "F"

    vitals = arch.vitals(rng, age)
    vitals = _maybe_corrupt_vitals(rng, vitals)

    complaint = rng.choice(arch.complaints)

    # ground-truth labels
    level = arch.triage_level
    dept = arch.department
    emergency = rng.random() < arch.emergency_prob
    if arch.escalate_prob and rng.random() < arch.escalate_prob:
        level = min(level, arch.escalate_to_level)
        if arch.escalate_department:
            dept = arch.escalate_department
        # escalation raises severity; only a minority of those are *true*
        # emergencies, so emergencies stay rare (~4%) as specified
        emergency = emergency or (level <= 1 and rng.random() < 0.2)

    # a genuine emergency is always level 1 or 2
    if emergency:
        level = min(level, 2)

    cond_str, med_str = _sample_history(rng, arch)

    feature = {
        "patient_id": pid,
        "age": age,
        "sex": sex,
        "bp_systolic": vitals["bp_systolic"],
        "bp_diastolic": vitals["bp_diastolic"],
        "pulse": vitals["pulse"],
        "temp_c": vitals["temp_c"],
        "spo2": vitals["spo2"],
        "chief_complaint": complaint,
        "known_conditions": cond_str,
        "medications": med_str,
    }
    label = {
        "patient_id": pid,
        "triage_level": level,
        "department": dept,
        "is_true_emergency": int(emergency),
    }
    return feature, label


def generate(n: int, seed: int, test_frac: float = 0.2) -> None:
    rng = random.Random(seed)
    os.makedirs(DATA_DIR, exist_ok=True)

    features, labels = [], []
    for pid in range(1, n + 1):
        f, l = _sample_patient(rng, pid)
        features.append(f)
        labels.append(l)

    # arrival log: ~800 walk-ins/day spread across as many days as needed,
    # within a 10-hour OPD window (08:00-18:00) skewed toward the morning rush.
    PER_DAY = 800
    OPD_WINDOW_MIN = 10 * 60
    base = datetime(2026, 1, 5, 8, 0, 0)
    arrivals = []
    for idx, f in enumerate(features):
        day = idx // PER_DAY
        # minutes after 08:00 within the OPD window, morning-heavy
        minute = int(abs(rng.gauss(0, 170))) % OPD_WINDOW_MIN
        arrivals.append((f["patient_id"], base + timedelta(days=day, minutes=minute)))
    arrivals.sort(key=lambda x: x[1])

    n_test = int(n * test_frac)
    test_ids = set(f["patient_id"] for f in features[-n_test:])

    train_feats = [f for f in features if f["patient_id"] not in test_ids]
    train_labels = {l["patient_id"]: l for l in labels}

    # write train (features + labels inline)
    train_path = os.path.join(DATA_DIR, "intake_train.csv")
    with open(train_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(FEATURE_COLUMNS + ["triage_level", "department", "is_true_emergency"])
        for f in train_feats:
            l = train_labels[f["patient_id"]]
            w.writerow([f[c] for c in FEATURE_COLUMNS]
                       + [l["triage_level"], l["department"], l["is_true_emergency"]])

    # write test features
    test_feats = [f for f in features if f["patient_id"] in test_ids]
    test_path = os.path.join(DATA_DIR, "intake_test.csv")
    with open(test_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(FEATURE_COLUMNS)
        for f in test_feats:
            w.writerow([f[c] for c in FEATURE_COLUMNS])

    # write hidden test labels
    labels_path = os.path.join(DATA_DIR, "labels_test.csv")
    with open(labels_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(LABEL_COLUMNS)
        for pid in sorted(test_ids):
            l = train_labels[pid]
            w.writerow([l[c] for c in LABEL_COLUMNS])

    # arrival log
    arr_path = os.path.join(DATA_DIR, "arrival_log.csv")
    with open(arr_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["patient_id", "arrival_time"])
        for pid, t in arrivals:
            w.writerow([pid, t.isoformat()])

    n_emerg = sum(l["is_true_emergency"] for l in labels)
    print(f"Generated {n} records ({len(train_feats)} train / {len(test_feats)} test)")
    print(f"True emergencies: {n_emerg} ({100 * n_emerg / n:.1f}%)")
    print(f"Wrote: {train_path}")
    print(f"       {test_path}")
    print(f"       {labels_path}")
    print(f"       {arr_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate synthetic OPD intake data")
    ap.add_argument("--n", type=int, default=30000, help="number of records")
    ap.add_argument("--seed", type=int, default=7, help="random seed")
    ap.add_argument("--test-frac", type=float, default=0.2)
    args = ap.parse_args()
    generate(args.n, args.seed, args.test_frac)
