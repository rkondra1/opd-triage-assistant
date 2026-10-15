# MediPriority — Web UI (React)

A React frontend that recreates the OPD Triage Assistant login experience and
talks to the FastAPI backend in [`../api`](../api). It does **not** replace the
Streamlit demo in [`../app`](../app) — both can be used independently.

## Run it (local development)

You need **two terminals**.

### Terminal 1 — backend API

From the project root (with the Python virtual environment active):

```bash
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8000
```

### Terminal 2 — frontend

```bash
cd web
npm install
npm run dev
```

Open **http://localhost:5173/login**.

The dev server automatically forwards `/api` requests to the backend on port
8000, so you don't need to configure anything for local use.

## Sign in

Use any of the seeded staff accounts (also shown as "Quick demo login" buttons):

| Role   | Username | Password   |
| ------ | -------- | ---------- |
| Nurse  | `nurse`  | `nurse123` |
| Doctor | `doctor` | `doctor123`|
| Admin  | `admin`  | `admin123` |

Logins are verified by the backend (hashed passwords + a signed token) — this is
real authentication, not a mock.

## Build for production

```bash
npm run build      # outputs static files to web/dist/
npm run preview    # preview the production build locally
```

When hosting the built frontend separately from the backend, set
`VITE_API_BASE` (see `.env.example`) to the backend's URL and configure
`OPD_CORS_ORIGINS` on the backend.

## Project layout

```
web/
  index.html
  vite.config.js          # dev server + /api proxy
  src/
    main.jsx              # app entry (router + auth provider)
    App.jsx               # routes + protected-route guard
    index.css             # design system (colors, typography, layout)
    lib/api.js            # tiny fetch client
    auth/AuthContext.jsx  # session state (login/logout, token storage)
    components/PulseLogo.jsx
    pages/Login.jsx       # the recreated login page
    pages/Dashboard.jsx   # placeholder landing after login
```
