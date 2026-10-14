"""
The asymmetric cost model - the heart of this challenge.

Under-triaging a patient (calling them LESS urgent than they really are) is far
more dangerous than over-triaging (calling them MORE urgent). We penalise
under-triage ~20x more than over-triage, with a large extra penalty when the
under-triaged patient is a TRUE EMERGENCY.

Both predict.py (to make decisions) and evaluate.py (to score them) import from
here, so the system is literally optimised for the metric it is graded on.

Remember: lower level number = more urgent.
    pred_level > true_level  => UNDER-triage (dangerous)
    pred_level < true_level  => OVER-triage  (wasteful but safe)
"""

from __future__ import annotations

UNDER_TRIAGE_MULT = 20.0     # per level of under-triage
OVER_TRIAGE_MULT = 1.0       # per level of over-triage
EMERGENCY_MISS_EXTRA = 60.0  # extra if a TRUE emergency is under-triaged
ABSTAIN_COST = 2.0           # "send to nurse now" - small, safe, bounded cost


def triage_cost(true_level: int, pred_level: int, is_emergency: bool = False) -> float:
    """Cost of predicting ``pred_level`` when truth is ``true_level``."""
    if pred_level == true_level:
        return 0.0
    if pred_level > true_level:
        # under-triage: the dangerous direction
        cost = UNDER_TRIAGE_MULT * (pred_level - true_level)
        if is_emergency:
            cost += EMERGENCY_MISS_EXTRA
        return cost
    # over-triage: safe but wastes scarce capacity
    return OVER_TRIAGE_MULT * (true_level - pred_level)


def abstain_cost(true_level: int = 0, is_emergency: bool = False) -> float:
    """Cost of abstaining ('cannot assess - send to nurse now').

    Fixed and small: a human immediately reassesses, so the patient is safe.
    It is cheaper than under-triaging an emergency but not free, so the system
    is not rewarded for abstaining on everything.
    """
    return ABSTAIN_COST
