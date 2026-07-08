# Quickstart

Get VERDANT running locally and wrap your first AI call in under 5 minutes.

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for the dashboard)
- **Redis** (optional — the SDK falls back to in-memory caching)
- API keys for **Anthropic** and/or **Google Gemini**

---

## 1. Clone the Repository

```bash
git clone https://github.com/your-org/verdant.git
cd verdant
```

## 2. Set Up Environment Variables

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
REDIS_URL=redis://localhost:6379/0
```

> **Tip:** VERDANT works without Supabase or Redis — it falls back to in-memory storage. This is fine for local development but not recommended for production.

## 3. Install the SDK

```bash
cd sdk
pip install -e .
cd ..
```

## 4. Start the API Server

```bash
# Option A: Direct
uvicorn api.main:app --reload --port 8000

# Option B: Docker (includes Redis)
docker compose up
```

## 5. Start the Dashboard

```bash
cd dashboard
npm install
npm run dev
```

The dashboard will be available at [http://localhost:3000](http://localhost:3000).

---

## Your First Wrap

```python
from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")

# Wrap any AI call
result = await client.wrap(
    fn=openai.chat.completions.create,
    model="gpt-4o",
    messages=[{"role": "user", "content": "Is this candidate a good fit?"}]
)

print(result.output)        # Clean AI response
print(result.trust_score)   # 0–100
print(result.flags)         # Bias/risk flags
print(result.explanation)   # Plain-language explanation
```

### Without a Wrapped Function

You can also run the pipeline directly via the API — useful for testing:

```bash
curl -X POST http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Should we hire this candidate from Lagos?",
    "context_type": "hiring"
  }'
```

The response includes the full audit payload with trust score, bias flags, and a plain-language explanation.

---

## What Happens Under the Hood

Every call to `client.wrap()` passes through the 5-stage reasoning pipeline:

1. **Intent Extraction** — What is this AI output trying to do?
2. **Fairness Baseline Load** — Which Nigerian demographic baseline applies?
3. **Bias Pattern Match** — Does the output match known bias patterns?
4. **Explanation Generation** — Plain-language "why did the AI say this?"
5. **Trust Synthesis** — 0–100 trust score from all stage signals

The full audit is stored in Supabase and visible in the dashboard.

---

## Next Steps

- Read the [API Reference](./api-reference.md) for endpoint details
- Explore the dashboard at `http://localhost:3000/overview`
- Configure webhook alerts in Settings for low-trust outputs
