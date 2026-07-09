from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from sdk.verdant.config import Settings, get_settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# Avoid circular import — type-check only
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from api.services.db_service import DBService


class _GeneratedCompletion(BaseModel):
    output: str
    confidence: float = 0.5


class ClaudeService:
    model_name = "claude-sonnet-4-6"

    def __init__(self, settings: Settings | None = None, *, db_service: "DBService | None" = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        self._db_service = db_service
        self._prompts_dir = Path(__file__).resolve().parent / "prompts"

        if self.settings.anthropic_api_key:
            try:
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
            except Exception as exc:  # pragma: no cover - import/runtime guard
                logger.warning("Anthropic client unavailable: %s", exc)

    async def _ensure_client(self) -> None:
        """Lazily configure the Anthropic client from DB-stored keys if not already set."""
        if self._client is not None:
            return
        if self._db_service is None:
            return
        try:
            key = await self._db_service.get_provider_key("anthropic")
            if key:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=key)
                logger.info("Anthropic client initialized from DB-stored provider key.")
        except Exception as exc:
            logger.warning("Failed to initialize Anthropic client from DB key: %s", exc)

    def _load_prompt(self, prompt_name: str) -> str:
        prompt_path = self._prompts_dir / f"{prompt_name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def _extract_text(self, response: Any) -> str:
        if response is None:
            return ""
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            for key in ("output", "text", "content"):
                value = response.get(key)
                if isinstance(value, str):
                    return value
            return json.dumps(response, ensure_ascii=False, default=str)

        content = getattr(response, "content", None)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                text = getattr(item, "text", None)
                if isinstance(text, str):
                    parts.append(text)
                elif isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            if parts:
                return "".join(parts)

        for attr in ("output_text", "text"):
            value = getattr(response, attr, None)
            if isinstance(value, str):
                return value

        return str(response)

    def _clean_json_text(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
        return cleaned

    def _parse_json(self, text: str) -> dict[str, Any]:
        cleaned = self._clean_json_text(text)
        payload = json.loads(cleaned)
        if not isinstance(payload, dict):
            raise ValueError("Claude response did not contain a JSON object")
        return payload

    async def _invoke(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        await self._ensure_client()
        if self._client is None:
            raise RuntimeError("Anthropic client is not configured. Set ANTHROPIC_API_KEY or add it via the Dashboard.")

        response = await self._client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return self._extract_text(response)

    async def generate_json(
        self,
        prompt_name: str,
        user_prompt: str,
        response_model: type[T],
        *,
        temperature: float = 0.0,
    ) -> T:
        system_prompt = self._load_prompt(prompt_name)
        raw_text = await self._invoke(system_prompt, user_prompt, temperature=temperature)
        payload = self._parse_json(raw_text)
        return response_model.model_validate(payload)

    async def generate_text(
        self,
        prompt_name: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
    ) -> str:
        completion = await self.generate_json(
            prompt_name,
            user_prompt,
            _GeneratedCompletion,
            temperature=temperature,
        )
        return completion.output
