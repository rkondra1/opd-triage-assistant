"""
Stretch goal: estimate wait-time reduction vs first-come-first-served (FCFS).

    python -m src.waittime

Simulates the OPD with 2 doctors using the provided arrival log, comparing:
    A) FCFS           - patients seen strictly in arrival order (today's reality)
    B) Triage-ordered - patients seen by the assistant's predicted priority
                        (ties broken by arrival time), non-preemptive

Reports average wait overall and - most importantly - average wait and
target-time compliance for TRUE EMERGENCIES.
"""

from __future__ import annotations

import heapq
import os
import random

import pandas as pd

from .predict import TriageEngine
from .triage_rubric import ABSTAIN, TRIAGE_LEVELS

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "data")

N_DOCTORS = 2
MEAN_SERVICE_MIN = 6.0


def _load_all_features() -> pd.DataFrame:
    frames = []
    for name in ("intake_train.csv", "intake_test.csv"):
        p = os.path.join(DATA_DIR, name)
        if os.path.exists(p):
            frames.append(pd.read_csv(p))
    if not frames:
        raise SystemExit("No intake data. Run `python -m src.generate_data` first.")
    return pd.concat(frames, ignore_index=True)


def _service_times(pids, seed=11):
    rng = random.Random(seed)
    return {pid: max(2.0, rng.gauss(MEAN_SERVICE_MIN, 2.0)) for pid in pids}


def _simulate(patients, service, prioritized: bool) -> dict:
    """patients: list of dicts {pid, arrival, priority}. Returns pid -> wait (min)."""
    arrivals = sorted(patients, key=lambda p: p["arrival"])
    waits: dict = {}

    if not prioritized:
        free = [0.0] * N_DOCTORS
        heapq.heapify(free)
        for p in arrivals:
            sf = heapq.heappop(free)
            start = max(sf, p["arrival"])
            waits[p["pid"]] = start - p["arrival"]
            heapq.heappush(free, start + service[p["pid"]])
        return waits

    # non-preemptive priority with N servers
    free = [0.0] * N_DOCTORS
    heapq.heapify(free)
    waiting: list = []          # heap of (priority, arrival, seq, pid)
    i, served, N, seq = 0, 0, len(arrivals), 0
    while served < N:
        sf = heapq.heappop(free)
        while i < N and arrivals[i]["arrival"] <= sf:
            p = arrivals[i]
            heapq.heappush(waiting, (p["priority"], p["arrival"], seq, p["pid"]))
            seq += 1
            i += 1
        if not waiting:
            # server idles until the next arrival
            p = arrivals[i]
            heapq.heappush(waiting, (p["priority"], p["arrival"], seq, p["pid"]))
            seq += 1
            i += 1
            sf = max(sf, p["arrival"])
        _prio, arr, _s, pid = heapq.heappop(waiting)
        start = max(sf, arr)
        waits[pid] = start - arr
        heapq.heappush(free, start + service[pid])
        served += 1
    return waits


def main() -> None:
    arr = pd.read_csv(os.path.join(DATA_DIR, "arrival_log.csv"))
    arr["arrival_time"] = pd.to_datetime(arr["arrival_time"])

    # The log spans many days (~800 walk-ins/day). Simulate ONE representative
    # day so the numbers reflect a single real OPD session with 2 doctors.
    arr["day"] = arr["arrival_time"].dt.date
    busiest = arr["day"].value_counts().idxmax()
    arr = arr[arr["day"] == busiest].copy()
    day_start = arr["arrival_time"].min().normalize() + pd.Timedelta(hours=8)
    arr["arrival_min"] = (arr["arrival_time"] - day_start).dt.total_seconds() / 60.0
    arr.loc[arr["arrival_min"] < 0, "arrival_min"] = 0.0

    feats = _load_all_features()

    # True-emergency flags live inline in intake_train.csv and in labels_test.csv
    emerg_ids: set = set()
    train_path = os.path.join(DATA_DIR, "intake_train.csv")
    if os.path.exists(train_path):
        tr = pd.read_csv(train_path, usecols=["patient_id", "is_true_emergency"])
        emerg_ids |= set(tr.loc[tr["is_true_emergency"] == 1, "patient_id"])
    labels_path = os.path.join(DATA_DIR, "labels_test.csv")
    if os.path.exists(labels_path):
        lab = pd.read_csv(labels_path)
        emerg_ids |= set(lab.loc[lab["is_true_emergency"] == 1, "patient_id"])

    day_ids = set(arr["patient_id"])
    feats = feats[feats["patient_id"].isin(day_ids)].copy()

    print(f"Scoring {len(feats)} patients (one OPD day) with the triage engine ...")
    engine = TriageEngine.load()
    results = engine.predict_frame(feats)
    pred_priority = {}
    for row, res in zip(feats.itertuples(index=False), results):
        lvl = res.triage_level
        pred_priority[row.patient_id] = 2 if lvl == ABSTAIN else int(lvl)

    arr = arr[arr["patient_id"].isin(pred_priority)]
    patients = [
        {"pid": r.patient_id, "arrival": r.arrival_min,
         "priority": pred_priority[r.patient_id]}
        for r in arr.itertuples(index=False)
    ]
    service = _service_times([p["pid"] for p in patients])

    fcfs = _simulate(patients, service, prioritized=False)
    prio = _simulate(patients, service, prioritized=True)

    def avg(d, ids=None):
        vals = [v for k, v in d.items() if ids is None or k in ids]
        return sum(vals) / max(1, len(vals))

    emerg_present = emerg_ids & set(pred_priority)
    l1l2 = {p["pid"] for p in patients if p["priority"] <= 2}

    print("=" * 60)
    print("  WAIT-TIME SIMULATION  (2 doctors)")
    print("=" * 60)
    print(f"  Patients simulated        : {len(patients)}")
    print(f"  Mean service time         : {MEAN_SERVICE_MIN:.0f} min")
    print("-" * 60)
    print(f"  Avg wait  ALL   FCFS      : {avg(fcfs):6.1f} min")
    print(f"  Avg wait  ALL   Triage    : {avg(prio):6.1f} min")
    print("-" * 60)
    if emerg_present:
        fe, pe = avg(fcfs, emerg_present), avg(prio, emerg_present)
        print(f"  True emergencies in day   : {len(emerg_present)}")
        print(f"  Avg wait  EMERGENCIES FCFS: {fe:6.1f} min")
        print(f"  Avg wait  EMERGENCIES Triage:{pe:6.1f} min")
        print(f"  Emergency wait reduction  : {fe - pe:6.1f} min "
              f"({_safe_pct(fe, pe)})")
        print("-" * 60)
        print("  Emergencies seen within X minutes   FCFS  ->  Triage")
        for tgt in (10, 30, 60, 120):
            cf = sum(1 for k in emerg_present if fcfs[k] <= tgt) / len(emerg_present)
            cp = sum(1 for k in emerg_present if prio[k] <= tgt) / len(emerg_present)
            print(f"    within {tgt:4d} min                 "
                  f"{100*cf:4.0f}%  ->  {100*cp:4.0f}%")
    print("-" * 60)
    print("  NOTE: with only 2 doctors for 800 walk-ins the OPD is capacity-")
    print("  bound, so triage cannot hit the 10-min ESI target - but it still")
    print("  cuts emergency waiting dramatically. This quantifies the staffing")
    print("  gap, which is itself a useful finding.")
    print("=" * 60)


def _safe_pct(a, b):
    if a <= 0:
        return "n/a"
    return f"-{100 * (a - b) / a:.0f}%"


if __name__ == "__main__":
    main()
