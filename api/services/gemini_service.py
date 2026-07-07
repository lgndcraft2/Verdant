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


class GeminiService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        self._prompts_dir = Path(__file__).resolve().parent / "prompts"

        if self.settings.gemini_api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.settings.gemini_api_key)
                self._client = genai
            except Exception as exc:  # pragma: no cover - import/runtime guard
                logger.warning("Gemini client unavailable: %s", exc)

    def _load_prompt(self, prompt_name: str) -> str:
        prompt_path = self._prompts_dir / f"{prompt_name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

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
        payload = json.loads(self._clean_json_text(text))
        if not isinstance(payload, dict):
            raise ValueError("Gemini response did not contain a JSON object")
        return payload

    async def _invoke(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        if self._client is None:
            raise RuntimeError("Gemini client is not configured")

        def _run() -> str:
            model = self._client.GenerativeModel(
                model_name=self.settings.gemini_model,
                system_instruction=system_prompt,
            )
            response = model.generate_content(
                user_prompt,
                generation_config={"temperature": temperature},
            )
            if hasattr(response, "text") and isinstance(response.text, str):
                return response.text
            return str(response)

        return await asyncio.to_thread(_run)

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
        class _GeneratedCompletion(BaseModel):
            output: str
            confidence: float = 0.5

        completion = await self.generate_json(
            prompt_name,
            user_prompt,
            _GeneratedCompletion,
            temperature=temperature,
        )
        return completion.output

    async def cross_validate_json(
        self,
        prompt_name: str,
        user_prompt: str,
        response_model: type[T],
        *,
        temperature: float = 0.0,
    ) -> T:
        return await self.generate_json(
            prompt_name,
            user_prompt,
            response_model,
            temperature=temperature,
        )
