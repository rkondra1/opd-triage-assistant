"""
Mandatory hard-coded escalation rule layer + vitals sanitisation.

These rules run AFTER the ML model and can only make a case MORE urgent, never
less. They encode clinical "red flags" that must never be missed regardless of
what the statistical model thinks. This is a safety net, not the primary brain.

The problem statement requires that these rules be explicit and visible - so
every rule returns a human-readable reason that the UI and logs display.

Two public functions:
    clean_vitals(raw)    -> (clean_vitals_dict, list_of_data_quality_flags)
    apply_escalation(...) -> EscalationResult
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Plausible physiological ranges. Anything outside is treated as a mis-entry
# (e.g. temp of 96 "C", 0 BP, SpO2 of 0) and set to missing rather than trusted.
# ---------------------------------------------------------------------------
PLAUSIBLE = {
    "bp_systolic": (50, 260),
    "bp_diastolic": (30, 160),
    "pulse": (25, 220),
    "temp_c": (33.0, 43.0),
    "spo2": (50, 100),
}


def _to_float(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def clean_vitals(raw: dict) -> tuple[dict, list[str]]:
    """Return sanitised vitals and a list of data-quality flags.

    Implausible or missing values become None so downstream code treats them as
    "unknown" instead of trusting a 0 blood pressure.
    """
    flags: list[str] = []
    clean: dict = {}
    for key, (lo, hi) in PLAUSIBLE.items():
        val = _to_float(raw.get(key))
        if val is None:
            clean[key] = None
            flags.append(f"{key}: missing")
            continue
        # Fahrenheit-in-Celsius field auto-correction (common nurse mistake)
        if key == "temp_c" and 94.0 <= val <= 108.0:
            converted = round((val - 32) * 5 / 9, 1)
            flags.append(f"temp_c looked like Fahrenheit ({val}) -> {converted}C")
            val = converted
        if val < lo or val > hi:
            clean[key] = None
            flags.append(f"{key}: implausible value {val} -> treated as missing")
        else:
            clean[key] = val
    return clean, flags


# ---------------------------------------------------------------------------
# Red-flag symptom keywords (English + Hindi transliteration + Hinglish)
# ---------------------------------------------------------------------------
RED_FLAG_PATTERNS: list[tuple[str, str, int]] = [
    # (regex, human reason, escalate-to level)
    (r"chest pain|seene? mein dard|chaati mein dard|chest (tight|pressure|heav)",
     "Chest pain / pressure", 2),
    (r"left arm|jaw|radiat", "Pain radiating to arm/jaw", 2),
    (r"can.?not breathe|cannot breath|trouble breathing|difficulty breathing|"
     r"saans (lene|nahi)|saans phool|short of breath|throat (clos|tight)",
     "Breathing difficulty", 2),
    (r"face droop|slurred|one side|ek taraf|mooh tedha|sunn ho|weakness .*side",
     "Possible stroke (FAST) signs", 1),
    (r"unconscious|behoshi|faint|passed out|unrespons|drowsy",
     "Altered consciousness", 2),
    (r"severe bleed|bahut khoon|heavy bleeding|khoon beh", "Severe bleeding", 2),
    (r"swelling of face|chehra sooj|hives|anaphyla|allergic reaction",
     "Possible anaphylaxis", 1),
    (r"swallow(ed)? pills|overdose|zeher|poison|too many tablets",
     "Possible poisoning/overdose", 1),
    (r"bleeding.*pregnan|pregnan.*bleed|pregnancy.*blood", "Bleeding in pregnancy", 2),
]


@dataclass
class EscalationResult:
    final_level: int
    red_flags: list[str] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)
    forced_department: str | None = None

    @property
    def overridden(self) -> bool:
        return bool(self.rules_fired)


def apply_escalation(model_level: int, clean_v: dict, complaint: str,
                     model_department: str | None = None) -> EscalationResult:
    """Combine the model's level with hard safety rules.

    The returned level is always the MOST urgent (lowest number) of the model
    and any fired rule.
    """
    level = model_level
    red_flags: list[str] = []
    rules_fired: list[str] = []
    forced_department = None

    text = (complaint or "").lower()

    # --- vitals-based critical overrides ---------------------------------
    spo2 = clean_v.get("spo2")
    if spo2 is not None and spo2 < 90:
        level = min(level, 1 if spo2 < 85 else 2)
        rules_fired.append(f"SpO2 {spo2}% < 90 -> level {1 if spo2 < 85 else 2}")
        red_flags.append("Hypoxia")

    sys = clean_v.get("bp_systolic")
    if sys is not None and (sys < 90 or sys > 220):
        level = min(level, 2)
        rules_fired.append(f"Systolic BP {sys} out of safe range -> level 2")
        red_flags.append("Abnormal blood pressure")

    pulse = clean_v.get("pulse")
    if pulse is not None and (pulse > 130 or pulse < 40):
        level = min(level, 2)
        rules_fired.append(f"Pulse {pulse} out of safe range -> level 2")
        red_flags.append("Abnormal heart rate")

    temp = clean_v.get("temp_c")
    if temp is not None and temp >= 40.0:
        level = min(level, 2)
        rules_fired.append(f"Temperature {temp}C >= 40 -> level 2")
        red_flags.append("Hyperpyrexia")
    if temp is not None and temp <= 35.0:
        level = min(level, 2)
        rules_fired.append(f"Temperature {temp}C <= 35 (hypothermia) -> level 2")
        red_flags.append("Hypothermia")

    # --- symptom red-flag keyword overrides ------------------------------
    for pattern, reason, lvl in RED_FLAG_PATTERNS:
        if re.search(pattern, text):
            red_flags.append(reason)
            if lvl < level:
                level = lvl
                rules_fired.append(f"Red flag '{reason}' -> level {lvl}")

    return EscalationResult(
        final_level=level,
        red_flags=sorted(set(red_flags)),
        rules_fired=rules_fired,
        forced_department=forced_department,
    )
