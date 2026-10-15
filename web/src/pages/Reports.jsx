import AppLayout from "../components/AppLayout.jsx";
import { useQueue } from "../queue/QueueContext.jsx";
import { summarise, toCSV } from "../lib/analytics.js";
import { LEVEL_META } from "../lib/triage.js";

export default function Reports() {
  const { items } = useQueue();
  const s = summarise(items);

  function downloadCSV() {
    const csv = toCSV(items);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `opd-triage-report-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <AppLayout
      title="Reports"
      subtitle="Session summary for handover / records"
      actions={
        <button className="btn-primary compact" onClick={downloadCSV} disabled={!items.length}>
          ⬇ Download CSV
        </button>
      }
    >
      <div className="card report-summary">
        <h3 className="card-title">Session summary</h3>
        <div className="summary-grid">
          <SummaryItem label="Total patients" value={s.total} />
          <SummaryItem label="Currently waiting" value={s.waiting} />
          <SummaryItem label="Seen" value={s.seen} />
          <SummaryItem label="Emergencies (L1–L2)" value={s.emergencies} />
          <SummaryItem label="Sent to nurse" value={s.abstains} />
          <SummaryItem label="Avg confidence" value={`${Math.round(s.avgConfidence * 100)}%`} />
        </div>
      </div>

      <div className="card">
        <h3 className="card-title">Breakdown by triage level</h3>
        {s.total === 0 ? (
          <div className="result-list-empty">No patients recorded yet.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>Level</th><th>Meaning</th><th>Target</th><th>Count</th><th>Share</th></tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4, 5].map((lvl) => (
                <tr key={lvl}>
                  <td>
                    <span className="level-pill" style={{ background: LEVEL_META[lvl].color }}>
                      L{lvl}
                    </span>
                  </td>
                  <td className="strong">{LEVEL_META[lvl].name}</td>
                  <td>{LEVEL_META[lvl].target}</td>
                  <td>{s.levelDist[lvl]}</td>
                  <td>{s.total ? Math.round((s.levelDist[lvl] / s.total) * 100) : 0}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </AppLayout>
  );
}

function SummaryItem({ label, value }) {
  return (
    <div className="summary-item">
      <div className="summary-value">{value}</div>
      <div className="summary-label">{label}</div>
    </div>
  );
}
