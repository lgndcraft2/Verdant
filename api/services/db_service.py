from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sdk.verdant.config import Settings, get_settings
from sdk.verdant.models import AuditPayload, ContextType

logger = logging.getLogger(__name__)


def _normalize_context_type(context_type: str | ContextType) -> str:
    return ContextType.normalize(context_type).value


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


class DBService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._supabase = self._build_client()
        self._memory = {
            "audit_logs": [],
            "fairness_baselines": [],
            "webhook_configs": [],
            "api_keys": [],
        }

    def _build_client(self) -> Any:
        if not (self.settings.supabase_url and self.settings.supabase_service_role_key):
            return None
        try:
            from supabase import create_client

            return create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key,
            )
        except Exception as exc:  # pragma: no cover - import/runtime guard
            logger.warning("Supabase unavailable, using in-memory DB: %s", exc)
            return None

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None

    async def fetch_baseline(self, context_type: str | ContextType) -> dict[str, Any] | None:
        normalized = _normalize_context_type(context_type)
        if self._supabase is None:
            for row in reversed(self._memory["fairness_baselines"]):
                if row.get("context_type") == normalized and row.get("active", True):
                    return deepcopy(row)
            return None

        def _run() -> dict[str, Any] | None:
            query = (
                self._supabase.table("fairness_baselines")
                .select("*")
                .eq("context_type", normalized)
                .eq("active", True)
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )
            data = getattr(query, "data", None) or []
            return data[0] if data else None

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase baseline fetch failed, falling back to memory: %s", exc)
            return None

    async def insert_audit_log(self, payload: AuditPayload) -> dict[str, Any]:
        row = payload.model_dump(mode="json")
        row["context_type"] = _normalize_context_type(payload.context_type)
        row["stages"] = payload.stages.model_dump(mode="json")
        row["flags"] = list(payload.flags)
        row["raw_output"] = payload.raw_output
        row["clean_output"] = payload.clean_output
        audit_id = str(row.pop("audit_id") or uuid4())
        row["id"] = audit_id

        if self._supabase is None:
            stored = deepcopy(row)
            self._memory["audit_logs"].append(stored)
            return stored

        def _run() -> dict[str, Any]:
            result = (
                self._supabase.table("audit_logs")
                .insert(row)
                .execute()
            )
            data = getattr(result, "data", None) or []
            return data[0] if data else row

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase audit insert failed, storing audit in memory: %s", exc)
            stored = deepcopy(row)
            self._memory["audit_logs"].append(stored)
            return stored

    async def list_audits(
        self,
        limit: int = 50,
        offset: int = 0,
        context_type: str | ContextType | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        normalized = _normalize_context_type(context_type) if context_type else None
        if self._supabase is None:
            audits = self._memory["audit_logs"]
            if normalized:
                audits = [item for item in audits if item.get("context_type") == normalized]
            audits = sorted(audits, key=lambda item: _as_datetime(item.get("created_at")), reverse=True)
            total = len(audits)
            return deepcopy(audits[offset : offset + limit]), total

        def _run() -> tuple[list[dict[str, Any]], int]:
            query = self._supabase.table("audit_logs").select("*", count="exact")
            if normalized:
                query = query.eq("context_type", normalized)
            result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            data = getattr(result, "data", None) or []
            total = int(getattr(result, "count", 0) or len(data))
            return data, total

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase audit list failed, falling back to memory: %s", exc)
            audits = self._memory["audit_logs"]
            if normalized:
                audits = [item for item in audits if item.get("context_type") == normalized]
            audits = sorted(audits, key=lambda item: _as_datetime(item.get("created_at")), reverse=True)
            total = len(audits)
            return deepcopy(audits[offset : offset + limit]), total

    async def get_audit(self, audit_id: str | UUID) -> dict[str, Any] | None:
        audit_id_str = str(audit_id)
        if self._supabase is None:
            for row in self._memory["audit_logs"]:
                if str(row.get("id")) == audit_id_str or str(row.get("audit_id")) == audit_id_str:
                    return deepcopy(row)
            return None

        def _run() -> dict[str, Any] | None:
            result = (
                self._supabase.table("audit_logs")
                .select("*")
                .eq("id", audit_id_str)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None) or []
            return data[0] if data else None

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase audit fetch failed, falling back to memory: %s", exc)
            for row in self._memory["audit_logs"]:
                if str(row.get("id")) == audit_id_str or str(row.get("audit_id")) == audit_id_str:
                    return deepcopy(row)
            return None

    async def fetch_recent_audits(
        self,
        context_type: str | ContextType | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        audits, _ = await self.list_audits(limit=limit, offset=0, context_type=context_type)
        return audits

    async def fetch_webhook_configs(self, active_only: bool = True) -> list[dict[str, Any]]:
        if self._supabase is None:
            configs = self._memory["webhook_configs"]
            if active_only:
                configs = [item for item in configs if item.get("active", True)]
            return deepcopy(configs)

        def _run() -> list[dict[str, Any]]:
            query = self._supabase.table("webhook_configs").select("*")
            if active_only:
                query = query.eq("active", True)
            result = query.execute()
            return getattr(result, "data", None) or []

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase webhook config fetch failed, falling back to memory: %s", exc)
            configs = self._memory["webhook_configs"]
            if active_only:
                configs = [item for item in configs if item.get("active", True)]
            return deepcopy(configs)

    async def fetch_api_key(self, key_prefix: str) -> dict[str, Any] | None:
        if self._supabase is None:
            for row in self._memory["api_keys"]:
                if row.get("key_prefix") == key_prefix:
                    return deepcopy(row)
            return None

        def _run() -> dict[str, Any] | None:
            result = (
                self._supabase.table("api_keys")
                .select("*")
                .eq("key_prefix", key_prefix)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None) or []
            return data[0] if data else None

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase api key fetch failed, falling back to memory: %s", exc)
            for row in self._memory["api_keys"]:
                if row.get("key_prefix") == key_prefix:
                    return deepcopy(row)
            return None
