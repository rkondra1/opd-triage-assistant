// Display metadata for triage levels (mirrors src/triage_rubric.py colours used
// in the Streamlit app, adapted to the web palette).
export const LEVEL_META = {
  1: { name: "Resuscitation", color: "#b71c1c", target: "Immediate" },
  2: { name: "Emergent", color: "#e64a19", target: "~10 min" },
  3: { name: "Urgent", color: "#f9a825", target: "~30 min" },
  4: { name: "Less urgent", color: "#2e7d32", target: "~1 hour" },
  5: { name: "Non-urgent", color: "#1565c0", target: "~2 hours" },
};

export const ABSTAIN_META = {
  name: "Send to nurse now",
  color: "#6d28d9",
  target: "Human review",
};

export function levelDisplay(result) {
  if (!result) return ABSTAIN_META;
  if (result.abstained || result.triage_level === "ABSTAIN") return ABSTAIN_META;
  return LEVEL_META[Number(result.triage_level)] || ABSTAIN_META;
}
