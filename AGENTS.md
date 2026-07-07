# VERDANT — CLAUDE.md

> Inspectable AI governance — built for African builders

This file gives Claude context about the VERDANT codebase, architecture decisions, conventions, and how to contribute effectively.

---

## Project Overview

VERDANT is a lightweight, NDPR-native SDK that wraps any AI integration and returns a structured reasoning chain alongside every output — bias flags, plain-language explanations, and a trust score — without requiring developers to change their existing code.

**Target users:** Nigerian and African developers shipping AI into high-stakes contexts (hiring, lending, content moderation, healthcare).

**Core value prop:** Drop-in accountability. Any AI call becomes inspectable in one wrap.

---

## Repository Structure

```
verdant/
├── sdk/                        # Python SDK (pip installable)
│   ├── verdant/
│   │   ├── __init__.py
│   │   ├── client.py           # Main VerdantClient class
│   │   ├── pipeline.py         # Reasoning chain orchestrator
│   │   ├── stages/             # Individual reasoning stage modules
│   │   │   ├── intent.py       # Intent extraction
│   │   │   ├── baseline.py     # Fairness baseline loader
│   │   │   ├── bias.py         # Bias pattern matching
│   │   │   ├── explain.py      # Explanation generation
│   │   │   └── trust.py        # Trust score synthesis
│   │   ├── models.py           # Pydantic models for all structured outputs
│   │   └── config.py           # SDK configuration
│   └── pyproject.toml
│
├── api/                        # FastAPI backend
│   ├── main.py
│   ├── routers/
│   │   ├── audit.py            # Audit log endpoints
│   │   ├── pipeline.py         # Pipeline execution endpoints
│   │   ├── webhooks.py         # Webhook dispatch
│   │   └── reports.py          # NDPR compliance report export
│   ├── services/
│   │   ├── claude_service.py   # Anthropic SDK integration
│   │   ├── gemini_service.py   # Gemini SDK integration (fallback/comparison)
│   │   ├── cache_service.py    # Redis caching layer
│   │   └── db_service.py       # Supabase client
│   ├── models/                 # SQLAlchemy / Supabase table models
│   └── config.py
│
├── dashboard/                  # Next.js frontend
│   ├── app/
│   │   ├── page.tsx            # Overview / trust score feed
│   │   ├── audits/             # Per-decision audit explorer
│   │   ├── reports/            # NDPR export UI
│   │   └── settings/           # API keys, webhook config, thresholds
│   ├── components/
│   └── lib/
│
├── supabase/
│   ├── migrations/             # DB schema migrations
│   └── seed.sql
│
├── tests/
│   ├── sdk/
│   └── api/
│
├── docs/
│   ├── quickstart.md
│   └── api-reference.md
│
├── .env.example
├── docker-compose.yml
└── CLAUDE.md                   # You are here
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| SDK | Python 3.11+ | pip installable, minimal dependencies |
| API | FastAPI | <50ms latency target on pipeline execution |
| AI — Primary | Anthropic Claude (`claude-sonnet-4-6`) | Reasoning, explanation generation |
| AI — Secondary | Google Gemini | Fallback, cross-validation on edge cases |
| Database | Supabase (PostgreSQL) | Audit logs, feedback, model versioning |
| Cache | Redis | Frequent baseline/register lookups |
| Dashboard | Next.js 14 (App Router) | TypeScript, Tailwind |
| Auth | Supabase Auth | API key management |

---

## Core Concepts

### The Reasoning Chain
Every AI call wrapped by VERDANT passes through a 5-stage pipeline. Each stage returns structured JSON. No freestyle outputs.

```
Input
  └── Stage 1: Intent Extraction       → what is this output trying to do?
  └── Stage 2: Fairness Baseline Load  → which Nigerian demographic baseline applies?
  └── Stage 3: Bias Pattern Match      → does this output match known bias patterns?
  └── Stage 4: Explanation Generation  → plain-language "why did the AI say this"
  └── Stage 5: Trust Synthesis         → 0–100 trust score from all stage signals
