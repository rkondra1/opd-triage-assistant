import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";
import PulseLogo from "./PulseLogo.jsx";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: "grid", roles: ["nurse", "doctor", "admin"] },
  { to: "/triage", label: "New triage", icon: "pulse", roles: ["nurse", "doctor", "admin"] },
  { to: "/queue", label: "Patient queue", icon: "list", roles: ["nurse", "doctor", "admin"] },
  { to: "/admin", label: "Admin", icon: "shield", roles: ["admin"] },
];

function Icon({ name }) {
  const paths = {
    grid: "M4 4h7v7H4zM13 4h7v7h-7zM13 13h7v7h-7zM4 13h7v7H4z",
    pulse: "M3 12h4l2-6 3 12 2.5-7 1.5 3H21",
    list: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
    shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
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
        </nav>

        <div className="sidebar-user">
          <div className="avatar">{(user?.name || user?.username || "?")[0].toUpperCase()}</div>
          <div className="sidebar-user-meta">
            <div className="su-name">{user?.name || user?.username}</div>
            <div className="su-role">{role}</div>
          </div>
        </div>
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
