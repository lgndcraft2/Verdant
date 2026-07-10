from __future__ import annotations

import statistics
from typing import Any

from ..config import Settings, get_settings
from ..models import (
    BaselineStageOutput,
    BiasSeverity,
    BiasStageOutput,
    ContextType,
    ExplainStageOutput,
    IntentStageOutput,
    RiskLevel,
    TrustStageOutput,
)
from ..services.db_service import DBService


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _risk_level_from_score(score: int) -> RiskLevel:
    if score >= 80:
        return RiskLevel.low
    if score >= 60:
        return RiskLevel.medium
    if score >= 40:
        return RiskLevel.high
    return RiskLevel.critical


def _historical_consistency(current_bias_strength: float, audits: list[dict[str, Any]]) -> float:
    if not audits:
        return 75.0

    prior_scores = [float(item.get("trust_score", 0)) for item in audits if item.get("trust_score") is not None]
    prior_flag_counts = [len(item.get("flags", []) or []) for item in audits]

    if not prior_scores:
        return 75.0

    mean_score = statistics.mean(prior_scores)
    mean_flag_count = statistics.mean(prior_flag_counts) if prior_flag_counts else 0.0
    consistency = 100.0 - abs(mean_score - current_bias_strength) - (mean_flag_count * 2.0)
    return _clamp(consistency)


async def synthesize_trust_score(
    *,
    intent: IntentStageOutput,
    baseline: BaselineStageOutput,
    bias: BiasStageOutput,
    explanation: ExplainStageOutput,
    settings: Settings | None = None,
    db_service: DBService | None = None,
) -> TrustStageOutput:
    settings = settings or get_settings()
    db_service = db_service or DBService(settings)

    bias_signal_strength = _clamp(100.0 - float(bias.bias_score))
    explanation_confidence = _clamp(explanation.confidence * 100.0)
    intent_alignment = _clamp(((intent.confidence + baseline.confidence) / 2.0) * 100.0)
    if intent.needs_review:
        intent_alignment = _clamp(intent_alignment - 15.0)
    if intent.context_type != baseline.context_type:
        intent_alignment = _clamp(intent_alignment - 10.0)

    historical_audits = []
    try:
        historical_audits = await db_service.fetch_recent_audits(intent.context_type, limit=20)
    except Exception:
        historical_audits = []
    historical_pattern_consistency = _historical_consistency(bias_signal_strength, historical_audits)

    trust_score = round(
        (0.40 * bias_signal_strength)
        + (0.30 * explanation_confidence)
        + (0.20 * intent_alignment)
        + (0.10 * historical_pattern_consistency)
    )
    trust_score = max(0, min(100, trust_score))

    alerts: list[str] = []
    if trust_score < settings.trust_score_alert_threshold:
        alerts.append("Trust score below alert threshold")
    if bias.severity in {BiasSeverity.high, BiasSeverity.critical}:
        alerts.append(f"Bias severity is {bias.severity.value}")
    if intent.needs_review:
        alerts.append("Intent requires human review")

    reasons = [
        f"Bias signal strength: {bias_signal_strength:.1f}/100.",
        f"Explanation confidence: {explanation_confidence:.1f}/100.",
        f"Intent alignment: {intent_alignment:.1f}/100.",
        f"Historical pattern consistency: {historical_pattern_consistency:.1f}/100.",
    ]

    confidence = (intent.confidence + baseline.confidence + bias.confidence + explanation.confidence) / 4.0

    return TrustStageOutput(
        trust_score=trust_score,
        risk_level=_risk_level_from_score(trust_score),
        score_breakdown={
            "bias_signal_strength": bias_signal_strength,
            "explanation_confidence": explanation_confidence,
            "intent_alignment": intent_alignment,
            "historical_pattern_consistency": historical_pattern_consistency,
        },
        reasons=reasons,
        alerts=alerts,
        confidence=max(0.0, min(1.0, confidence)),
    )
