from __future__ import annotations

from typing import Any, Callable

import httpx

from .config import Settings, get_settings
from .models import ContextType, WrapResult
from .pipeline import (
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
    """Client for the hosted VERDANT API.

    Authentication is by VERDANT API key only. Generate one in the dashboard
    (Settings -> API keys) and pass it as ``VerdantClient(api_key="vd_live_...")``
    or via the ``VERDANT_API_KEY`` environment variable. The API URL is baked in,
    so the key is all you need. Provider (Claude/Gemini) keys stay server-side and
    are managed in the dashboard.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        updates: dict[str, Any] = {}
        if api_key:
            updates["verdant_api_key"] = api_key
        if base_url:
            updates["verdant_api_url"] = base_url
        if updates:
            self.settings = self.settings.model_copy(update=updates)

    def _require_key(self) -> None:
        if not self.settings.verdant_api_key:
            raise VerdantAPIError(
                "VerdantClient requires an api_key. Generate one in the dashboard "
                "(Settings -> API keys) and pass VerdantClient(api_key='vd_live_...') "
                "or set VERDANT_API_KEY."
            )
        if not self.settings.verdant_api_url:
            raise VerdantAPIError("The VERDANT API URL is not configured.")

    async def wrap(
        self,
        fn: Callable[..., Any],
        *,
        context_type: str | ContextType | None = None,
        input_text: str | None = None,
        metadata: dict[str, Any] | None = None,
        **fn_kwargs: Any,
    ) -> WrapResult:
        """Run your model call locally, then analyse its output with VERDANT.

        ``fn`` runs on your machine (so you keep your own provider keys and any
        custom call logic); its output is sent to VERDANT for scoring. Anything
        after ``context_type``, ``input_text``, and ``metadata`` is forwarded to
        ``fn`` as keyword arguments.
        """
        self._require_key()

        # Call the model locally; keep the caller's output even if the call fails.
        try:
            raw_output: Any = await _call_target(fn, fn_kwargs)
            output_value = _json_safe(raw_output)
        except Exception as exc:  # keep the caller's app up
            raw_output = {"error": str(exc)}
            output_value = raw_output

        payload: dict[str, Any] = {
            "input_text": input_text or _derive_input_text(fn_kwargs),
            "output_text": _stringify_output(output_value),
            "metadata": metadata or {},
        }
        if context_type is not None:
            payload["context_type"] = _context_value(context_type)

        result = await self._post_pipeline("/pipeline/analyze", payload)
        # Hand back the caller's own output rather than the echoed text.
        return result.model_copy(update={"output": output_value})

    async def run(
        self,
        *,
        context_type: str | ContextType,
        input_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> WrapResult:
        """Run the full reasoning pipeline on VERDANT for the given input.

        VERDANT calls the model and runs every stage server-side, so no provider
        keys are needed in your app.
        """
        self._require_key()
        return await self._post_pipeline(
            "/pipeline/run",
            {
                "context_type": _context_value(context_type),
                "input_text": input_text,
                "metadata": metadata or {},
            },
        )

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