Output (clean) → User
Audit payload  → Dashboard
```

### Fairness Baselines
Baselines are calibrated to Nigerian demographic realities — not Western defaults. They account for ethnic diversity (Yoruba, Igbo, Hausa, and minority groups), regional economic disparity (North/South, urban/rural), gender dynamics in Nigerian professional contexts, and linguistic register.

Baselines are versioned and stored in Supabase. They can be overridden per-client via config.

### Trust Score
0–100 composite score per output. Weighted across:
- Bias signal strength (40%)
- Explanation confidence (30%)
- Intent alignment (20%)
- Historical pattern consistency (10%)

Scores below 40 trigger a webhook alert by default (configurable).

---

## SDK Usage

```python
from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")

# Wrap any AI call
result = await client.wrap(
    fn=openai.chat.completions.create,
    model="gpt-4o",
    messages=[{"role": "user", "content": user_input}]
)

result.output        # Clean AI response — pass this to your user
result.audit         # Full reasoning chain JSON
result.trust_score   # 0–100
result.flags         # List of bias/risk flags
result.explanation   # Plain-language explanation string
```

---

## Environment Variables

```env
# API
VERDANT_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Database
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

# Cache
REDIS_URL=

# Webhooks
WEBHOOK_SECRET=

# Config
ENVIRONMENT=development
LOG_LEVEL=info
TRUST_SCORE_ALERT_THRESHOLD=40
```

---

## Development Conventions

### General
- All pipeline stage outputs must conform to Pydantic models defined in `sdk/verdant/models.py`
- No freestyle string outputs from AI calls — always prompt for structured JSON, always validate against models
- Every API endpoint that touches the reasoning pipeline must log to Supabase before returning

### FastAPI
- Use async throughout — all DB and AI calls are awaited
- Route files own only routing logic — business logic lives in `services/`
- All responses use consistent envelope: `{ data, meta, error }`

### Next.js Dashboard
- App Router only — no Pages Router patterns
- Server Components by default, Client Components only where interactivity requires it
- Tailwind for all styling — no inline styles

### AI Prompting
- System prompts live in `api/services/prompts/` as `.txt` files — not hardcoded in service files
- All Claude calls use `claude-sonnet-4-6`
- Always request JSON output explicitly in the prompt and validate the response before use
- Wrap all AI calls in try/catch — never let a failed AI call crash the pipeline silently

### Commits
- `feat:` new feature
- `fix:` bug fix
- `chore:` config, deps, tooling
- `audit:` changes to reasoning pipeline logic or fairness baselines

---

## Key Design Decisions

**Why a pipeline of stages instead of one big prompt?**
Inspectability. If a trust score is wrong, you need to know which stage produced the bad signal. A monolithic prompt gives you a number with no trace. Staged JSON gives you a full audit of the reasoning.

**Why Nigerian demographic baselines instead of universal ones?**
Universal fairness metrics are Western fairness metrics with a neutral name. Applying them to Nigerian hiring or lending data produces meaningless or actively misleading signals. VERDANT's value proposition is that it was built here, for here.

**Why Claude for explanation generation specifically?**
Explanation quality — the plain-language "why" — is the feature developers will demo to their stakeholders. It needs to be coherent, specific, and defensible. Claude outperforms on nuanced reasoning tasks. Gemini is used for cross-validation on edge cases where a second opinion adds signal.

---

## Team

| Name | Role |
|---|---|
| Raheem | Architecture, FastAPI backend, Claude integration, pitch |
| Emafido | Next.js dashboard |
| Ismail | SDK wrapper, bias logic, Supabase schema |

---

## Hackathon Context

Built at the Believers Tech Network Hackathon — Track 2: AI with Guardrails.
Submission deadline: 3rd August 2026.
Pitch deck: max 7 slides.
Repo must be public on GitHub before submission.

---

*VERDANT — because every decision leaves a trace.*
