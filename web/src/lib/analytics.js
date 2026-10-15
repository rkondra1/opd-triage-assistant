// Pure helpers that turn the queue entries into summary analytics.
import { LEVEL_META, ABSTAIN_META } from "./triage.js";

export function summarise(items) {
  const total = items.length;
  const seen = items.filter((i) => i.status === "seen").length;
  const abstains = items.filter(
    (i) => i.result?.abstained || i.result?.triage_level === "ABSTAIN"
  ).length;
  const emergencies = items.filter(
    (i) => i.result?.triage_level === 1 || i.result?.triage_level === 2
  ).length;

  const levelDist = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  const deptDist = {};
  const redFlags = {};
  let confSum = 0;
  let confCount = 0;

  items.forEach((i) => {
    const r = i.result || {};
    const lvl = Number(r.triage_level);
    if (levelDist[lvl] !== undefined) levelDist[lvl] += 1;

    const dept = r.department || "—";
    deptDist[dept] = (deptDist[dept] || 0) + 1;

    (r.red_flags || []).forEach((f) => {
      redFlags[f] = (redFlags[f] || 0) + 1;
    });

    if (typeof r.confidence === "number") {
      confSum += r.confidence;
      confCount += 1;
    }
  });

  const avgConfidence = confCount ? confSum / confCount : 0;

  const deptRanked = Object.entries(deptDist).sort((a, b) => b[1] - a[1]);
  const redFlagsRanked = Object.entries(redFlags).sort((a, b) => b[1] - a[1]);

  return {
    total,
    seen,
    waiting: total - seen,
    abstains,
    emergencies,
    levelDist,
    deptRanked,
    redFlagsRanked,
    avgConfidence,
  };
}

export function levelColor(lvl) {
  return LEVEL_META[Number(lvl)]?.color || ABSTAIN_META.color;
}

// Build a CSV string from the queue entries (for the Reports download).
export function toCSV(items) {
  const header = [
    "created_at",
    "name",
    "age",
    "sex",
    "complaint",
    "triage_level",
    "level_name",
    "department",
    "confidence",
    "red_flags",
    "rules_fired",
    "status",
  ];
  const rows = items.map((i) => {
    const r = i.result || {};
    const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    return [
      i.createdAt,
      i.patient?.name,
      i.patient?.age,
      i.patient?.sex,
      i.complaint,
      r.triage_level,
      r.level_name,
      r.department,
      r.confidence,
      (r.red_flags || []).join("; "),
      (r.rules_fired || []).join("; "),
      i.status,
    ].map(esc).join(",");
  });
  return [header.join(","), ...rows].join("\n");
}
