from __future__ import annotations

import logging
from typing import Any

from ..config import Settings, get_settings
from ..models import BaselineStageOutput, BiasStageOutput, ContextType, ExplainStageOutput, IntentStageOutput
from ..services.claude_service import ClaudeService
from ..services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


def _heuristic_explanation(
    input_text: str,
    output_text: str,
    *,
    intent: IntentStageOutput,
    baseline: BaselineStageOutput,
    bias: BiasStageOutput,
) -> ExplainStageOutput:
    if bias.flags:
        explanation = (
            f"The output may be risky because it matches {len(bias.flags)} bias signal(s) "
            f"against the {baseline.context_type.value} baseline."
        )
        caveats = [
            "A human reviewer should inspect the flagged logic before production use.",
            "The result may rely on proxy signals instead of task-relevant evidence.",
        ]
    else:
        explanation = (
            f"The output aligns with the {baseline.context_type.value} baseline and does not show a clear bias pattern."
        )
        caveats = [
            "This is a heuristic check; edge cases still need review in high-stakes contexts.",
        ]

    reasoning_summary = [
        f"Intent detected: {intent.detected_intent}.",
        f"Baseline source: {baseline.source} ({baseline.baseline_version}).",
        f"Bias severity: {bias.severity.value}.",
    ]

    confidence = max(0.4, min(0.95, (intent.confidence + baseline.confidence + bias.confidence) / 3))
    return ExplainStageOutput(
        plain_language_explanation=explanation,
        reasoning_summary=reasoning_summary,
        caveats=caveats,
        confidence=confidence,
    )


async def generate_explanation(
    input_text: str,
    output_text: str,
    *,
    intent: IntentStageOutput,
    baseline: BaselineStageOutput,
    bias: BiasStageOutput,
    settings: Settings | None = None,
    claude_service: ClaudeService | None = None,
    gemini_service: GeminiService | None = None,
) -> ExplainStageOutput:
    settings = settings or get_settings()
    claude_service = claude_service or ClaudeService(settings)
    gemini_service = gemini_service or GeminiService(settings)

    user_prompt = (
        "Generate a plain-language explanation from these stage outputs.\n\n"
        f"Input text:\n{input_text}\n\n"
        f"Output text:\n{output_text}\n\n"
        f"Intent JSON:\n{intent.model_dump_json(indent=2)}\n\n"
        f"Baseline JSON:\n{baseline.model_dump_json(indent=2)}\n\n"
        f"Bias JSON:\n{bias.model_dump_json(indent=2)}\n"
    )

    try:
        return await claude_service.generate_json("explain", user_prompt, ExplainStageOutput)
    except Exception as exc:
        logger.warning("Claude explanation generation failed, falling back to Gemini/heuristics: %s", exc)

    try:
        return await gemini_service.generate_json("explain", user_prompt, ExplainStageOutput)
    except Exception as exc:
        logger.warning("Gemini explanation generation failed, using heuristics: %s", exc)
        return _heuristic_explanation(input_text, output_text, intent=intent, baseline=baseline, bias=bias)
