"""
ESI-style 5-level triage rubric and department taxonomy.

This is the single source of truth for:
  - what each triage level means (clinical definition)
  - the list of departments the assistant can route to
  - the "condition archetypes" that the synthetic data generator uses to
    produce realistic patients with known (hidden) ground-truth labels.

Triage levels follow an Emergency Severity Index (ESI) style scale where
LEVEL 1 IS THE MOST URGENT and LEVEL 5 IS THE LEAST URGENT.

    Level 1 - Resuscitation : life-threatening, needs immediate intervention
    Level 2 - Emergent      : high risk, should be seen within ~10 minutes
    Level 3 - Urgent        : needs several resources, seen within ~30 minutes
    Level 4 - Less urgent   : one resource, seen within ~1 hour
    Level 5 - Non-urgent    : routine, seen within ~2 hours

IMPORTANT: because lower number == more urgent, "under-triage" means the
system assigned a HIGHER number (less urgent) than the truth. That is the
dangerous failure mode the evaluation penalises ~20x.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Triage levels
# ---------------------------------------------------------------------------
TRIAGE_LEVELS = {
    1: {
        "name": "Resuscitation",
        "target_minutes": 0,
        "definition": "Life-threatening. Requires immediate life-saving intervention.",
    },
    2: {
        "name": "Emergent",
        "target_minutes": 10,
        "definition": "High risk situation, or severe pain/distress. See within ~10 min.",
    },
    3: {
        "name": "Urgent",
        "target_minutes": 30,
        "definition": "Stable but needs multiple resources. See within ~30 min.",
    },
    4: {
        "name": "Less urgent",
        "target_minutes": 60,
        "definition": "Stable, likely one resource. See within ~1 hour.",
    },
    5: {
        "name": "Non-urgent",
        "target_minutes": 120,
        "definition": "Routine problem, minimal resources. See within ~2 hours.",
    },
}

ABSTAIN = "ABSTAIN"  # "cannot assess - send to nurse now"

# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    "Emergency",
    "Cardiology",
    "Pulmonology",
    "General Medicine",
    "Pediatrics",
    "OB/GYN",
    "Orthopedics",
    "Neurology",
    "Gastroenterology",
    "ENT",
    "Dermatology",
    "Urology",
]

# ---------------------------------------------------------------------------
# Known conditions and medications used to build patient history
# ---------------------------------------------------------------------------
KNOWN_CONDITIONS = [
    "hypertension",
    "diabetes",
    "asthma",
    "COPD",
    "coronary artery disease",
    "chronic kidney disease",
    "pregnancy",
    "epilepsy",
    "thyroid disorder",
    "none",
]

MEDICATIONS = [
    "amlodipine",
    "metformin",
    "insulin",
    "salbutamol inhaler",
    "aspirin",
    "atorvastatin",
    "levothyroxine",
    "none",
]
