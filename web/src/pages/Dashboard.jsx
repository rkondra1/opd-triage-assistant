import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";
import PulseLogo from "../components/PulseLogo.jsx";

// Placeholder landing shown after a successful real login.
// The authenticated dashboard/triage/queue screens from the reference app are
// NOT yet implemented here because they could not be inspected (the reference
// backend was offline). This screen confirms that real auth works end to end.
export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function onLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="dash">
      <header className="dash-top">
        <div className="brand">
          <PulseLogo size={36} />
          <div className="brand-text">
            <div className="brand-name">MediPriority</div>
            <div className="brand-sub">AI · OPD TRIAGE ASSISTANT</div>
          </div>
        </div>
        <button className="btn-ghost" onClick={onLogout}>
          Sign out
        </button>
      </header>

      <main className="dash-body">
        <div className="dash-card">
          <div className="dash-badge">{user?.role?.toUpperCase()}</div>
          <h1>Welcome, {user?.name || user?.username}</h1>
          <p>
            You are signed in with a real, server-verified session. The clinical
            dashboard screens are coming next — the login experience is live.
          </p>
        </div>
      </main>
    </div>
  );
}
