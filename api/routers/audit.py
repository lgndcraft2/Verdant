from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from sdk.verdant.models import ContextType

router = APIRouter(tags=["audits"])


def _envelope(data: Any = None, meta: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "error": error}


@router.get("/audits")
async def list_audits(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    context_type: str | None = None,
) -> dict[str, Any]:
    db = request.app.state.db
    try:
        normalized = ContextType.normalize(context_type) if context_type else None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    records, total = await db.list_audits(limit=limit, offset=offset, context_type=normalized)
    return _envelope(
        data={"items": records, "total": total},
        meta={"limit": limit, "offset": offset, "context_type": normalized.value if normalized else None},
    )


@router.get("/audits/{audit_id}")
async def get_audit(request: Request, audit_id: str) -> dict[str, Any]:
    db = request.app.state.db
    record = await db.get_audit(audit_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    return _envelope(data=record, meta={"audit_id": audit_id})
