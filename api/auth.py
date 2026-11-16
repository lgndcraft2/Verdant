from __future__ import annotations

import hashlib
import logging
import secrets
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt

from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# VERDANT keys look like: vd_live_<48 hex chars>. The prefix (first 12 chars,
# "vd_live_XXXX") is stored unhashed for fast lookup and safe display.
API_KEY_PREFIX = "vd_live_"


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _key_prefix(raw_key: str) -> str:
    return raw_key[:12] if len(raw_key) >= 12 else raw_key


def generate_api_key() -> tuple[str, str, str]:
    """Mint a new VERDANT API key. Returns (raw_key, key_prefix, hashed_key).

    The raw key is shown to the user exactly once; only the prefix and hash are stored.
    """
    raw_key = f"{API_KEY_PREFIX}{secrets.token_hex(24)}"
    return raw_key, _key_prefix(raw_key), _hash_key(raw_key)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return "$".join(("pbkdf2_sha256", "600000", salt.hex(), digest.hex()))


def check_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(candidate, bytes.fromhex(digest))
    except (ValueError, TypeError):
        return False


def issue_token(user: dict[str, Any], secret: str) -> str:
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must contain at least 32 characters")
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user["id"]), "iss": "verdant", "aud": "verdant-dashboard",
                       "iat": now, "exp": now + timedelta(hours=12)}, secret, algorithm="HS256")


async def verify_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> dict[str, Any]:
    """Validate an app-issued JWT and load its current user from Neon."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session token. Sign in to the dashboard first.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db = request.app.state.db
    try:
        claims = jwt.decode(credentials.credentials, request.app.state.settings.jwt_secret,
                            algorithms=["HS256"], issuer="verdant", audience="verdant-dashboard")
        user = await db.get_user_by_id(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        user = None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user_id": str(user["id"]), "email": user["email"], "full_name": user["full_name"], "role": user["role"]}


async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> dict[str, Any]:
    """FastAPI dependency that validates the Bearer token against the api_keys table."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Pass your VERDANT API key as a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_key = credentials.credentials
    prefix = _key_prefix(raw_key)
    hashed = _hash_key(raw_key)

    db = request.app.state.db
    record = await db.fetch_api_key(prefix)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not hmac.compare_digest(record.get("hashed_key", ""), hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not record.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has been deactivated.",
        )

    await db.touch_api_key_last_used(prefix)
    return record


async def verify_reader(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> dict[str, Any]:
    if credentials and credentials.credentials.startswith(API_KEY_PREFIX):
        return await verify_api_key(request, credentials)
    user = await verify_session(request, credentials)
    return {"owner_id": user["user_id"]}
