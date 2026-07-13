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

## Get Your API Key

Sign in to the dashboard, open **Settings → API keys**, and click **Generate key**. Copy the
`vd_live_...` key immediately — it's shown only once (only a hash is stored). Lost it? Use
**Regenerate key**, which revokes the old one and issues a new one.

## Your First Wrap (local, in-process)

Runs the pipeline in your own process using your provider keys from `.env`:

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

## Hosted Mode (SaaS)

Set `VERDANT_API_URL` (or pass `base_url`) and the SDK runs the pipeline on the hosted API —
provider keys stay server-side (managed in the dashboard), so you only need your VERDANT key:

```python
client = VerdantClient(api_key="vd_live_...", base_url="https://verdant-be.onrender.com")

result = await client.run(
    context_type="hiring",
    input_text="Should we hire this candidate from Lagos?",
)
print(result.trust_score, result.flags)
```

### Hybrid: wrap your own call, analyze on the server

Want to keep calling **your own** model but skip local provider keys? Pass
`remote_analysis=True`. Your `fn` runs locally, and only the analysis stages run on the
hosted API using the dashboard-managed keys:

```python
client = VerdantClient(api_key="vd_live_...", base_url="https://verdant-be.onrender.com")

def gen(**kwargs):
    return genai_client.models.generate_content(**kwargs).text

result = await client.wrap(
    fn=gen,
    context_type="hiring",
    input_text=question,
    model="gemini-2.5-flash",
    contents=question,
    remote_analysis=True,   # analysis runs server-side with dashboard keys
)
print(result.output)        # your model's output
print(result.trust_score)   # scored server-side — no local ANTHROPIC/GEMINI key needed
```

Requires an Anthropic/Gemini key configured in the dashboard (Settings → Provider Keys).

### Directly via the API

The pipeline endpoint is authenticated — pass your key as a Bearer token:

```bash
curl -X POST https://verdant-be.onrender.com/pipeline/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer vd_live_..." \
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
