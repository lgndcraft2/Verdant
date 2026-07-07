from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Request

from sdk.verdant.models import ContextType

router = APIRouter(tags=["reports"])


def _envelope(data: Any = None, meta: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "error": error}


def _parse_created_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


@router.get("/reports/ndpr")
async def ndpr_report(request: Request, days: int = 30) -> dict[str, Any]:
    db = request.app.state.db
    audits, total = await db.list_audits(limit=5000, offset=0)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered = [audit for audit in audits if _parse_created_at(audit.get("created_at")) >= cutoff]

    by_context = Counter()
    flag_counts = Counter()
    trust_scores: list[int] = []
    low_trust = 0
    for audit in filtered:
        context_value = audit.get("context_type", "unknown")
        by_context[context_value] += 1
        flags = audit.get("flags") or []
        flag_counts.update(flags)
        score = int(audit.get("trust_score", 0))
        trust_scores.append(score)
        if score < request.app.state.settings.trust_score_alert_threshold:
            low_trust += 1

    avg_trust = round(sum(trust_scores) / len(trust_scores), 2) if trust_scores else None
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": days,
        "total_audits": len(filtered),
        "available_audits": total,
        "low_trust_decisions": low_trust,
        "average_trust_score": avg_trust,
        "by_context_type": dict(by_context),
        "flag_counts": dict(flag_counts.most_common()),
        "compliance_notes": [
            "Audits are stored with full stage breakdowns for traceability.",
            "Low-trust outputs trigger webhook dispatch according to configured thresholds.",
            "Baselines are versioned and can be updated independently of the SDK.",
        ],
    }
    return _envelope(data=report, meta={"days": days})
