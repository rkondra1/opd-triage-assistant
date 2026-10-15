# Web UI Implementation Report

This report documents the recreation of the reference application's user
interface (reference: the "MediPriority" OPD Triage Assistant login experience)
inside this existing project.

## 1. Summary

A new **React frontend** (`web/`) and a **FastAPI backend** (`api/`) were added
to the project. The React app faithfully recreates the reference **login page**,
and the backend provides **real, server-verified authentication** that the login
page talks to. The existing Streamlit demo (`app/`) and the machine-learning code
(`src/`) were **not modified** — the new UI sits alongside them and reuses the
same `TriageEngine`.

## 2. What was inspected vs. what was built

| Screen | Could it be inspected? | Status |
| --- | --- | --- |
| Login page | Yes — rendered in a real browser | **Recreated natively** (not an iframe or screenshot) |
| Dashboard, Patients, Triage, Queue, Admin, Reports, Analytics, Settings, Profile | **No** — the reference backend was offline, so these never rendered | Not built. A small placeholder dashboard confirms login works end to end. |

Only the login page could be faithfully reproduced because it is the only screen
that rendered in the reference deployment (the rest sit behind a sleeping
backend). No inaccessible screens were invented.

## 3. Architecture decision

The existing project was 100% Streamlit/Python, while the reference is a React
single-page app. Per the chosen direction, a **React frontend was added** with
the **Python ML code exposed as a backend API**, rather than approximating the
look inside Streamlit. This preserves the original architecture (Streamlit demo +
`src/` ML engine remain intact) while allowing a pixel-faithful UI.

## 4. Design system extracted from the reference

| Token | Value used | Notes |
| --- | --- | --- |
| Primary (teal) | `#14b8a6` → `#0d9488` gradient | Brand colour, primary button, accents |
| Doctor accent | Indigo `#4f46e5` | "Doctor" demo card |
| Admin accent | Slate `#1e293b` → `#0b1220` | "Admin" demo card |
| Hero background | Dark slate gradient with teal/indigo radial glows | Left panel |
| Sign-in panel background | Light slate `#eef1f6` | Right panel |
| Card | White, radius 16px, soft shadow | Sign-in card |
| Typography | Inter (Google Fonts), system-ui fallback | Weights 400–800 |

> Exact hex values could not be programmatically extracted (the reference CSS
> never loaded in automation), so the palette above was matched visually from a
> captured render of the login screen. It is a close, professional match to the
> "MediPriority" teal medical branding.

## 5. Login page — elements recreated

- Brand mark: teal rounded-square with a white pulse/heartbeat glyph, wordmark
  "MediPriority" + "AI · OPD TRIAGE ASSISTANT".
- Split-screen layout: dark hero (left) + light sign-in panel (right).
- Hero: headline "Rapid triage. / Patient safety first." (teal accent), lede
  paragraph, three stat cards (`60s`, `5`, `20×`), footer disclaimer line.
- Sign-in card: "Staff sign in" / "Access your clinical dashboard", USERNAME
  field (placeholder `nurse / doctor / admin`), PASSWORD field, full-width teal
  "Sign in" button.
- "QUICK DEMO LOGIN" row: three cards (Nurse / Doctor / Admin) that fill the
  credentials and submit a real login.
- The hosting platform's "Frontend Preview Only / Wake up servers" banner was
  intentionally **not** copied — it belongs to the reference host, not the app.

## 6. Functional behaviour (not a static mockup)

- The form performs a real `POST /api/auth/login`. Correct credentials receive a
  signed JWT; wrong credentials show an inline error (verified: HTTP 401).
- The three demo buttons submit real logins for the seeded staff accounts.
- On success the app stores the session and routes to `/dashboard`; unauthenticated
  access to `/dashboard` redirects to `/login`.
- Responsive: verified at 1440×900 (desktop) and 390×844 (mobile).

## 7. Authentication (real, not simulated)

`api/auth.py` implements genuine auth:

- Staff accounts (`nurse`, `doctor`, `admin`) are seeded with **PBKDF2-HMAC-SHA256
  hashed** passwords (per-user salt, 120k rounds) — never stored in plain text.
- Login verifies with a constant-time comparison and issues a **signed JWT**
  (`HS256`, 8-hour expiry). The signing secret is read from `OPD_JWT_SECRET`
  (dev fallback only when unset).
- No hardcoded login bypass, no fake "always succeeds" path. These are the
  system's intended demo accounts, authenticated properly.

## 8. How to run

Backend (from project root, with the Python venv active):

```
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8000
```

Frontend (in a second terminal):

```
cd web
npm install
npm run dev
```

Then open http://localhost:5173/login . The Vite dev server proxies `/api` to the
backend on port 8000, so no extra configuration is needed for local development.

## 9. Verification performed

- `npm run build` — frontend compiles cleanly.
- Backend auth unit check — correct creds issue a JWT that round-trips; wrong
  creds and unknown users are rejected.
- End-to-end browser test (Playwright): login page renders on desktop + mobile;
  clicking a demo card performs a real login and navigates to the dashboard.

## 10. Not done / next steps

- The authenticated screens (dashboard, patients, triage, queue, admin, etc.)
  were not built because they could not be inspected (reference backend offline).
  When those screens are available (a live reference or screenshots/design
  export), they can be added as new React routes that call the existing
  `POST /api/triage` endpoint (already wired to `TriageEngine`).
