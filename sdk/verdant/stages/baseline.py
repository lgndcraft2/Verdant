from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

from api.services.cache_service import CacheService
from api.services.db_service import DBService

from ..config import Settings, get_settings
from ..models import BaselineStageOutput, ContextType

logger = logging.getLogger(__name__)

DEFAULT_BASELINES: dict[ContextType, dict[str, Any]] = {
    ContextType.hiring: {
        "baseline_name": "Nigerian Hiring Baseline",
        "baseline_version": "2026.07.01",
        "demographic_focus": ["Yoruba", "Igbo", "Hausa", "minority ethnic groups", "urban-rural parity", "gender balance"],
        "baseline_summary": "Use hiring signals that reflect role fit and verified capability, not tribe, accent, religion, or school prestige alone.",
        "policy_notes": [
            "Avoid proxy discrimination through name, origin, or language register.",
            "Account for regional access to education and work experience.",
            "Flag overconfident ranking based on informal cues.",
        ],
        "baseline_data": {
            "context": "hiring",
            "risk_focus": ["proxy discrimination", "accent bias", "gendered screening"],
            "recommended_review": ["qualification evidence", "role-specific experience", "local labor market context"],
        },
        "source": "fallback",
        "confidence": 0.65,
    },
    ContextType.lending: {
        "baseline_name": "Nigerian Lending Baseline",
        "baseline_version": "2026.07.01",
        "demographic_focus": ["financial inclusion", "informal income earners", "SMEs", "rural borrowers", "gender access"],
        "baseline_summary": "Use repayment and affordability signals that recognize informal income, uneven banking access, and regional economic disparity.",
        "policy_notes": [
            "Do not treat lack of formal credit history as proof of default risk.",
            "Prefer cashflow and transaction evidence where available.",
            "Flag decisions that ignore mobile-money and cooperative savings patterns.",
        ],
        "baseline_data": {
            "context": "lending",
            "risk_focus": ["informal-income exclusion", "thin-file bias", "regional disparity"],
            "recommended_review": ["cashflow evidence", "repayment ability", "alternative credit indicators"],
        },
        "source": "fallback",
        "confidence": 0.65,
    },
    ContextType.content: {
        "baseline_name": "Nigerian Content Moderation Baseline",
        "baseline_version": "2026.07.01",
        "demographic_focus": ["multilingual code-switching", "political speech nuance", "religious sensitivity", "youth slang", "local dialects"],
        "baseline_summary": "Distinguish harm from ordinary Nigerian multilingual expression, satire, and context-dependent references.",
        "policy_notes": [
            "Avoid over-penalizing local slang or code-switching.",
            "Treat direct threats and hate speech as high risk.",
            "Consider whether a phrase is quoted, reclaimed, or targeted.",
        ],
        "baseline_data": {
            "context": "content moderation",
            "risk_focus": ["language nuance", "context collapse", "political expression"],
            "recommended_review": ["speaker intent", "targeted harm", "cultural context"],
        },
        "source": "fallback",
        "confidence": 0.65,
    },
    ContextType.healthcare: {
        "baseline_name": "Nigerian Healthcare Baseline",
        "baseline_version": "2026.07.01",
        "demographic_focus": ["rural access", "maternal health", "language access", "cost sensitivity", "regional care gaps"],
        "baseline_summary": "Use clinically relevant signals while accounting for access disparities, language barriers, and the risk of overconfident triage.",
        "policy_notes": [
            "Do not substitute proxy social cues for clinical evidence.",
            "Surface uncertainty for human review when symptoms are ambiguous.",
            "Treat safety-critical decisions as high review priority.",
        ],
        "baseline_data": {
            "context": "healthcare",
            "risk_focus": ["access disparity", "triage risk", "language barrier"],
            "recommended_review": ["clinical evidence", "urgency", "need for human escalation"],
        },
        "source": "fallback",
        "confidence": 0.65,
    },
}


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return [str(value)]


def _build_output(context_type: ContextType, row: dict[str, Any] | None, source: str) -> BaselineStageOutput:
    baseline = deepcopy(DEFAULT_BASELINES[context_type])
    if row:
        baseline.update(
            {
                "baseline_name": row.get("baseline_name", baseline["baseline_name"]),
                "baseline_version": row.get("baseline_version", baseline["baseline_version"]),
                "demographic_focus": _coerce_list(row.get("demographic_focus", baseline["demographic_focus"])),
                "baseline_summary": row.get("baseline_summary", baseline["baseline_summary"]),
                "policy_notes": _coerce_list(row.get("policy_notes", baseline["policy_notes"])),
                "baseline_data": row.get("baseline_data", baseline["baseline_data"]),
                "source": row.get("source", source),
                "confidence": float(row.get("confidence", baseline["confidence"])),
            }
        )
    else:
        baseline["source"] = source

    return BaselineStageOutput(
        context_type=context_type,
        baseline_name=baseline["baseline_name"],
        baseline_version=baseline["baseline_version"],
        demographic_focus=list(baseline["demographic_focus"]),
        baseline_summary=baseline["baseline_summary"],
        policy_notes=list(baseline["policy_notes"]),
        baseline_data=dict(baseline["baseline_data"]),
        source=baseline["source"],
        confidence=float(baseline["confidence"]),
    )


async def load_baseline(
    context_type: str | ContextType,
    *,
    settings: Settings | None = None,
    db_service: DBService | None = None,
    cache_service: CacheService | None = None,
) -> BaselineStageOutput:
    settings = settings or get_settings()
    db_service = db_service or DBService(settings)
    cache_service = cache_service or CacheService(settings)
    normalized_context = ContextType.normalize(context_type)

    try:
        cached = await cache_service.get_baseline(normalized_context)
        if isinstance(cached, dict) and cached:
            return BaselineStageOutput.model_validate(
                {
                    "context_type": normalized_context.value,
                    "baseline_name": cached.get("baseline_name", DEFAULT_BASELINES[normalized_context]["baseline_name"]),
                    "baseline_version": cached.get("baseline_version", DEFAULT_BASELINES[normalized_context]["baseline_version"]),
                    "demographic_focus": cached.get("demographic_focus", []),
                    "baseline_summary": cached.get("baseline_summary", DEFAULT_BASELINES[normalized_context]["baseline_summary"]),
                    "policy_notes": cached.get("policy_notes", []),
                    "baseline_data": cached.get("baseline_data", {}),
                    "source": cached.get("source", "cache"),
                    "confidence": cached.get("confidence", 0.7),
                }
            )
    except Exception as exc:
        logger.warning("Baseline cache lookup failed: %s", exc)

    row = None
    try:
        row = await db_service.fetch_baseline(normalized_context)
    except Exception as exc:
        logger.warning("Baseline DB lookup failed, using fallback baseline: %s", exc)

    output = _build_output(normalized_context, row, source="supabase" if row else "fallback")

    try:
        await cache_service.set_baseline(normalized_context, output.model_dump(mode="json"), ttl_seconds=3600)
    except Exception as exc:
        logger.warning("Failed to cache baseline: %s", exc)

    return output
