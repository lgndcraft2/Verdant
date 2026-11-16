create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  full_name text not null,
  role text not null default 'member' check (role in ('member','admin')),
  created_at timestamptz not null default now()
);

create table if not exists fairness_baselines (
  id uuid primary key default gen_random_uuid(),
  context_type text not null unique,
  baseline_name text not null,
  baseline_version text not null,
  demographic_focus jsonb not null default '[]',
  baseline_summary text not null,
  policy_notes jsonb not null default '[]',
  baseline_data jsonb not null default '{}',
  source text not null default 'seed',
  confidence numeric(4,3) not null default 0.8 check (confidence between 0 and 1),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references users(id) on delete cascade,
  request_id uuid not null,
  context_type text not null,
  input_text text not null,
  output_text text not null,
  raw_output jsonb,
  clean_output jsonb,
  stages jsonb not null,
  trust_score integer not null check (trust_score between 0 and 100),
  flags jsonb not null default '[]',
  explanation text not null,
  metadata jsonb not null default '{}',
  model_name text not null,
  duration_ms integer not null default 0 check (duration_ms >= 0),
  error text,
  created_at timestamptz not null default now()
);
create index if not exists audit_logs_owner_created_idx on audit_logs(owner_id,created_at desc);
create index if not exists audit_logs_owner_context_created_idx on audit_logs(owner_id,context_type,created_at desc);

create table if not exists webhook_configs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references users(id) on delete cascade,
  name text not null,
  url text not null,
  secret text,
  min_trust_score integer not null default 40 check (min_trust_score between 0 and 100),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists api_keys (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references users(id) on delete cascade,
  key_prefix text not null unique,
  hashed_key text not null,
  label text,
  scopes jsonb not null default '[]',
  active boolean not null default true,
  last_used_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists api_keys_owner_idx on api_keys(owner_id);

create table if not exists provider_keys (
  provider text primary key check (provider in ('anthropic','gemini')),
  api_key text not null,
  updated_at timestamptz not null default now()
);

revoke all on all tables in schema public from public;
revoke all on all sequences in schema public from public;
