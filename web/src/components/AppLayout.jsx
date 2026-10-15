import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";
import PulseLogo from "./PulseLogo.jsx";

const ALL = ["nurse", "doctor", "admin"];
const CLINICAL = ["doctor", "admin"];

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: "grid", roles: ALL },
  { to: "/triage", label: "New triage", icon: "pulse", roles: ALL },
  { to: "/queue", label: "Patient queue", icon: "list", roles: ALL },
  { to: "/patients", label: "Patients", icon: "users", roles: ALL },
  { to: "/analytics", label: "Analytics", icon: "chart", roles: CLINICAL },
  { to: "/reports", label: "Reports", icon: "doc", roles: CLINICAL },
  { to: "/admin", label: "Admin", icon: "shield", roles: ["admin"] },
];

const NAV_FOOTER = [
  { to: "/profile", label: "Profile", icon: "user", roles: ALL },
  { to: "/settings", label: "Settings", icon: "gear", roles: ALL },
];

function Icon({ name }) {
  const paths = {
    grid: "M4 4h7v7H4zM13 4h7v7h-7zM13 13h7v7h-7zM4 13h7v7H4z",
    pulse: "M3 12h4l2-6 3 12 2.5-7 1.5 3H21",
    list: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
    shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
    users: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0 0M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
    chart: "M3 3v18h18M7 15l3-3 3 3 5-6",
    doc: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M8 13h8M8 17h8",
    user: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 7a4 4 0 1 0 0 0",
    gear: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-2.82 1.17V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 7.5 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 3 12.6a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 7.5a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 12 3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 2.82 1.17l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 21 12.6a2 2 0 1 1 0 4z",
  };
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d={paths[name] || paths.grid} />
    </svg>
  );
}

export default function AppLayout({ title, subtitle, children, actions }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const role = user?.role || "nurse";
  const items = NAV.filter((n) => n.roles.includes(role));
  const footerItems = NAV_FOOTER.filter((n) => n.roles.includes(role));

  function onLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="shell">
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-brand">
          <PulseLogo size={36} />
          <div className="brand-text">
            <div className="brand-name">MediPriority</div>
            <div className="brand-sub">AI · OPD TRIAGE</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {items.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
              onClick={() => setOpen(false)}
            >
              <Icon name={n.icon} />
              <span>{n.label}</span>
            </NavLink>
          ))}

          <div className="nav-sep" />
          {footerItems.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
              onClick={() => setOpen(false)}
            >
              <Icon name={n.icon} />
              <span>{n.label}</span>
            </NavLink>
          ))}
        </nav>

        <NavLink to="/profile" className="sidebar-user" onClick={() => setOpen(false)}>
          <div className="avatar">{(user?.name || user?.username || "?")[0].toUpperCase()}</div>
          <div className="sidebar-user-meta">
            <div className="su-name">{user?.name || user?.username}</div>
            <div className="su-role">{role}</div>
          </div>
        </NavLink>
      </aside>

      {open && <div className="scrim" onClick={() => setOpen(false)} />}

      <div className="main">
        <header className="topbar">
          <button className="hamburger" onClick={() => setOpen((v) => !v)} aria-label="Menu">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M3 6h18M3 12h18M3 18h18" />
            </svg>
          </button>
          <div className="topbar-titles">
            <h1>{title}</h1>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <div className="topbar-actions">
            {actions}
            <button className="btn-ghost dark" onClick={onLogout}>Sign out</button>
          </div>
        </header>

        <main className="content">{children}</main>
      </div>
    </div>
  );
}
