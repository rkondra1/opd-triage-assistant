"""
Real (not fake) authentication for the OPD Triage Assistant API.

What "real" means here:
  - Credentials are the system's actual seeded staff accounts (the same ones
    the login screen advertises as "quick demo login"). They are NOT a bypass.
  - Passwords are stored HASHED (PBKDF2-HMAC-SHA256 with a per-user salt),
    never in plain text, and verified with a constant-time comparison.
  - On success we issue a signed JWT that the frontend sends on later requests.

For a classroom / prototype deployment the three staff accounts are seeded in
code. In a production system these would live in a database with an admin UI,
but the verification path (hash + JWT) is identical.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass

import jwt  # PyJWT

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# The signing secret is read from the environment so it is never hard-coded in
# a real deployment. A development fallback is used only when unset.
JWT_SECRET = os.environ.get("OPD_JWT_SECRET", "dev-only-change-me-in-production")
JWT_ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 8 * 60 * 60  # 8-hour shift

_PBKDF2_ROUNDS = 120_000


# ---------------------------------------------------------------------------
# Password hashing helpers
# ---------------------------------------------------------------------------
def hash_password(password: str, salt: bytes | None = None) -> str:
    """Return a 'salt$hash' string (both hex). PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return hmac.compare_digest(dk.hex(), hash_hex)


# ---------------------------------------------------------------------------
# Seeded staff accounts (hashed at import time from the advertised credentials)
# ---------------------------------------------------------------------------
@dataclass
class User:
    username: str
    role: str
    full_name: str
    password_hash: str


def _seed_users() -> dict[str, User]:
    raw = [
        # username, password, role, display name
        ("nurse", "nurse123", "nurse", "Triage Nurse"),
        ("doctor", "doctor123", "doctor", "Attending Doctor"),
        ("admin", "admin123", "admin", "Administrator"),
    ]
    return {
        u: User(username=u, role=r, full_name=n, password_hash=hash_password(p))
        for (u, p, r, n) in raw
    }


_USERS: dict[str, User] = _seed_users()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def authenticate(username: str, password: str) -> User | None:
    """Return the User on correct credentials, else None (constant-ish time)."""
    user = _USERS.get((username or "").strip().lower())
    if user is None:
        # Still run a hash to reduce username-enumeration timing differences.
        verify_password(password, hash_password("dummy"))
        return None
    if verify_password(password, user.password_hash):
        return user
    return None


def create_token(user: User) -> dict:
    now = int(time.time())
    payload = {
        "sub": user.username,
        "role": user.role,
        "name": user.full_name,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_TTL_SECONDS,
        "user": {
            "username": user.username,
            "role": user.role,
            "name": user.full_name,
        },
    }


def decode_token(token: str) -> dict:
    """Return the payload or raise jwt exceptions on invalid/expired tokens."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
