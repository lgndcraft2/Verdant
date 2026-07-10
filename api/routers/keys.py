from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from api.auth import generate_api_key, verify_supabase_jwt

router = APIRouter(tags=["keys"])

# Fields safe to expose to the dashboard (never hashed_key or the raw key).
_PUBLIC_FIELDS = ("id", "key_prefix", "label", "active", "created_at", "last_used_at")


def _envelope(data: Any = None, meta: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "error": error}


def _public_key(record: dict[str, Any]) -> dict[str, Any]:
    return {field: record.get(field) for field in _PUBLIC_FIELDS}


class ApiKeyCreate(BaseModel):
    label: str | None = None


async def _issue_key(request: Request, user: dict[str, Any], label: str | None) -> dict[str, Any]:
    raw_key, key_prefix, hashed_key = generate_api_key()
    db = request.app.state.db
    stored = await db.create_api_key(
        {
            "user_id": user["user_id"],
            "key_prefix": key_prefix,
            "hashed_key": hashed_key,
            "label": label or "Default key",
            "scopes": [],
        }
    )
    return _envelope(
        data={"raw_key": raw_key, **_public_key(stored)},
        meta={"message": "Copy your key now — it won't be shown again."},
    )


@router.get("/keys")
async def list_keys(request: Request, user: dict[str, Any] = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    """List the caller's active VERDANT API keys (prefixes and metadata only)."""
    db = request.app.state.db
    keys = await db.list_api_keys(user["user_id"])
    return _envelope(data=[_public_key(k) for k in keys])


@router.post("/keys")
async def create_key(
    request: Request,
    body: ApiKeyCreate | None = None,
    user: dict[str, Any] = Depends(verify_supabase_jwt),
) -> dict[str, Any]:
    """Issue a new VERDANT API key. The raw key is returned exactly once."""
    label = body.label if body else None
    return await _issue_key(request, user, label)


@router.post("/keys/regenerate")
async def regenerate_key(
    request: Request,
    body: ApiKeyCreate | None = None,
    user: dict[str, Any] = Depends(verify_supabase_jwt),
) -> dict[str, Any]:
    """Revoke the caller's existing keys and issue a fresh one (returned once)."""
    db = request.app.state.db
    await db.revoke_api_keys_for_user(user["user_id"])
    label = body.label if body else None
    return await _issue_key(request, user, label)
