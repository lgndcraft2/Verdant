create extension if not exists pgcrypto;

create table if not exists public.fairness_baselines (
    id uuid primary key default gen_random_uuid(),
    context_type text not null unique,
    baseline_name text not null,
    baseline_version text not null,
    demographic_focus jsonb not null default '[]'::jsonb,
    baseline_summary text not null,
    policy_notes jsonb not null default '[]'::jsonb,
    baseline_data jsonb not null default '{}'::jsonb,
    source text not null default 'seed',
    confidence numeric(4, 3) not null default 0.8,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists fairness_baselines_context_type_idx
    on public.fairness_baselines (context_type);

create table if not exists public.audit_logs (
    id uuid primary key default gen_random_uuid(),
    request_id uuid not null,
    context_type text not null,
    input_text text not null,
    output_text text not null,
    raw_output jsonb,
    clean_output jsonb,
    stages jsonb not null,
    trust_score integer not null,
    flags jsonb not null default '[]'::jsonb,
    explanation text not null,
    metadata jsonb not null default '{}'::jsonb,
    model_name text not null default 'claude-sonnet-4-6',
    duration_ms integer not null default 0,
    error text,
    created_at timestamptz not null default now()
);

create index if not exists audit_logs_created_at_idx
    on public.audit_logs (created_at desc);

create index if not exists audit_logs_context_type_idx
    on public.audit_logs (context_type);

create index if not exists audit_logs_request_id_idx
    on public.audit_logs (request_id);

create table if not exists public.webhook_configs (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    url text not null,
    secret text,
    min_trust_score integer not null default 40,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.api_keys (
    id uuid primary key default gen_random_uuid(),
    key_prefix text not null unique,
    hashed_key text not null,
    label text,
    scopes jsonb not null default '[]'::jsonb,
    active boolean not null default true,
    last_used_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists api_keys_key_prefix_idx
    on public.api_keys (key_prefix);
