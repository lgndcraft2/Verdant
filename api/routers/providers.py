from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from api.auth import verify_session
from pydantic import BaseModel

router = APIRouter(tags=["providers"])


def _envelope(data: Any = None, meta: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "error": error}


class ProviderKeyUpdate(BaseModel):
    provider: str
    api_key: str


@router.get("/providers/keys")
async def get_provider_keys_status(request: Request, user: dict = Depends(verify_session)) -> dict[str, Any]:
    """Return this account's provider-key status without exposing the keys."""
    db = request.app.state.db
    status_map = await db.get_provider_keys_status(user["user_id"])
    return _envelope(data=status_map)


@router.post("/providers/keys")
async def set_provider_key(request: Request, body: ProviderKeyUpdate, user: dict = Depends(verify_session)) -> dict[str, Any]:
    """Save or update a provider API key for this account only."""
    allowed = {"anthropic", "gemini"}
    if body.provider not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider '{body.provider}'. Must be one of: {', '.join(sorted(allowed))}.",
        )

    db = request.app.state.db
    await db.set_provider_key(user["user_id"], body.provider, body.api_key)
    service = getattr(request.app.state, "claude" if body.provider == "anthropic" else "gemini", None)
    if service and hasattr(service, "clear_account_client"):
        service.clear_account_client(user["user_id"])

    return _envelope(
        data={"provider": body.provider, "configured": bool(body.api_key)},
        meta={"message": f"{body.provider} API key updated successfully."},
    )
