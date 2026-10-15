// Tiny API client. In development, requests to /api are proxied to the FastAPI
// backend (see vite.config.js). In production set VITE_API_BASE to the backend
// origin (e.g. https://your-api.example.com).
const API_BASE = import.meta.env.VITE_API_BASE || "";

async function request(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    // non-JSON response
  }

  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  login: (username, password) =>
    request("/api/auth/login", { method: "POST", body: { username, password } }),
  me: (token) => request("/api/me", { token }),
  health: () => request("/api/health"),
  meta: (token) => request("/api/meta", { token }),
  triage: (token, record) =>
    request("/api/triage", { method: "POST", token, body: record }),
};
