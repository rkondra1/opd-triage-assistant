import { useNavigate } from "react-router-dom";
import AppLayout from "../components/AppLayout.jsx";
import { useAuth } from "../auth/AuthContext.jsx";
import { useQueue } from "../queue/QueueContext.jsx";

function decodeExp(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    if (payload.exp) return new Date(payload.exp * 1000);
  } catch {
    /* ignore */
  }
  return null;
}

export default function Profile() {
  const { user, token, logout } = useAuth();
  const { items } = useQueue();
  const navigate = useNavigate();

  const assessedByMe = items.length; // single-user session
  const exp = token ? decodeExp(token) : null;

  function onLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  const initial = (user?.name || user?.username || "?")[0].toUpperCase();

  return (
    <AppLayout title="Profile" subtitle="Your account and current session">
      <div className="dash-two">
        <div className="card profile-card">
          <div className="profile-head">
            <div className="avatar big">{initial}</div>
            <div>
              <div className="profile-name">{user?.name || user?.username}</div>
              <div className="profile-role">{user?.role}</div>
            </div>
          </div>
          <div className="result-row"><span>Username</span><b>{user?.username}</b></div>
          <div className="result-row"><span>Role</span><b style={{ textTransform: "capitalize" }}>{user?.role}</b></div>
          <div className="result-row">
            <span>Session expires</span>
            <b>{exp ? exp.toLocaleString() : "—"}</b>
          </div>
          <button className="btn-ghost dark profile-logout" onClick={onLogout}>Sign out</button>
        </div>

        <div className="card">
          <h3 className="card-title">This session</h3>
          <div className="summary-grid">
            <div className="summary-item">
              <div className="summary-value">{assessedByMe}</div>
              <div className="summary-label">Patients assessed</div>
            </div>
            <div className="summary-item">
              <div className="summary-value">{items.filter((i) => i.status !== "seen").length}</div>
              <div className="summary-label">Still waiting</div>
            </div>
          </div>
          <p className="muted-note">
            You are authenticated with a server-signed token. Signing out clears it
            from this device.
          </p>
        </div>
      </div>
    </AppLayout>
  );
}
