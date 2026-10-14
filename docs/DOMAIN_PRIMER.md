# Domain Primer — OPD Triage

A short clinical-context document for the project. It explains the triage
scale, the red flags, and the safety philosophy the system must follow.

## The setting

A government hospital outpatient department (OPD) sees ~800 walk-ins a day with
only two doctors. Today patients are seen first-come-first-served, so a person
with chest pain can wait behind 40 people with mild fever. A nurse makes the
triage call in ~30 seconds. The assistant exists to make that 30-second call
**safer and more consistent** — not to replace the nurse.

## The 5-level triage scale (ESI-style)

Lower number = more urgent.

| Level | Name          | See within | Meaning |
|-------|---------------|-----------|---------|
| 1 | Resuscitation | immediate | Life-threatening; needs life-saving action now |
| 2 | Emergent      | ~10 min   | High risk / severe distress |
| 3 | Urgent        | ~30 min   | Stable but needs several resources |
| 4 | Less urgent   | ~60 min   | Stable, probably one resource |
| 5 | Non-urgent    | ~120 min  | Routine problem |

## Red flags (must never be missed)

These trigger the **hard escalation rules** regardless of the model:

- **SpO2 < 90%** → hypoxia (SpO2 < 85% → Level 1)
- **Systolic BP < 90 or > 220** → shock / hypertensive crisis
- **Pulse > 130 or < 40** → unstable rhythm
- **Temp ≥ 40 °C or ≤ 35 °C** → hyperpyrexia / hypothermia
- **Chest pain / pressure**, pain radiating to arm or jaw
- **Breathing difficulty**, throat closing
- **Stroke (FAST) signs**: face droop, one-sided weakness, slurred speech
- **Altered consciousness**, fainting, unresponsiveness
- **Severe bleeding**, bleeding in pregnancy
- **Anaphylaxis** (facial swelling + hives + breathing trouble)
- **Poisoning / overdose**

## Data-quality realities

Vitals are often missing or mis-entered. The system must **not trust**:

- `0` blood pressure or `0` SpO2 → treat as missing
- A temperature of `96` in a Celsius field → almost certainly Fahrenheit;
  auto-convert, otherwise treat as missing
- Patients may under- or over-report symptoms

## Safety philosophy (why accuracy is the wrong metric)

Under-triaging a true emergency (calling it less urgent than it is) can kill
someone. Over-triaging a mild case just wastes a little doctor time. So:

- **Under-triage is penalised ~20× more than over-triage.**
- Missing a **true emergency** carries a large extra penalty.
- The system may **abstain** ("cannot assess — send to nurse now"). Abstaining
  is a small, bounded cost — much safer than guessing wrong on an emergency.
- **Emergency sensitivity/recall** is reported separately and prominently.

A model that just maximises accuracy will look great on the 96% of easy cases
and quietly kill people in the 4% that matter. The whole design — asymmetric
cost, hard rules, abstention — exists to prevent that.
