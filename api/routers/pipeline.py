from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from api.routers.webhooks import dispatch_low_trust_webhooks
from sdk.verdant.models import PipelineAnalyzeRequest, PipelineRunRequest, WrapResult

router = APIRouter(tags=["pipeline"])


def _envelope(data: Any = None, meta: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "error": error}


async def _finalize(request: Request, result: WrapResult) -> dict[str, Any]:
    """Persist the audit, fire low-trust webhooks, and build the response envelope."""
    db = request.app.state.db
    settings = request.app.state.settings

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


@router.post("/pipeline/run")
async def run_pipeline(request: Request, body: PipelineRunRequest) -> dict[str, Any]:
    """Generate an output for the input and run the full reasoning pipeline."""
    pipeline = request.app.state.pipeline
    try:
        result = await pipeline.run(
            context_type=body.context_type,
            input_text=body.input_text,
            metadata=body.metadata,
        )
        return await _finalize(request, result)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/pipeline/analyze")
async def analyze_pipeline(request: Request, body: PipelineAnalyzeRequest) -> dict[str, Any]:
    """Run the reasoning stages on an output the caller already produced.

    Used by hybrid wrap: the model is called client-side, and the resulting
    output is analysed here with server-side (dashboard-managed) provider keys.
    """
    pipeline = request.app.state.pipeline
    try:
        result = await pipeline.run(
            context_type=body.context_type,
            input_text=body.input_text,
            precomputed_output=body.output_text,
            metadata=body.metadata,
        )
        return await _finalize(request, result)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
