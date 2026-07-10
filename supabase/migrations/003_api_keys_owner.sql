-- API keys: associate each issued VERDANT key with the Supabase user who created it.
-- The api_keys table (prefix, hashed_key, active, last_used_at, ...) already exists
-- in 001_init.sql; this migration only adds per-user ownership.
alter table public.api_keys add column if not exists user_id uuid;

create index if not exists api_keys_user_id_idx
    on public.api_keys (user_id);
