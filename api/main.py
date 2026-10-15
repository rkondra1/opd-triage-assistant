"""
FastAPI backend for the OPD Triage Assistant.

This exposes the existing Python ML engine (src/) over HTTP so the React
frontend (web/) can use it, and provides real staff authentication (api/auth.py).

Run from the project root:
    uvicorn api.main:app --reload --port 8000

Endpoints
    GET  /api/health          -> liveness + whether the ML model is loaded
    POST /api/auth/login      -> {username, password} -> JWT + user info
    GET  /api/me              -> current user (requires Bearer token)
    POST /api/triage          -> run a triage assessment (requires Bearer token)

The triage endpoint reuses TriageEngine from src/predict.py; the model is
loaded lazily on first use. Only the login screen is wired into the UI so far,
but the engine endpoint is ready for the dashboard/triage screens.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

# allow `from src...` and `from api...` when run via uvicorn from project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api import auth  # noqa: E402

app = FastAPI(title="OPD Triage Assistant API", version="1.0.0")

# CORS: during development the Vite dev server runs on :5173 (and :3000).
# Override with OPD_CORS_ORIGINS="https://your-site" (comma-separated) in prod.
_origins = os.environ.get(
    "OPD_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
def current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = auth.decode_token(creds.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., max_length=64)
    password: str = Field(..., max_length=128)


class TriageRequest(BaseModel):
    age: int = 45
    sex: str = "M"
    bp_systolic: float = 120
    bp_diastolic: float = 80
    pulse: float = 78
    temp_c: float = 37.0
    spo2: float = 98
    chief_complaint: str = ""
    known_conditions: str = "none"
    medications: str = "none"


# ---------------------------------------------------------------------------
# Lazy ML engine
# ---------------------------------------------------------------------------
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        from src.predict import TriageEngine

        _engine = TriageEngine.load()
    return _engine


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health() -> dict:
    model_path = os.path.join(PROJECT_ROOT, "models", "triage_model.joblib")
    return {"status": "ok", "model_loaded": os.path.exists(model_path)}


@app.post("/api/auth/login")
def login(body: LoginRequest) -> dict:
    user = auth.authenticate(body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return auth.create_token(user)


@app.get("/api/me")
def me(user: dict = Depends(current_user)) -> dict:
    return {"username": user["sub"], "role": user["role"], "name": user.get("name")}


@app.post("/api/triage")
def triage(body: TriageRequest, user: dict = Depends(current_user)) -> dict:
    engine = get_engine()
    result = engine.predict_one(body.model_dump())
    return result.to_dict()
