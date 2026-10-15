import AppLayout from "../components/AppLayout.jsx";
import { useQueue } from "../queue/QueueContext.jsx";
import { summarise } from "../lib/analytics.js";
import { LEVEL_META } from "../lib/triage.js";

export default function Analytics() {
  const { items } = useQueue();
  const s = summarise(items);
  const maxLevel = Math.max(1, ...Object.values(s.levelDist));
  const maxDept = Math.max(1, ...s.deptRanked.map(([, n]) => n));
  const maxFlag = Math.max(1, ...s.redFlagsRanked.map(([, n]) => n));

  return (
    <AppLayout title="Analytics" subtitle="Patterns across this session's assessments">
      <div className="stat-row">
        <Stat value={s.total} label="Total assessed" color="#0d9488" />
        <Stat value={`${Math.round(s.avgConfidence * 100)}%`} label="Avg model confidence" color="#2563eb" />
        <Stat value={s.emergencies} label="Emergencies (L1–L2)" color="#dc2626" />
        <Stat
          value={`${s.total ? Math.round((s.abstains / s.total) * 100) : 0}%`}
          label="Abstention rate"
          color="#6d28d9"
        />
      </div>

      {s.total === 0 ? (
        <div className="card">
          <div className="result-list-empty">No data yet — assess some patients first.</div>
        </div>
      ) : (
        <div className="dash-two">
          <div className="card">
            <h3 className="card-title">Triage levels</h3>
            <div className="bars">
              {[1, 2, 3, 4, 5].map((lvl) => (
                <div className="bar-row" key={lvl}>
                  <span className="bar-label">L{lvl}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{
                      width: `${(s.levelDist[lvl] / maxLevel) * 100}%`,
                      background: LEVEL_META[lvl].color,
                    }} />
                  </div>
                  <span className="bar-count">{s.levelDist[lvl]}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Departments</h3>
            <div className="bars">
              {s.deptRanked.map(([dept, n]) => (
                <div className="bar-row" key={dept}>
                  <span className="bar-label wide">{dept}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${(n / maxDept) * 100}%`, background: "#0d9488" }} />
                  </div>
                  <span className="bar-count">{n}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {s.redFlagsRanked.length > 0 && (
        <div className="card">
          <h3 className="card-title">Most common red flags</h3>
          <div className="bars">
            {s.redFlagsRanked.slice(0, 8).map(([flag, n]) => (
              <div className="bar-row" key={flag}>
                <span className="bar-label wide">{flag}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(n / maxFlag) * 100}%`, background: "#dc2626" }} />
                </div>
                <span className="bar-count">{n}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </AppLayout>
  );
}

function Stat({ value, label, color }) {
  return (
    <div className="card stat">
      <div className="stat-num" style={{ color }}>{value}</div>
      <div className="stat-cap">{label}</div>
    </div>
  );
}
