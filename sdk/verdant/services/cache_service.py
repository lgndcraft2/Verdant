from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from ..config import Settings, get_settings
from ..models import ContextType

logger = logging.getLogger(__name__)


def _json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return str(value)


@dataclass
class _CacheEntry:
    value: str
    expires_at: float | None = None


class _MemoryCacheBackend:
    def __init__(self) -> None:
        self._store: dict[str, _CacheEntry] = {}

    def _expired(self, entry: _CacheEntry | None) -> bool:
        if entry is None:
            return True
        return entry.expires_at is not None and time.time() > entry.expires_at

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if self._expired(entry):
            self._store.pop(key, None)
            return None
        return entry.value if entry else None

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = _CacheEntry(value=value, expires_at=(time.time() + ex) if ex else None)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None


class _RedisCacheBackend:
    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis

        self._redis = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self._redis.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def ping(self) -> bool:
        return bool(await self._redis.ping())

    async def close(self) -> None:
        await self._redis.aclose()


class CacheService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._backend = self._build_backend()

    def _build_backend(self) -> Any:
        if self.settings.redis_url:
            try:
                return _RedisCacheBackend(self.settings.redis_url)
            except Exception as exc:  # pragma: no cover - import/runtime guard
                logger.warning("Redis unavailable, using in-memory cache: %s", exc)
        return _MemoryCacheBackend()

    def baseline_key(self, context_type: str | ContextType) -> str:
        return f"verdant:baseline:{ContextType.normalize(context_type).value}"

    def register_key(self, key_prefix: str) -> str:
        return f"verdant:register:{key_prefix}"

    async def get(self, key: str) -> str | None:
        return await self._backend.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        await self._backend.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._backend.delete(key)

    async def get_json(self, key: str) -> Any | None:
        value = await self.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        await self.set(key, json.dumps(value, default=_json_default, ensure_ascii=False), ttl_seconds)

    async def get_baseline(self, context_type: str | ContextType) -> Any | None:
        return await self.get_json(self.baseline_key(context_type))

    async def set_baseline(self, context_type: str | ContextType, baseline: Any, ttl_seconds: int | None = 3600) -> None:
        await self.set_json(self.baseline_key(context_type), baseline, ttl_seconds=ttl_seconds)

    async def get_register_entry(self, key_prefix: str) -> Any | None:
        return await self.get_json(self.register_key(key_prefix))

    async def set_register_entry(self, key_prefix: str, value: Any, ttl_seconds: int | None = 3600) -> None:
        await self.set_json(self.register_key(key_prefix), value, ttl_seconds=ttl_seconds)

    async def ping(self) -> bool:
        return bool(await self._backend.ping())

    async def close(self) -> None:
        await self._backend.close()
