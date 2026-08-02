from __future__ import annotations

import logging

from ..config import Settings, get_settings
from ..errors import ProviderUnavailableError
from ..models import ContextType, IntentStageOutput
from ..services.claude_service import ClaudeService
from ..services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


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

    def _apply_hint(result: IntentStageOutput) -> IntentStageOutput:
        if context_hint and result.context_type != context_hint:
            return result.model_copy(update={"context_type": context_hint})
        return result

    try:
        return _apply_hint(await claude_service.generate_json("intent", user_prompt, IntentStageOutput))
    except Exception as exc:
        logger.warning("Claude intent extraction failed, falling back to Gemini: %s", exc)

    try:
        return _apply_hint(await gemini_service.generate_json("intent", user_prompt, IntentStageOutput))
    except Exception as exc:
        logger.error("Gemini intent extraction failed and heuristic fallback is disabled: %s", exc)
        raise ProviderUnavailableError(
            "Intent extraction failed: no provider model is available. Configure an "
            "Anthropic or Gemini key in the dashboard (Settings -> Provider Keys)."
        ) from exc
