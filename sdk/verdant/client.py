from __future__ import annotations

from typing import Any, Callable

import httpx

from .config import Settings, get_settings
from .models import ContextType, WrapResult
from .pipeline import VerdantPipeline


class VerdantClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        settings: Settings | None = None,
        pipeline: VerdantPipeline | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        updates: dict[str, Any] = {}
        if api_key:
            updates["verdant_api_key"] = api_key
        if base_url:
            updates["verdant_api_url"] = base_url
        if updates:
            self.settings = self.settings.model_copy(update=updates)
        self.pipeline = pipeline or VerdantPipeline(self.settings)

    @property
    def _is_hosted(self) -> bool:
        """Use the hosted API when both a base URL and a VERDANT key are configured."""
        return bool(self.settings.verdant_api_url and self.settings.verdant_api_key)

    async def wrap(
        self,
        fn: Callable[..., Any],
        *,
        context_type: str | ContextType | None = None,
        input_text: str | None = None,
        metadata: dict[str, Any] | None = None,
        **fn_kwargs: Any,
    ) -> WrapResult:
        """Wrap a local model call and run the reasoning pipeline in-process."""
        return await self.pipeline.run(
            fn=fn,
            context_type=context_type,
            input_text=input_text,
            fn_kwargs=fn_kwargs,
            metadata=metadata,
        )

    async def run(
        self,
        *,
        context_type: str | ContextType,
        input_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> WrapResult:
        """Run the reasoning pipeline for the given input.

        In hosted mode (a ``verdant_api_url`` and ``verdant_api_key`` are set) this calls
        the VERDANT API over HTTP, so provider (Claude/Gemini) keys stay server-side. Otherwise
        it runs the pipeline in-process.
        """
        if self._is_hosted:
            return await self._run_hosted(context_type=context_type, input_text=input_text, metadata=metadata)
        return await self.pipeline.run(
            context_type=context_type,
            input_text=input_text,
            metadata=metadata,
        )

    async def _run_hosted(
        self,
        *,
        context_type: str | ContextType,
        input_text: str,
        metadata: dict[str, Any] | None,
    ) -> WrapResult:
        url = self.settings.verdant_api_url.rstrip("/") + "/pipeline/run"
        context_value = context_type.value if isinstance(context_type, ContextType) else str(context_type)
        payload = {
            "context_type": context_value,
            "input_text": input_text,
            "metadata": metadata or {},
        }
        headers = {"Authorization": f"Bearer {self.settings.verdant_api_key}"}

        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.post(url, json=payload, headers=headers)

        try:
            body = response.json()
        except ValueError:
            body = None

        if response.status_code >= 400:
            message = None
            if isinstance(body, dict) and body.get("error"):
                message = body["error"].get("message")
            raise VerdantAPIError(message or f"VERDANT API returned {response.status_code}", status_code=response.status_code)

        if not isinstance(body, dict) or body.get("data") is None:
            raise VerdantAPIError("VERDANT API returned an unexpected response.", status_code=response.status_code)

        return WrapResult.model_validate(body["data"])


class VerdantAPIError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
