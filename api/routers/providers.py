from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(tags=["providers"])


def _envelope(data: Any = None, meta: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "error": error}


class ProviderKeyUpdate(BaseModel):
    provider: str
    api_key: str


@router.get("/providers/keys")
async def get_provider_keys_status(request: Request) -> dict[str, Any]:
    """Return which providers have keys configured (without exposing the keys)."""
    db = request.app.state.db
    status_map = await db.get_all_provider_keys_status()
    return _envelope(data=status_map)


@router.post("/providers/keys")
async def set_provider_key(request: Request, body: ProviderKeyUpdate) -> dict[str, Any]:
    """Save or update a provider API key."""
    allowed = {"anthropic", "gemini"}
    if body.provider not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider '{body.provider}'. Must be one of: {', '.join(sorted(allowed))}.",
        )

    db = request.app.state.db
    await db.set_provider_key(body.provider, body.api_key)

    # Reset the cached LLM service client so it picks up the new key on next call
    if body.provider == "anthropic" and hasattr(request.app.state, "claude"):
        request.app.state.claude._client = None
    elif body.provider == "gemini" and hasattr(request.app.state, "gemini"):
        request.app.state.gemini._client = None

    return _envelope(
        data={"provider": body.provider, "configured": bool(body.api_key)},
        meta={"message": f"{body.provider} API key updated successfully."},
    )
