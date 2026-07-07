from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from api.routers.webhooks import dispatch_low_trust_webhooks
from sdk.verdant.models import PipelineRunRequest

router = APIRouter(tags=["pipeline"])


def _envelope(data: Any = None, meta: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "error": error}


@router.post("/pipeline/run")
async def run_pipeline(request: Request, body: PipelineRunRequest) -> dict[str, Any]:
    pipeline = request.app.state.pipeline
    db = request.app.state.db
    settings = request.app.state.settings

    try:
        result = await pipeline.run(
            context_type=body.context_type,
            input_text=body.input_text,
            metadata=body.metadata,
        )
        stored_audit = await db.insert_audit_log(result.audit)
        audit_id = stored_audit.get("id") or stored_audit.get("audit_id")
        if audit_id:
            result = result.model_copy(update={"audit": result.audit.model_copy(update={"audit_id": audit_id})})

        webhook_result = None
        if result.trust_score < settings.trust_score_alert_threshold:
            webhook_result = await dispatch_low_trust_webhooks(request.app, result.audit)

        meta = {
            "audit_id": str(audit_id) if audit_id else None,
            "trust_score": result.trust_score,
            "webhook_dispatched": bool(webhook_result and webhook_result.get("sent", 0)),
        }
        return _envelope(data=result.model_dump(mode="json"), meta=meta)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
