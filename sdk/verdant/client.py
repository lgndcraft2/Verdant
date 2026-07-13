from __future__ import annotations

from typing import Any, Callable

import httpx

from .config import Settings, get_settings
from .models import ContextType, WrapResult
from .pipeline import (
    VerdantPipeline,
    _call_target,
    _derive_input_text,
    _json_safe,
    _stringify_output,
)


class VerdantAPIError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


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
        remote_analysis: bool = False,
        **fn_kwargs: Any,
    ) -> WrapResult:
        """Wrap a model call and run the reasoning pipeline on its output.

        By default the whole pipeline runs in-process (provider keys must be set
        locally). With ``remote_analysis=True`` the wrapped ``fn`` still runs
        locally, but the analysis stages run on the hosted API using its
        dashboard-managed provider keys — so no local provider keys are needed.
        Requires ``base_url``/``VERDANT_API_URL`` and an ``api_key``.
        """
        if remote_analysis:
            return await self._wrap_remote(
                fn,
                context_type=context_type,
                input_text=input_text,
                metadata=metadata,
                fn_kwargs=fn_kwargs,
            )
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
            return await self._post_pipeline(
                "/pipeline/run",
                {
                    "context_type": _context_value(context_type),
                    "input_text": input_text,
                    "metadata": metadata or {},
                },
            )
        return await self.pipeline.run(
            context_type=context_type,
            input_text=input_text,
            metadata=metadata,
        )

    async def _wrap_remote(
        self,
        fn: Callable[..., Any],
        *,
        context_type: str | ContextType | None,
        input_text: str | None,
        metadata: dict[str, Any] | None,
        fn_kwargs: dict[str, Any],
    ) -> WrapResult:
        if not self._is_hosted:
            raise VerdantAPIError(
                "remote_analysis=True requires a hosted API: set base_url / VERDANT_API_URL "
                "and an api_key."
            )

        # Call the model locally; keep the wrapped output even if analysis is remote.
        try:
            raw_output: Any = await _call_target(fn, fn_kwargs)
            output_value = _json_safe(raw_output)
        except Exception as exc:  # keep the caller's app up, mirror in-process behaviour
            raw_output = {"error": str(exc)}
            output_value = raw_output

        resolved_input = input_text or _derive_input_text(fn_kwargs)
        payload: dict[str, Any] = {
            "input_text": resolved_input,
            "output_text": _stringify_output(output_value),
            "metadata": metadata or {},
        }
        if context_type is not None:
            payload["context_type"] = _context_value(context_type)

        result = await self._post_pipeline("/pipeline/analyze", payload)
        # Hand back the caller's own output rather than the echoed text.
        return result.model_copy(update={"output": output_value})

    async def _post_pipeline(self, path: str, payload: dict[str, Any]) -> WrapResult:
        url = self.settings.verdant_api_url.rstrip("/") + path
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
            raise VerdantAPIError(
                message or f"VERDANT API returned {response.status_code}",
                status_code=response.status_code,
            )

        if not isinstance(body, dict) or body.get("data") is None:
            raise VerdantAPIError(
                "VERDANT API returned an unexpected response.",
                status_code=response.status_code,
            )

        return WrapResult.model_validate(body["data"])


def _context_value(context_type: str | ContextType) -> str:
    return context_type.value if isinstance(context_type, ContextType) else str(context_type)
