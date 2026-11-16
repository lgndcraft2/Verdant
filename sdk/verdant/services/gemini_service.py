from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .db_service import DBService


class GeminiService:
    def __init__(self, settings: Settings | None = None, *, db_service: "DBService | None" = None) -> None:
        self.settings = settings or get_settings()
        self.model_name = self.settings.gemini_model
        self._client = None
        self._account_clients: dict[str, Any] = {}
        self._account_keys: dict[str, str] = {}
        self._request_lock = asyncio.Lock()
        self._db_service = db_service
        self._prompts_dir = Path(__file__).resolve().parent / "prompts"

        if self.settings.gemini_api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.settings.gemini_api_key)
                self._client = genai
            except Exception as exc:  # pragma: no cover - import/runtime guard
                logger.warning("Gemini client unavailable: %s", exc)

    async def _ensure_client(self, owner_id: str | None = None):
        """Resolve an account-specific Gemini client when a key is configured."""
        if owner_id is None:
            return self._client
        if owner_id in self._account_clients:
            return self._account_clients[owner_id]
        try:
            key = await self._db_service.get_provider_key("gemini", owner_id) if self._db_service else None
            if key:
                import google.generativeai as genai
                self._account_clients[owner_id] = genai
                self._account_keys[owner_id] = key
                return genai
        except Exception as exc:
            logger.warning("Failed to initialize Gemini client from DB key: %s", exc)
        return None if self._db_service else self._client

    def clear_account_client(self, owner_id: str) -> None:
        self._account_clients.pop(owner_id, None)
        self._account_keys.pop(owner_id, None)

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

    async def _invoke(self, system_prompt: str, user_prompt: str, temperature: float = 0.0, owner_id: str | None = None) -> str:
        client = await self._ensure_client(owner_id)
        if client is None:
            raise RuntimeError("Gemini client is not configured. Set GEMINI_API_KEY or add it via the Dashboard.")

        def _run() -> str:
            model = client.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt,
            )
            response = model.generate_content(
                user_prompt,
                generation_config={"temperature": temperature},
            )
            if hasattr(response, "text") and isinstance(response.text, str):
                return response.text
            return str(response)

        async with self._request_lock:
            if owner_id is not None and owner_id in self._account_keys:
                client.configure(api_key=self._account_keys[owner_id])
            return await asyncio.to_thread(_run)

    async def generate_json(
        self,
        prompt_name: str,
        user_prompt: str,
        response_model: type[T],
        *,
        temperature: float = 0.0,
        owner_id: str | None = None,
    ) -> T:
        system_prompt = self._load_prompt(prompt_name)
        raw_text = await self._invoke(system_prompt, user_prompt, temperature=temperature, owner_id=owner_id)
        payload = self._parse_json(raw_text)
        return response_model.model_validate(payload)

    async def generate_text(
        self,
        prompt_name: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        owner_id: str | None = None,
    ) -> str:
        class _GeneratedCompletion(BaseModel):
            output: str
            confidence: float = 0.5

        completion = await self.generate_json(
            prompt_name,
            user_prompt,
            _GeneratedCompletion,
            temperature=temperature,
            owner_id=owner_id,
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
