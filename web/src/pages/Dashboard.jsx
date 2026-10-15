import { Link } from "react-router-dom";
import AppLayout from "../components/AppLayout.jsx";
import { useAuth } from "../auth/AuthContext.jsx";
import { useQueue, queueSortKey } from "../queue/QueueContext.jsx";
import { LEVEL_META, levelDisplay } from "../lib/triage.js";

export default function Dashboard() {
  const { user } = useAuth();
  const { items } = useQueue();

  const total = items.length;
  const waiting = items.filter((i) => i.status !== "seen").length;
  const emergencies = items.filter((i) => {
    const lvl = i.result?.triage_level;
    return lvl === 1 || lvl === 2;
  }).length;
  const abstains = items.filter(
    (i) => i.result?.abstained || i.result?.triage_level === "ABSTAIN"
  ).length;

  // level distribution
  const dist = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  items.forEach((i) => {
    const lvl = Number(i.result?.triage_level);
    if (dist[lvl] !== undefined) dist[lvl] += 1;
  });
  const maxDist = Math.max(1, ...Object.values(dist));

  const topNext = [...items]
    .filter((i) => i.status !== "seen")
    .sort((a, b) => {
      const ka = queueSortKey(a), kb = queueSortKey(b);
      return ka[0] - kb[0] || ka[1] - kb[1];
    })
    .slice(0, 5);

  return (
    <AppLayout
      title={`Welcome, ${user?.name || user?.username}`}
      subtitle="Live overview of today's triage activity"
      actions={<Link to="/triage" className="btn-primary compact">+ New triage</Link>}
    >
      <div className="stat-row">
        <StatCard value={total} label="Assessed (this session)" accent="#0d9488" />
        <StatCard value={waiting} label="Currently waiting" accent="#2563eb" />
        <StatCard value={emergencies} label="Emergencies (L1–L2)" accent="#dc2626" />
        <StatCard value={abstains} label="Sent to nurse" accent="#6d28d9" />
      </div>

      <div className="dash-two">
        <div className="card">
          <h3 className="card-title">Triage level distribution</h3>
          {total === 0 ? (
            <div className="result-list-empty">No assessments yet.</div>
          ) : (
            <div className="bars">
              {[1, 2, 3, 4, 5].map((lvl) => (
                <div className="bar-row" key={lvl}>
                  <span className="bar-label">L{lvl}</span>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(dist[lvl] / maxDist) * 100}%`,
                        background: LEVEL_META[lvl].color,
                      }}
                    />
                  </div>
                  <span className="bar-count">{dist[lvl]}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h3 className="card-title">Next to be seen</h3>
          {topNext.length === 0 ? (
            <div className="result-list-empty">
              Queue is empty. <Link to="/triage">Assess a patient →</Link>
            </div>
          ) : (
            <ul className="next-list">
              {topNext.map((e) => {
                const meta = levelDisplay(e.result);
                return (
                  <li key={e.id}>
                    <span className="dot" style={{ background: meta.color }} />
                    <span className="next-name">{e.patient?.name || "Unnamed"}</span>
                    <span className="next-meta">{meta.name}</span>
                    <span className="next-dept">{e.result?.department}</span>
                  </li>
                );
              })}
            </ul>
          )}
          <Link to="/queue" className="card-link">Open full queue →</Link>
        </div>
      </div>
    </AppLayout>
  );
}

function StatCard({ value, label, accent }) {
  return (
    <div className="card stat">
      <div className="stat-num" style={{ color: accent }}>{value}</div>
      <div className="stat-cap">{label}</div>
    </div>
  );
}
