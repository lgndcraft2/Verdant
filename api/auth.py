from __future__ import annotations

import hashlib
import logging
import secrets
from typing import Any

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


async def verify_supabase_jwt(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> dict[str, Any]:
    """FastAPI dependency that authenticates a dashboard user via their Supabase session.

    Used to guard management endpoints (issuing keys, setting provider keys). The bearer
    token is the Supabase access token; it's validated against the Auth server.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session token. Sign in to the dashboard first.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db = request.app.state.db
    user = await db.get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


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

    if record.get("hashed_key") != hashed:
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
