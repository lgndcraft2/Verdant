-- Provider keys: stores Anthropic/Gemini API keys configured via the Dashboard
create table if not exists public.provider_keys (
    provider text primary key,
    api_key text not null,
    label text,
    updated_at timestamptz not null default now()
);

-- Seed rows so upserts work cleanly
insert into public.provider_keys (provider, api_key, label)
values
    ('anthropic', '', 'Anthropic Claude'),
    ('gemini', '', 'Google Gemini')
on conflict (provider) do nothing;
