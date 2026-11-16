from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from ..config import Settings, get_settings
from ..models import AuditPayload, ContextType


def _json(value: Any) -> str:
    return json.dumps(value, default=str)


def _row(record: Any) -> dict[str, Any] | None:
    if record is None:
        return None
    result = dict(record)
    for key in ("raw_output", "clean_output", "stages", "flags", "metadata",
                "demographic_focus", "policy_notes", "baseline_data", "scopes"):
        if isinstance(result.get(key), str):
            result[key] = json.loads(result[key])
    return result


class DBService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if not self.settings.database_url:
            raise RuntimeError("DATABASE_URL is required")
        self.pool = await asyncpg.create_pool(self.settings.database_url, min_size=1, max_size=10)
        await self.ping()

    def _pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("Database is unavailable")
        return self.pool

    async def ping(self) -> bool:
        await self._pool().fetchval("select 1")
        return True

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def fetch_baseline(self, context_type: str | ContextType) -> dict[str, Any] | None:
        context = ContextType.normalize(context_type).value
        return _row(await self._pool().fetchrow(
            "select * from fairness_baselines where context_type=$1 and active=true order by updated_at desc limit 1", context))

    async def insert_audit_log(self, payload: AuditPayload, owner_id: str) -> dict[str, Any]:
        if not owner_id:
            raise ValueError("Audit owner is required")
        row = payload.model_dump(mode="json")
        result = await self._pool().fetchrow("""
            insert into audit_logs (id,owner_id,request_id,context_type,input_text,output_text,
                raw_output,clean_output,stages,trust_score,flags,explanation,metadata,
                model_name,duration_ms,error,created_at)
            values ($1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb,$9::jsonb,$10,$11::jsonb,$12,$13::jsonb,$14,$15,$16,$17)
            returning *""",
            UUID(str(row.get("audit_id") or uuid4())), UUID(owner_id), UUID(row["request_id"]),
            ContextType.normalize(payload.context_type).value, row["input_text"], row["output_text"],
            _json(row["raw_output"]), _json(row["clean_output"]), _json(row["stages"]),
            row["trust_score"], _json(row["flags"]), row["explanation"], _json(row["metadata"]),
            row["model_name"] or "unknown", row["duration_ms"], row["error"], payload.created_at)
        return _row(result) or {}

    async def list_audits(self, owner_id: str, limit: int = 50, offset: int = 0,
                          context_type: str | ContextType | None = None,
                          since: datetime | None = None) -> tuple[list[dict[str, Any]], int]:
        context = ContextType.normalize(context_type).value if context_type else None
        where = "owner_id=$1 and ($2::text is null or context_type=$2) and ($3::timestamptz is null or created_at >= $3)"
        async with self._pool().acquire() as conn:
            total = await conn.fetchval(f"select count(*) from audit_logs where {where}", UUID(owner_id), context, since)
            records = await conn.fetch(f"select * from audit_logs where {where} order by created_at desc,id desc limit $4 offset $5",
                                       UUID(owner_id), context, since, max(1, min(limit, 500)), max(0, offset))
        return [_row(r) or {} for r in records], total

    async def get_audit(self, audit_id: str | UUID, owner_id: str) -> dict[str, Any] | None:
        return _row(await self._pool().fetchrow(
            "select * from audit_logs where id=$1 and owner_id=$2", UUID(str(audit_id)), UUID(owner_id)))

    async def fetch_recent_audits(self, context_type: str | ContextType | None = None,
                                  limit: int = 50, owner_id: str | None = None) -> list[dict[str, Any]]:
        if not owner_id:
            return []
        return (await self.list_audits(owner_id, limit=limit, context_type=context_type))[0]

    async def report_audits(self, owner_id: str, since: datetime) -> list[dict[str, Any]]:
        records = await self._pool().fetch(
            "select context_type,trust_score,flags from audit_logs where owner_id=$1 and created_at >= $2",
            UUID(owner_id), since)
        return [_row(r) or {} for r in records]

    async def fetch_webhook_configs(self, active_only: bool = True, owner_id: str | None = None) -> list[dict[str, Any]]:
        if not owner_id:
            return []
        records = await self._pool().fetch(
            "select * from webhook_configs where owner_id=$1 and ($2::boolean=false or active=true)",
            UUID(owner_id), active_only)
        return [_row(r) or {} for r in records]

    async def fetch_api_key(self, key_prefix: str) -> dict[str, Any] | None:
        return _row(await self._pool().fetchrow("select * from api_keys where key_prefix=$1", key_prefix))

    async def create_api_key(self, record: dict[str, Any]) -> dict[str, Any]:
        result = await self._pool().fetchrow(
            "insert into api_keys (owner_id,key_prefix,hashed_key,label,scopes) values ($1,$2,$3,$4,$5::jsonb) returning *",
            UUID(record["owner_id"]), record["key_prefix"], record["hashed_key"],
            record.get("label"), _json(record.get("scopes", [])))
        return _row(result) or {}

    async def list_api_keys(self, owner_id: str, active_only: bool = True) -> list[dict[str, Any]]:
        records = await self._pool().fetch(
            "select * from api_keys where owner_id=$1 and ($2::boolean=false or active=true) order by created_at desc",
            UUID(owner_id), active_only)
        return [_row(r) or {} for r in records]

    async def regenerate_api_key(self, owner_id: str, record: dict[str, Any]) -> dict[str, Any]:
        async with self._pool().acquire() as conn:
            async with conn.transaction():
                await conn.execute("update api_keys set active=false,updated_at=now() where owner_id=$1 and active=true", UUID(owner_id))
                result = await conn.fetchrow(
                    "insert into api_keys (owner_id,key_prefix,hashed_key,label,scopes) values ($1,$2,$3,$4,$5::jsonb) returning *",
                    UUID(owner_id), record["key_prefix"], record["hashed_key"],
                    record.get("label"), _json(record.get("scopes", [])))
        return _row(result) or {}

    async def revoke_api_keys_for_user(self, owner_id: str) -> int:
        records = await self._pool().fetch(
            "update api_keys set active=false,updated_at=now() where owner_id=$1 and active=true returning id", UUID(owner_id))
        return len(records)

    async def touch_api_key_last_used(self, key_prefix: str) -> None:
        await self._pool().execute("update api_keys set last_used_at=now() where key_prefix=$1", key_prefix)

    async def create_user(self, email: str, password_hash: str, full_name: str) -> dict[str, Any]:
        return _row(await self._pool().fetchrow(
            "insert into users (email,password_hash,full_name) values ($1,$2,$3) returning id,email,full_name,role",
            email, password_hash, full_name)) or {}

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        return _row(await self._pool().fetchrow("select * from users where email=$1", email))

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return _row(await self._pool().fetchrow(
            "select id,email,full_name,role from users where id=$1", UUID(user_id)))

    async def get_provider_key(self, provider: str, owner_id: str | None = None) -> str | None:
        if owner_id is None:
            return None
        return await self._pool().fetchval(
            "select api_key from user_provider_keys where owner_id=$1 and provider=$2",
            UUID(owner_id), provider)

    async def set_provider_key(self, owner_id: str, provider: str, api_key: str) -> None:
        await self._pool().execute(
            "insert into user_provider_keys (owner_id,provider,api_key) values ($1,$2,$3) "
            "on conflict(owner_id,provider) do update set api_key=excluded.api_key,updated_at=now()",
            UUID(owner_id), provider, api_key)

    async def get_provider_keys_status(self, owner_id: str) -> dict[str, bool]:
        records = await self._pool().fetch(
            "select provider,api_key from user_provider_keys where owner_id=$1", UUID(owner_id))
        return {r["provider"]: bool(r["api_key"]) for r in records}
