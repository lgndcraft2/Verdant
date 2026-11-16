-- Store each user's model-provider credentials independently.
create table if not exists user_provider_keys (
  owner_id uuid not null references users(id) on delete cascade,
  provider text not null check (provider in ('anthropic','gemini')),
  api_key text not null,
  updated_at timestamptz not null default now(),
  primary key (owner_id, provider)
);
create index if not exists user_provider_keys_owner_idx on user_provider_keys(owner_id);

revoke all on user_provider_keys from public;
