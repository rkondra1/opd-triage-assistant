import { useEffect, useState } from "react";
import AppLayout from "../components/AppLayout.jsx";
import { useAuth } from "../auth/AuthContext.jsx";
import { api } from "../lib/api.js";
import { LEVEL_META } from "../lib/triage.js";

const STAFF = [
  { role: "Nurse", username: "nurse", scope: "Triage, queue" },
  { role: "Doctor", username: "doctor", scope: "Triage, queue" },
  { role: "Admin", username: "admin", scope: "Full access" },
];

export default function Admin() {
  const { token } = useAuth();
  const [meta, setMeta] = useState(null);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    Promise.all([api.meta(token), api.health()])
      .then(([m, h]) => {
        if (!alive) return;
        setMeta(m);
        setHealth(h);
      })
      .catch((e) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, [token]);

  return (
    <AppLayout title="Admin" subtitle="System configuration & reference">
      {error && <div className="form-error">{error}</div>}

      <div className="stat-row">
        <div className="card stat">
          <div className="stat-num" style={{ color: health?.model_loaded ? "#0d9488" : "#dc2626" }}>
            {health ? (health.model_loaded ? "Ready" : "No model") : "…"}
          </div>
          <div className="stat-cap">ML model status</div>
        </div>
        <div className="card stat">
          <div className="stat-num" style={{ color: "#0d9488" }}>
            {meta ? meta.departments.length : "…"}
          </div>
          <div className="stat-cap">Departments configured</div>
        </div>
        <div className="card stat">
          <div className="stat-num" style={{ color: "#0d9488" }}>5</div>
          <div className="stat-cap">Triage levels</div>
        </div>
      </div>

      <div className="dash-two">
        <div className="card">
          <h3 className="card-title">Staff accounts</h3>
          <table className="admin-table">
            <thead>
              <tr><th>Role</th><th>Username</th><th>Access</th></tr>
            </thead>
            <tbody>
              {STAFF.map((s) => (
                <tr key={s.username}>
                  <td>{s.role}</td>
                  <td><code>{s.username}</code></td>
                  <td>{s.scope}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted-note">
            Passwords are stored hashed on the server (PBKDF2). This panel is
            read-only in the prototype.
          </p>
        </div>

        <div className="card">
          <h3 className="card-title">Triage scale reference</h3>
          <ul className="rubric">
            {meta &&
              Object.entries(meta.triage_levels).map(([lvl, info]) => (
                <li key={lvl}>
                  <span className="dot" style={{ background: LEVEL_META[Number(lvl)]?.color }} />
                  <b>L{lvl} — {info.name}</b>
                  <span className="rubric-def">{info.definition}</span>
                </li>
              ))}
            {!meta && <div className="result-list-empty">Loading…</div>}
          </ul>
        </div>
      </div>

      {meta && (
        <div className="card">
          <h3 className="card-title">Departments</h3>
          <div className="dept-tags">
            {meta.departments.map((d) => (
              <span key={d} className="tag">{d}</span>
            ))}
          </div>
        </div>
      )}
    </AppLayout>
  );
}
