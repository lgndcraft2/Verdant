# VERDANT

> Inspectable AI governance — built for African builders

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

VERDANT is a lightweight, NDPR-native SDK that wraps any AI integration and returns a structured reasoning chain alongside every output — bias flags, plain-language explanations, and a trust score — without requiring developers to change their existing code.

**Target users:** Nigerian and African developers shipping AI into high-stakes contexts (hiring, lending, content moderation, healthcare).

**Core value prop:** Drop-in accountability. Any AI call becomes inspectable in one wrap.

---

## How It Works

Every AI call wrapped by VERDANT passes through a 5-stage reasoning pipeline:

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

Each stage returns structured JSON. No freestyle outputs. Full traceability.

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/your-org/verdant.git
cd verdant
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Run

```bash
# Install the SDK
cd sdk && pip install -e . && cd ..

# Start the API
uvicorn api.main:app --reload --port 8000

# Start the dashboard (in another terminal)
cd dashboard && npm install && npm run dev
```

Or use Docker:

```bash
docker compose up
```

### 3. Wrap Your First AI Call

```python
from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")

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

## Architecture

| Layer | Technology |
|---|---|
| SDK | Python 3.11+ (pip installable) |
| API | FastAPI |
| AI — Primary | Anthropic Claude (`claude-sonnet-4-6`) |
| AI — Secondary | Google Gemini (fallback/cross-validation) |
| Database | Supabase (PostgreSQL) |
| Cache | Redis |
| Dashboard | Next.js 14 (App Router, TypeScript, Tailwind) |

---

## Trust Score

0–100 composite score per output, weighted across:

| Component | Weight |
|---|---|
| Bias signal strength | 40% |
| Explanation confidence | 30% |
| Intent alignment | 20% |
| Historical pattern consistency | 10% |

Scores below 40 trigger a webhook alert by default (configurable).

---

## Fairness Baselines

Baselines are calibrated to **Nigerian demographic realities** — not Western defaults. They account for:

- Ethnic diversity (Yoruba, Igbo, Hausa, and minority groups)
- Regional economic disparity (North/South, urban/rural)
- Gender dynamics in Nigerian professional contexts
- Linguistic register and code-switching

Baselines are versioned and stored in Supabase. They can be overridden per-client via config.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/pipeline/run` | Execute the reasoning pipeline |
| `GET` | `/audits` | List audit logs |
| `GET` | `/audits/{id}` | Get a single audit |
| `POST` | `/webhooks/dispatch` | Manually dispatch webhooks |
| `GET` | `/reports/ndpr` | Generate NDPR compliance report |

See [docs/api-reference.md](docs/api-reference.md) for full details.

---

## Documentation

- [Quickstart Guide](docs/quickstart.md)
- [API Reference](docs/api-reference.md)

---

## Project Structure

```
verdant/
├── sdk/              # Python SDK (pip installable)
├── api/              # FastAPI backend
├── dashboard/        # Next.js frontend
├── supabase/         # DB migrations and seed data
├── tests/            # SDK and API tests
└── docs/             # Documentation
```

---

## Running Tests

```bash
cd sdk && pip install -e .[dev] && cd ..
python -m pytest tests/ -v
```

---

## Team

| Name | Role |
|---|---|
| Raheem | Architecture, FastAPI backend|
| Emafido | Next.js dashboard |
| Ismail | SDK wrapper, bias logic, Supabase schema |

---

## Context

Built at the **Believers Tech Network Hackathon** — Track 2: AI with Guardrails.

---

*VERDANT — because every decision leaves a trace.*
