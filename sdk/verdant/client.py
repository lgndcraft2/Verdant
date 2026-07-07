from __future__ import annotations

from typing import Any, Callable

from .config import Settings, get_settings
from .models import ContextType, WrapResult
from .pipeline import VerdantPipeline


class VerdantClient:
    def __init__(self, api_key: str | None = None, *, settings: Settings | None = None, pipeline: VerdantPipeline | None = None) -> None:
        self.settings = settings or get_settings()
        if api_key:
            self.settings = self.settings.model_copy(update={"verdant_api_key": api_key})
        self.pipeline = pipeline or VerdantPipeline(self.settings)

    async def wrap(
        self,
        fn: Callable[..., Any],
        *,
        context_type: str | ContextType | None = None,
        input_text: str | None = None,
        metadata: dict[str, Any] | None = None,
        **fn_kwargs: Any,
    ) -> WrapResult:
        return await self.pipeline.run(
            fn=fn,
            context_type=context_type,
            input_text=input_text,
            fn_kwargs=fn_kwargs,
            metadata=metadata,
        )
