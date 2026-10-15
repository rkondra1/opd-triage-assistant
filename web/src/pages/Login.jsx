import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";
import PulseLogo from "../components/PulseLogo.jsx";

const STATS = [
  { value: "60s", label: "Target assessment" },
  { value: "5", label: "Triage levels" },
  { value: "20×", label: "Under-triage penalty" },
];

const DEMO_ACCOUNTS = [
  { role: "Nurse", username: "nurse", password: "nurse123", variant: "teal" },
  { role: "Doctor", username: "doctor", password: "doctor123", variant: "indigo" },
  { role: "Admin", username: "admin", password: "admin123", variant: "dark" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(user, pass) {
    setError("");
    setLoading(true);
    try {
      await login(user, pass);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Sign in failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e) {
    e.preventDefault();
    if (!username || !password) {
      setError("Please enter both username and password.");
      return;
    }
    submit(username, password);
  }

  function onDemo(acct) {
    setUsername(acct.username);
    setPassword(acct.password);
    submit(acct.username, acct.password);
  }

  return (
    <div className="login">
      {/* ---------- Left hero panel ---------- */}
      <section className="hero">
        <div className="brand">
          <PulseLogo size={44} />
          <div className="brand-text">
            <div className="brand-name">MediPriority</div>
            <div className="brand-sub">AI · OPD TRIAGE ASSISTANT</div>
          </div>
        </div>

        <div className="hero-body">
          <h1 className="hero-title">
            Rapid triage.
            <br />
            <span className="accent">Patient safety first.</span>
          </h1>
          <p className="hero-lede">
            Decision support for overloaded outpatient departments. Every patient
            assessed in under 60 seconds, with mandatory safety rules that can only
            raise urgency — never lower it.
          </p>

          <div className="stats">
            {STATS.map((s) => (
              <div className="stat-card" key={s.label}>
                <div className="stat-value">{s.value}</div>
                <div className="stat-label">{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="hero-footer">
          Clinical prototype · Synthetic data · Not for automated clinical use
        </div>
      </section>

      {/* ---------- Right sign-in panel ---------- */}
      <section className="signin-panel">
        <div className="signin-card">
          <h2 className="signin-title">Staff sign in</h2>
          <p className="signin-sub">Access your clinical dashboard</p>

          <form onSubmit={onSubmit} className="signin-form" noValidate>
            <label className="field">
              <span className="field-label">USERNAME</span>
              <input
                type="text"
                autoComplete="username"
                placeholder="nurse / doctor / admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
              />
            </label>

            <label className="field">
              <span className="field-label">PASSWORD</span>
              <input
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </label>

            {error && <div className="form-error" role="alert">{error}</div>}

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="demo-divider">
            <span>QUICK DEMO LOGIN</span>
          </div>

          <div className="demo-grid">
            {DEMO_ACCOUNTS.map((acct) => (
              <button
                key={acct.role}
                type="button"
                className={`demo-card demo-${acct.variant}`}
                onClick={() => onDemo(acct)}
                disabled={loading}
              >
                <span className="demo-role">{acct.role}</span>
                <span className="demo-creds">
                  {acct.username} / {acct.password}
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
