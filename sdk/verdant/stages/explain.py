from __future__ import annotations

import logging

from ..config import Settings, get_settings
from ..errors import ProviderUnavailableError
from ..models import BaselineStageOutput, BiasStageOutput, ExplainStageOutput, IntentStageOutput
from ..services.claude_service import ClaudeService
from ..services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


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
        logger.warning("Claude explanation generation failed, falling back to Gemini: %s", exc)

    try:
        return await gemini_service.generate_json("explain", user_prompt, ExplainStageOutput)
    except Exception as exc:
        logger.error("Gemini explanation generation failed and heuristic fallback is disabled: %s", exc)
        raise ProviderUnavailableError(
            "Explanation generation failed: no provider model is available. Configure an "
            "Anthropic or Gemini key in the dashboard (Settings -> Provider Keys)."
        ) from exc
