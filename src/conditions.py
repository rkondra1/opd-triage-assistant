"""
Condition archetypes used to generate synthetic patients.

Each archetype describes a latent "true" clinical situation and knows how to
produce:
  - a free-text chief complaint written the way patients actually speak
    (English, Hindi transliteration, and Hinglish variants)
  - a plausible vitals distribution (with occasional noise)
  - the hidden ground-truth triage level, department and emergency flag

The data generator samples an archetype, then samples a concrete patient from
it. The ML model never sees the archetype - only the resulting intake record.

NOTE ON SAFETY DESIGN
---------------------
Some archetypes are "deceptive": the complaint text sounds mild but the case
is actually an emergency (e.g. a silent heart attack described as "gas" /
indigestion). These are what make plain-accuracy models dangerous and are the
reason the escalation rules + abstention mechanism matter.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Archetype:
    key: str
    weight: float                      # relative sampling frequency
    department: str
    triage_level: int                  # most common level for this archetype
    emergency_prob: float              # chance this instance is a true emergency
    complaints: list[str]              # free-text templates (mixed languages)
    # vitals sampler returns dict with bp_sys, bp_dia, pulse, temp_c, spo2
    vitals: Callable[[random.Random, int], dict]
    # optional: sometimes bump severity (e.g. appendicitis hidden in abdo pain)
    escalate_prob: float = 0.0
    escalate_to_level: int = 2
    escalate_department: str | None = None
    age_range: tuple[int, int] = (16, 85)
    common_conditions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Vitals helpers
# ---------------------------------------------------------------------------
def _normal_vitals(rng: random.Random, age: int) -> dict:
    return {
        "bp_systolic": int(rng.gauss(122, 10)),
        "bp_diastolic": int(rng.gauss(78, 8)),
        "pulse": int(rng.gauss(78, 10)),
        "temp_c": round(rng.gauss(36.8, 0.3), 1),
        "spo2": int(min(100, rng.gauss(98, 1))),
    }


def _febrile_vitals(rng: random.Random, age: int) -> dict:
    v = _normal_vitals(rng, age)
    v["temp_c"] = round(rng.gauss(38.8, 0.6), 1)
    v["pulse"] = int(rng.gauss(96, 12))
    return v


def _cardiac_vitals(rng: random.Random, age: int) -> dict:
    v = _normal_vitals(rng, age)
    v["bp_systolic"] = int(rng.gauss(150, 25))
    v["bp_diastolic"] = int(rng.gauss(95, 15))
    v["pulse"] = int(rng.gauss(105, 20))
    v["spo2"] = int(min(100, rng.gauss(95, 3)))
    return v


def _respiratory_vitals(rng: random.Random, age: int) -> dict:
    v = _normal_vitals(rng, age)
    v["pulse"] = int(rng.gauss(110, 15))
    v["spo2"] = int(min(100, rng.gauss(90, 4)))
    v["temp_c"] = round(rng.gauss(37.6, 0.6), 1)
    return v


def _shock_vitals(rng: random.Random, age: int) -> dict:
    v = _normal_vitals(rng, age)
    v["bp_systolic"] = int(rng.gauss(82, 10))
    v["bp_diastolic"] = int(rng.gauss(52, 8))
    v["pulse"] = int(rng.gauss(125, 15))
    v["spo2"] = int(min(100, rng.gauss(93, 4)))
    return v


def _stroke_vitals(rng: random.Random, age: int) -> dict:
    v = _normal_vitals(rng, age)
    v["bp_systolic"] = int(rng.gauss(180, 25))
    v["bp_diastolic"] = int(rng.gauss(105, 15))
    v["pulse"] = int(rng.gauss(88, 12))
    return v


# ---------------------------------------------------------------------------
# Archetype catalogue
# ---------------------------------------------------------------------------
ARCHETYPES: list[Archetype] = [
    Archetype(
        key="viral_fever",
        weight=16,
        department="General Medicine",
        triage_level=4,
        emergency_prob=0.0,
        complaints=[
            "fever since 2 days with body ache",
            "bukhar hai 2 din se, badan dard",
            "high temperature and feeling weak",
            "mujhe teen din se fever aur kamzori",
            "running fever at night, sweating a lot",
        ],
        vitals=_febrile_vitals,
        common_conditions=["none", "diabetes"],
    ),
    Archetype(
        key="common_cold",
        weight=14,
        department="ENT",
        triage_level=5,
        emergency_prob=0.0,
        complaints=[
            "runny nose cough and sore throat",
            "khaasi aur gale mein kharash",
            "cold since 4 days, sneezing",
            "sardi zukaam, naak band",
            "throat pain and mild cough",
        ],
        vitals=_normal_vitals,
    ),
    Archetype(
        key="chest_pain_cardiac",
        weight=5,
        department="Cardiology",
        triage_level=2,
        emergency_prob=0.12,
        escalate_prob=0.4,
        escalate_to_level=1,
        escalate_department="Emergency",
        complaints=[
            "chest pain spreading to left arm, sweating",
            "seene mein dard aur pasina aa raha hai",
            "heavy pressure on chest since 1 hour",
            "chaati mein bhaari dard, saans phool rahi",
            "pain in chest and jaw, feeling restless",
        ],
        vitals=_cardiac_vitals,
        age_range=(40, 85),
        common_conditions=["hypertension", "diabetes", "coronary artery disease"],
    ),
    Archetype(
        # DECEPTIVE: silent MI described as indigestion / gas
        key="silent_mi_as_gas",
        weight=1.2,
        department="Cardiology",
        triage_level=2,
        emergency_prob=0.3,
        escalate_prob=0.5,
        escalate_to_level=1,
        escalate_department="Emergency",
        complaints=[
            "lots of gas and burning in upper stomach, uneasy",
            "pet ke upar gas aur jalan, ghabrahat ho rahi",
            "indigestion since morning, little sweating",
            "acidity and heaviness, feeling tired and sweaty",
        ],
        vitals=_cardiac_vitals,
        age_range=(45, 80),
        common_conditions=["diabetes", "hypertension"],
    ),
    Archetype(
        key="breathing_difficulty",
        weight=6,
        department="Pulmonology",
        triage_level=2,
        emergency_prob=0.07,
        escalate_prob=0.3,
        escalate_to_level=1,
        escalate_department="Emergency",
        complaints=[
            "difficulty breathing and wheezing",
            "saans lene mein takleef ho rahi hai",
            "cannot breathe properly, chest tight",
            "dama ka attack, saans phool rahi hai",
            "short of breath even while sitting",
        ],
        vitals=_respiratory_vitals,
        common_conditions=["asthma", "COPD"],
    ),
    Archetype(
        key="minor_injury",
        weight=10,
        department="Orthopedics",
        triage_level=4,
        emergency_prob=0.0,
        complaints=[
            "twisted my ankle while walking, mild swelling",
            "pair mein moch aa gayi hai",
            "wrist pain after fall, can move fingers",
            "ghutne mein dard chot lagne ke baad",
            "minor cut on hand, bleeding stopped",
        ],
        vitals=_normal_vitals,
    ),
    Archetype(
        key="major_trauma",
        weight=2,
        department="Emergency",
        triage_level=2,
        emergency_prob=0.2,
        escalate_prob=0.4,
        escalate_to_level=1,
        escalate_department="Emergency",
        complaints=[
            "fell from height, severe leg pain and bleeding",
            "road accident, bahut khoon beh raha hai",
            "deep cut on head, feeling dizzy",
            "gir gaya chhat se, tang mein bahut dard",
        ],
        vitals=_shock_vitals,
    ),
    Archetype(
        key="abdominal_pain",
        weight=9,
        department="Gastroenterology",
        triage_level=3,
        emergency_prob=0.03,
        escalate_prob=0.15,         # some are appendicitis / obstruction
        escalate_to_level=2,
        escalate_department="Emergency",
        complaints=[
            "stomach pain since morning, feeling nauseous",
            "pet mein dard aur ulti jaisa",
            "lower abdomen pain, getting worse",
            "pet ke niche hisse mein tej dard",
            "cramping stomach pain and loose motions",
        ],
        vitals=_normal_vitals,
    ),
    Archetype(
        key="headache",
        weight=8,
        department="General Medicine",
        triage_level=4,
        emergency_prob=0.01,
        escalate_prob=0.06,
        escalate_to_level=2,
        escalate_department="Neurology",
        complaints=[
            "headache since yesterday, mild",
            "sir dard ho raha hai subah se",
            "throbbing headache with light sensitivity",
            "sar mein halka dard aur thakan",
        ],
        vitals=_normal_vitals,
    ),
    Archetype(
        key="stroke",
        weight=1,
        department="Neurology",
        triage_level=1,
        emergency_prob=0.5,
        complaints=[
            "sudden weakness one side, face drooping, slurred speech",
            "achanak ek taraf kamzori, mooh tedha ho gaya",
            "cannot move right arm, talking unclear",
            "aadha sharir sunn ho gaya achanak",
        ],
        vitals=_stroke_vitals,
        age_range=(45, 85),
        common_conditions=["hypertension", "diabetes"],
    ),
    Archetype(
        key="pediatric_fever",
        weight=7,
        department="Pediatrics",
        triage_level=3,
        emergency_prob=0.02,
        complaints=[
            "my child has high fever and is not eating",
            "bachche ko tej bukhar hai aur sust hai",
            "baby fever since night, crying a lot",
            "bachcha garam hai aur doodh nahi pee raha",
        ],
        vitals=_febrile_vitals,
        age_range=(0, 12),
    ),
    Archetype(
        key="pregnancy_issue",
        weight=4,
        department="OB/GYN",
        triage_level=3,
        emergency_prob=0.05,
        escalate_prob=0.2,
        escalate_to_level=2,
        escalate_department="OB/GYN",
        complaints=[
            "pregnant with stomach pain and some bleeding",
            "pregnancy mein pet dard aur blood aa raha",
            "8 months pregnant, baby movement reduced",
            "garbhvati hoon, pet ke niche dard",
        ],
        vitals=_normal_vitals,
        age_range=(18, 42),
        common_conditions=["pregnancy"],
    ),
    Archetype(
        key="skin_rash",
        weight=6,
        department="Dermatology",
        triage_level=5,
        emergency_prob=0.0,
        complaints=[
            "itchy red rash on arms since 3 days",
            "haath par laal chakatte aur khujli",
            "skin allergy with small bumps",
            "khujli ho rahi hai poore sharir par",
        ],
        vitals=_normal_vitals,
    ),
    Archetype(
        key="anaphylaxis",
        weight=1,
        department="Emergency",
        triage_level=1,
        emergency_prob=0.45,
        complaints=[
            "allergic reaction, swelling of face and trouble breathing",
            "allergy se chehra sooj gaya, saans nahi aa rahi",
            "ate something and throat is closing, hives all over",
            "poore sharir par sujan, saans lene mein dikkat",
        ],
        vitals=_respiratory_vitals,
    ),
    Archetype(
        key="diabetic_emergency",
        weight=1.5,
        department="Emergency",
        triage_level=2,
        emergency_prob=0.2,
        escalate_prob=0.3,
        escalate_to_level=1,
        escalate_department="Emergency",
        complaints=[
            "diabetic patient, drowsy and sweating, feeling faint",
            "sugar ka mareez, behoshi jaisa aur pasina",
            "very thirsty, confused, rapid breathing",
            "diabetes hai, chakkar aur kamzori bahut",
        ],
        vitals=_shock_vitals,
        age_range=(30, 80),
        common_conditions=["diabetes"],
    ),
    Archetype(
        key="uti",
        weight=5,
        department="Urology",
        triage_level=4,
        emergency_prob=0.02,
        complaints=[
            "burning while passing urine since 2 days",
            "peshab mein jalan ho rahi hai",
            "frequent urination and lower belly discomfort",
            "baar baar peshab aur jalan",
        ],
        vitals=_normal_vitals,
    ),
    Archetype(
        key="poisoning_overdose",
        weight=1,
        department="Emergency",
        triage_level=1,
        emergency_prob=0.45,
        complaints=[
            "swallowed pills, vomiting and very drowsy",
            "zeher kha liya, ulti aur behoshi",
            "took too many tablets, breathing slow",
            "poison pee liya galti se, chakkar aa rahe",
        ],
        vitals=_shock_vitals,
    ),
    Archetype(
        key="dizziness_weakness",
        weight=6,
        department="General Medicine",
        triage_level=4,
        emergency_prob=0.02,
        escalate_prob=0.05,
        escalate_to_level=2,
        escalate_department="General Medicine",
        complaints=[
            "feeling dizzy and weak since morning",
            "chakkar aa rahe hain aur kamzori",
            "light headed, little tired",
            "sar ghoom raha hai thoda",
        ],
        vitals=_normal_vitals,
    ),
]


def total_weight() -> float:
    return sum(a.weight for a in ARCHETYPES)
