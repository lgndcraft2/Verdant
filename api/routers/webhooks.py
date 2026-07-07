from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, status

from sdk.verdant.models import AuditPayload

router = APIRouter(tags=["webhooks"])


def _envelope(data: Any = None, meta: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "error": error}


def _sign_payload(secret: str, payload: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def dispatch_low_trust_webhooks(app, audit: AuditPayload | dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    settings = app.state.settings
    db = app.state.db
    audit_payload = audit.model_dump(mode="json") if isinstance(audit, AuditPayload) else audit
    trust_score = int(audit_payload.get("trust_score", 0))

    webhook_configs = await db.fetch_webhook_configs(active_only=True)
    if not webhook_configs:
        return {"sent": 0, "failed": 0, "skipped": 0, "reason": "no_webhooks_configured"}

    if not force and trust_score >= settings.trust_score_alert_threshold:
        return {"sent": 0, "failed": 0, "skipped": len(webhook_configs), "reason": "threshold_not_met"}

    payload = {
        "event": "verdant.audit.low_trust",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit": audit_payload,
    }
    payload_bytes = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")

    sent = 0
    failed = 0
    async with httpx.AsyncClient(timeout=settings.webhook_timeout_seconds) as client:
        for config in webhook_configs:
            threshold = int(config.get("min_trust_score", settings.trust_score_alert_threshold))
            if not force and trust_score >= threshold:
                continue

            headers = {
                "Content-Type": "application/json",
                "X-Verdant-Event": "verdant.audit.low_trust",
                "X-Verdant-Timestamp": payload["timestamp"],
                "X-Verdant-Audit-Id": str(audit_payload.get("audit_id") or audit_payload.get("id") or ""),
            }
            secret = config.get("secret") or settings.webhook_secret
            if secret:
                headers["X-Verdant-Signature"] = _sign_payload(secret, payload_bytes)

            try:
                response = await client.post(config["url"], content=payload_bytes, headers=headers)
                response.raise_for_status()
                sent += 1
            except Exception:
                failed += 1

    return {"sent": sent, "failed": failed, "skipped": max(0, len(webhook_configs) - sent - failed)}


@router.post("/webhooks/dispatch")
async def dispatch_webhooks(request: Request, audit_id: str | None = None, force: bool = False) -> dict[str, Any]:
    if not audit_id and not force:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="audit_id is required unless force=true")

    db = request.app.state.db
    audit = None
    if audit_id:
        audit = await db.get_audit(audit_id)
        if not audit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")

    result = await dispatch_low_trust_webhooks(request.app, audit or {}, force=force)
    return _envelope(data=result, meta={"audit_id": audit_id, "force": force})
