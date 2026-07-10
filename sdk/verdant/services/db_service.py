from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from ..config import Settings, get_settings
from ..models import AuditPayload, ContextType

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
            "provider_keys": {},
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

    async def create_api_key(self, record: dict[str, Any]) -> dict[str, Any]:
        """Insert a newly issued VERDANT API key (prefix + hash, never the raw key)."""
        row = dict(record)
        row.setdefault("id", str(uuid4()))
        row.setdefault("active", True)
        row.setdefault("scopes", [])
        row.setdefault("created_at", datetime.now(timezone.utc).isoformat())

        if self._supabase is None:
            stored = deepcopy(row)
            self._memory["api_keys"].append(stored)
            return stored

        def _run() -> dict[str, Any]:
            result = self._supabase.table("api_keys").insert(row).execute()
            data = getattr(result, "data", None) or []
            return data[0] if data else row

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase api key insert failed, storing in memory: %s", exc)
            stored = deepcopy(row)
            self._memory["api_keys"].append(stored)
            return stored

    async def list_api_keys(self, user_id: str, active_only: bool = True) -> list[dict[str, Any]]:
        """List a user's API keys. Callers must strip hashed_key before returning to clients."""
        if self._supabase is None:
            keys = [k for k in self._memory["api_keys"] if str(k.get("user_id")) == str(user_id)]
            if active_only:
                keys = [k for k in keys if k.get("active", True)]
            keys = sorted(keys, key=lambda item: _as_datetime(item.get("created_at")), reverse=True)
            return deepcopy(keys)

        def _run() -> list[dict[str, Any]]:
            query = self._supabase.table("api_keys").select("*").eq("user_id", user_id)
            if active_only:
                query = query.eq("active", True)
            result = query.order("created_at", desc=True).execute()
            return getattr(result, "data", None) or []

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase api key list failed, falling back to memory: %s", exc)
            keys = [k for k in self._memory["api_keys"] if str(k.get("user_id")) == str(user_id)]
            if active_only:
                keys = [k for k in keys if k.get("active", True)]
            keys = sorted(keys, key=lambda item: _as_datetime(item.get("created_at")), reverse=True)
            return deepcopy(keys)

    async def revoke_api_keys_for_user(self, user_id: str) -> int:
        """Deactivate all of a user's active keys. Returns how many were revoked."""
        now = datetime.now(timezone.utc).isoformat()
        if self._supabase is None:
            count = 0
            for key in self._memory["api_keys"]:
                if str(key.get("user_id")) == str(user_id) and key.get("active", True):
                    key["active"] = False
                    key["updated_at"] = now
                    count += 1
            return count

        def _run() -> int:
            result = (
                self._supabase.table("api_keys")
                .update({"active": False, "updated_at": now})
                .eq("user_id", user_id)
                .eq("active", True)
                .execute()
            )
            return len(getattr(result, "data", None) or [])

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase api key revoke failed, falling back to memory: %s", exc)
            count = 0
            for key in self._memory["api_keys"]:
                if str(key.get("user_id")) == str(user_id) and key.get("active", True):
                    key["active"] = False
                    count += 1
            return count

    async def touch_api_key_last_used(self, key_prefix: str) -> None:
        """Best-effort update of last_used_at; failures are swallowed."""
        now = datetime.now(timezone.utc).isoformat()
        if self._supabase is None:
            for key in self._memory["api_keys"]:
                if key.get("key_prefix") == key_prefix:
                    key["last_used_at"] = now
            return

        def _run() -> None:
            self._supabase.table("api_keys").update({"last_used_at": now}).eq(
                "key_prefix", key_prefix
            ).execute()

        try:
            await asyncio.to_thread(_run)
        except Exception as exc:
            logger.debug("last_used_at touch failed (non-fatal): %s", exc)

    async def get_user_from_token(self, access_token: str) -> dict[str, Any] | None:
        """Validate a Supabase access token and return {user_id, email}, or None."""
        if self._supabase is None:
            return None

        def _run() -> dict[str, Any] | None:
            response = self._supabase.auth.get_user(access_token)
            user = getattr(response, "user", None)
            if user is None:
                return None
            return {"user_id": str(user.id), "email": getattr(user, "email", None)}

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase token verification failed: %s", exc)
            return None

    async def get_provider_key(self, provider: str) -> str | None:
        """Fetch an LLM provider API key (e.g. 'anthropic', 'gemini') from DB."""
        if self._supabase is None:
            key = self._memory["provider_keys"].get(provider, "")
            return key if key else None

        def _run() -> str | None:
            result = (
                self._supabase.table("provider_keys")
                .select("api_key")
                .eq("provider", provider)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None) or []
            if data and data[0].get("api_key"):
                return data[0]["api_key"]
            return None

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase provider key fetch failed: %s", exc)
            return None

    async def set_provider_key(self, provider: str, api_key: str) -> None:
        """Upsert an LLM provider API key."""
        if self._supabase is None:
            self._memory["provider_keys"][provider] = api_key
            return

        def _run() -> None:
            self._supabase.table("provider_keys").upsert(
                {"provider": provider, "api_key": api_key, "updated_at": datetime.now(timezone.utc).isoformat()},
                on_conflict="provider",
            ).execute()

        try:
            await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase provider key upsert failed, storing in memory: %s", exc)
            self._memory["provider_keys"][provider] = api_key

    async def get_all_provider_keys_status(self) -> dict[str, bool]:
        """Return a dict of provider -> bool indicating if a key is configured."""
        if self._supabase is None:
            return {
                provider: bool(key)
                for provider, key in self._memory["provider_keys"].items()
            }

        def _run() -> dict[str, bool]:
            result = self._supabase.table("provider_keys").select("provider, api_key").execute()
            data = getattr(result, "data", None) or []
            return {row["provider"]: bool(row.get("api_key")) for row in data}

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.warning("Supabase provider keys status fetch failed: %s", exc)
            return {}
