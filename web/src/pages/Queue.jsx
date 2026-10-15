import { Link } from "react-router-dom";
import AppLayout from "../components/AppLayout.jsx";
import { useQueue, queueSortKey } from "../queue/QueueContext.jsx";
import { levelDisplay } from "../lib/triage.js";

function cmp(a, b) {
  const ka = queueSortKey(a);
  const kb = queueSortKey(b);
  return ka[0] - kb[0] || ka[1] - kb[1];
}

function timeAgo(iso) {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  return `${Math.round(mins / 60)} h ago`;
}

export default function Queue() {
  const { items, updateStatus, remove, clear } = useQueue();
  const sorted = [...items].sort(cmp);
  const waiting = sorted.filter((i) => i.status !== "seen");

  return (
    <AppLayout
      title="Patient queue"
      subtitle={`${waiting.length} waiting · sorted by priority`}
      actions={
        items.length > 0 && (
          <button className="btn-ghost dark" onClick={clear}>Clear all</button>
        )
      }
    >
      {items.length === 0 ? (
        <div className="card empty-state">
          <h3>No patients in the queue yet</h3>
          <p>
            Run an assessment on the <Link to="/triage">New triage</Link> screen and
            add it to the queue. Patients are automatically ordered with the most
            urgent (and any "send to nurse now" cases) at the top.
          </p>
        </div>
      ) : (
        <div className="queue-list">
          {sorted.map((entry) => {
            const meta = levelDisplay(entry.result);
            const seen = entry.status === "seen";
            return (
              <div key={entry.id} className={`queue-card ${seen ? "seen" : ""}`}>
                <div className="queue-level" style={{ background: meta.color }}>
                  {entry.result?.abstained || entry.result?.triage_level === "ABSTAIN"
                    ? "!"
                    : entry.result?.triage_level}
                </div>
                <div className="queue-main">
                  <div className="queue-name">
                    {entry.patient?.name || "Unnamed patient"}
                    <span className="queue-meta">
                      {entry.patient?.age} / {entry.patient?.sex} · {meta.name}
                    </span>
                  </div>
                  <div className="queue-complaint">{entry.complaint}</div>
                  <div className="queue-tags">
                    <span className="tag">{entry.result?.department}</span>
                    {entry.result?.red_flags?.slice(0, 2).map((f, i) => (
                      <span key={i} className="tag tag-red">{f}</span>
                    ))}
                    <span className="tag tag-plain">{timeAgo(entry.createdAt)}</span>
                  </div>
                </div>
                <div className="queue-actions">
                  {seen ? (
                    <span className="status-seen">Seen ✓</span>
                  ) : (
                    <button className="btn-mini" onClick={() => updateStatus(entry.id, "seen")}>
                      Mark seen
                    </button>
                  )}
                  <button className="btn-mini ghost" onClick={() => remove(entry.id)}>
                    Remove
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </AppLayout>
  );
}
