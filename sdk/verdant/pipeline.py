from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from typing import Any, Callable

from .config import Settings, get_settings
from .models import (
    AuditPayload,
    BaselineStageOutput,
    BiasStageOutput,
    ContextType,
    ExplainStageOutput,
    IntentStageOutput,
    PipelineStageOutputs,
    RiskLevel,
    TrustStageOutput,
    WrapResult,
)
from .services.cache_service import CacheService
from .services.claude_service import ClaudeService
from .services.db_service import DBService
from .services.gemini_service import GeminiService
from .stages.baseline import load_baseline
from .stages.bias import match_bias_patterns
from .stages.explain import generate_explanation
from .stages.intent import extract_intent
from .stages.trust import synthesize_trust_score

logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in value]
    return str(value)


def _stringify_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("output"), str):
            return value["output"]
        if "choices" in value:
            choices = value.get("choices") or []
            if choices:
                first = choices[0]
                message = first.get("message") if isinstance(first, dict) else getattr(first, "message", None)
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"]
                if hasattr(message, "content"):
                    content = getattr(message, "content")
                    if isinstance(content, str):
                        return content
        return json.dumps(value, ensure_ascii=False, default=str)
    for attr in ("output_text", "text"):
        attr_value = getattr(value, attr, None)
        if isinstance(attr_value, str):
            return attr_value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, dict):
            return _stringify_output(dumped)
    return str(value)


def _derive_input_text(fn_kwargs: dict[str, Any]) -> str:
    for key in ("input_text", "prompt", "content", "text", "message"):
        value = fn_kwargs.get(key)
        if isinstance(value, str) and value.strip():
            return value
    messages = fn_kwargs.get("messages")
    if isinstance(messages, list) and messages:
        parts: list[str] = []
        for message in messages:
            if isinstance(message, dict):
                role = message.get("role", "user")
                content = message.get("content", "")
            else:
                role = getattr(message, "role", "user")
                content = getattr(message, "content", "")
            parts.append(f"{role}: {content}")
        if parts:
            return "\n".join(parts)
    return json.dumps(_json_safe(fn_kwargs), ensure_ascii=False, default=str)


async def _call_target(fn: Callable[..., Any], fn_kwargs: dict[str, Any]) -> Any:
    result = fn(**fn_kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class VerdantPipeline:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        claude_service: ClaudeService | None = None,
        gemini_service: GeminiService | None = None,
        cache_service: CacheService | None = None,
        db_service: DBService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.claude_service = claude_service or ClaudeService(self.settings)
        self.gemini_service = gemini_service or GeminiService(self.settings)
        self.cache_service = cache_service or CacheService(self.settings)
        self.db_service = db_service or DBService(self.settings)

    async def _generate_default_output(
        self,
        input_text: str,
        intent: IntentStageOutput,
        baseline: BaselineStageOutput,
        metadata: dict[str, Any],
    ) -> str:
        prompt = (
            "Respond helpfully to the user's request and return JSON only.\n\n"
            f"Context type: {intent.context_type.value}\n"
            f"Intent summary: {intent.user_intent_summary}\n"
            f"Baseline summary: {baseline.baseline_summary}\n"
            f"Input text:\n{input_text}\n\n"
            f"Metadata:\n{json.dumps(_json_safe(metadata), ensure_ascii=False, default=str)}\n"
        )

        try:
            return await self.claude_service.generate_text("generate", prompt)
        except Exception as exc:
            logger.warning("Default output generation failed, using input echo fallback: %s", exc)
            return input_text

    async def run(
        self,
        fn: Callable[..., Any] | None = None,
        *,
        context_type: str | ContextType | None = None,
        input_text: str | None = None,
        fn_kwargs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WrapResult:
        started_at = time.perf_counter()
        metadata = metadata or {}
        fn_kwargs = dict(fn_kwargs or {})
        resolved_input_text = input_text or _derive_input_text(fn_kwargs)

        intent = await extract_intent(
            resolved_input_text,
            context_type=context_type,
            settings=self.settings,
            claude_service=self.claude_service,
            gemini_service=self.gemini_service,
        )

        baseline_context = ContextType.normalize(context_type) if context_type else intent.context_type
        baseline = await load_baseline(
            baseline_context,
            settings=self.settings,
            db_service=self.db_service,
            cache_service=self.cache_service,
        )

        pipeline_error: str | None = None

        if fn is None:
            try:
                raw_output: Any = await self._generate_default_output(resolved_input_text, intent, baseline, metadata)
                clean_output: Any = raw_output
            except Exception as exc:  # pragma: no cover - catch-all guard
                logger.exception("Default generation failed unexpectedly: %s", exc)
                raw_output = {"error": str(exc)}
                clean_output = ""
                pipeline_error = str(exc)
        else:
            try:
                raw_output = await _call_target(fn, fn_kwargs)
                clean_output = _json_safe(raw_output)
            except Exception as exc:
                logger.warning("Wrapped function raised; continuing with fallback output: %s", exc)
                raw_output = {"error": str(exc)}
                clean_output = ""
                pipeline_error = str(exc)

        output_text = _stringify_output(clean_output)
        bias = await match_bias_patterns(
            resolved_input_text,
            output_text,
            intent=intent,
            baseline=baseline,
        )
        explanation = await generate_explanation(
            resolved_input_text,
            output_text,
            intent=intent,
            baseline=baseline,
            bias=bias,
            settings=self.settings,
            claude_service=self.claude_service,
            gemini_service=self.gemini_service,
        )
        trust = await synthesize_trust_score(
            intent=intent,
            baseline=baseline,
            bias=bias,
            explanation=explanation,
            settings=self.settings,
            db_service=self.db_service,
        )

        if pipeline_error:
            explanation = explanation.model_copy(
                update={
                    "plain_language_explanation": (
                        f"{explanation.plain_language_explanation} "
                        f"The wrapped AI call failed: {pipeline_error}."
                    ).strip(),
                    "caveats": explanation.caveats + ["No valid upstream output was produced."],
                }
            )
            trust = trust.model_copy(
                update={
                    "trust_score": min(trust.trust_score, 15),
                    "risk_level": RiskLevel.critical,
                    "alerts": list(dict.fromkeys(trust.alerts + ["Wrapped function call failed"])),
                    "reasons": trust.reasons + [f"Upstream call failed: {pipeline_error}."],
                    "score_breakdown": {**trust.score_breakdown, "upstream_call_failed": 0.0},
                }
            )

        stages = PipelineStageOutputs(
            intent=intent,
            baseline=baseline,
            bias=bias,
            explanation=explanation,
            trust=trust,
        )

        audit = AuditPayload(
            context_type=ContextType.normalize(intent.context_type),
            input_text=resolved_input_text,
            output_text=output_text,
            raw_output=_json_safe(raw_output),
            clean_output=_json_safe(clean_output),
            stages=stages,
            trust_score=trust.trust_score,
            flags=list(bias.flags),
            explanation=explanation.plain_language_explanation,
            metadata=_json_safe(metadata),
            model_name=self.settings.claude_model,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            error=raw_output.get("error") if isinstance(raw_output, dict) else None,
        )

        return WrapResult(
            output=clean_output,
            audit=audit,
            trust_score=trust.trust_score,
            flags=list(bias.flags),
            explanation=explanation.plain_language_explanation,
        )
