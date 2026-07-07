from __future__ import annotations

import json
import logging
import re
from typing import Any

from api.services.claude_service import ClaudeService
from api.services.gemini_service import GeminiService

from ..config import Settings, get_settings
from ..models import ContextType, IntentStageOutput

logger = logging.getLogger(__name__)

_HINT_KEYWORDS: dict[ContextType, set[str]] = {
    ContextType.hiring: {"hire", "hiring", "candidate", "candidate", "interview", "resume", "cv", "recruit", "job"},
    ContextType.lending: {"loan", "credit", "borrow", "borrower", "repayment", "interest", "default", "underwrite", "lending"},
    ContextType.content: {"content", "moderation", "moderate", "policy", "hate", "spam", "post", "comment", "remove", "block"},
    ContextType.healthcare: {"health", "medical", "patient", "doctor", "clinic", "diagnosis", "treatment", "triage"},
}


def _extract_entities(text: str) -> list[str]:
    candidates = re.findall(r"\b[A-Z][a-zA-Z0-9&-]{2,}\b", text)
    tokens = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
    return list(dict.fromkeys(candidates + tokens))


def _detect_context(text: str) -> tuple[ContextType, list[str], float, bool]:
    lowered = text.lower()
    scores: dict[ContextType, int] = {}
    signals: list[str] = []

    for context_type, keywords in _HINT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        scores[context_type] = score
        if score:
            signals.append(f"{context_type.value}:{score}")

    best_context = max(scores, key=scores.get) if any(scores.values()) else ContextType.content
    top_score = scores.get(best_context, 0)
    ambiguous = list(scores.values()).count(top_score) > 1 if top_score else True
    confidence = min(1.0, 0.45 + (top_score * 0.15))
    if ambiguous:
        confidence = max(0.35, confidence - 0.15)
    needs_review = ambiguous or confidence < 0.6
    return best_context, signals, confidence, needs_review


def _heuristic_intent(input_text: str, context_hint: ContextType | None) -> IntentStageOutput:
    inferred_context, signals, confidence, needs_review = _detect_context(input_text)
    context_type = context_hint or inferred_context
    lower = input_text.lower()

    if context_type == ContextType.hiring:
        detected_intent = "screen_candidates"
        summary = "The request appears to evaluate or rank candidates for a job decision."
    elif context_type == ContextType.lending:
        detected_intent = "assess_credit_risk"
        summary = "The request appears to estimate repayment or lending eligibility."
    elif context_type == ContextType.healthcare:
        detected_intent = "support_clinical_decision"
        summary = "The request appears to support a healthcare decision or triage task."
    else:
        detected_intent = "moderate_content"
        summary = "The request appears to assess, classify, or moderate user-generated content."

    if "review" in lower or "check" in lower:
        signals.append("review_request")
    if "reject" in lower or "deny" in lower:
        signals.append("exclusion_signal")
    if "score" in lower or "rank" in lower:
        signals.append("ranking_signal")

    return IntentStageOutput(
        detected_intent=detected_intent,
        context_type=context_type,
        user_intent_summary=summary,
        entities=_extract_entities(input_text),
        signals=signals,
        confidence=confidence,
        needs_review=needs_review,
    )


async def extract_intent(
    input_text: str,
    *,
    context_type: str | ContextType | None = None,
    settings: Settings | None = None,
    claude_service: ClaudeService | None = None,
    gemini_service: GeminiService | None = None,
) -> IntentStageOutput:
    settings = settings or get_settings()
    context_hint = ContextType.normalize(context_type) if context_type else None
    claude_service = claude_service or ClaudeService(settings)
    gemini_service = gemini_service or GeminiService(settings)

    user_prompt = (
        "Analyze the following AI request and return JSON only.\n\n"
        f"Provided context type: {context_hint.value if context_hint else 'unknown'}\n"
        f"Input text:\n{input_text}\n"
    )

    try:
        result = await claude_service.generate_json("intent", user_prompt, IntentStageOutput)
        if context_hint and result.context_type != context_hint:
            result = result.model_copy(update={"context_type": context_hint})
        return result
    except Exception as exc:
        logger.warning("Claude intent extraction failed, falling back to Gemini/heuristics: %s", exc)

    try:
        result = await gemini_service.generate_json("intent", user_prompt, IntentStageOutput)
        if context_hint and result.context_type != context_hint:
            result = result.model_copy(update={"context_type": context_hint})
        return result
    except Exception as exc:
        logger.warning("Gemini intent extraction failed, using heuristics: %s", exc)
        return _heuristic_intent(input_text, context_hint)
