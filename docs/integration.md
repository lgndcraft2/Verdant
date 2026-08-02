# Integration Guide

How to add VERDANT to your app: wrap an AI decision, get back a trust score,
bias flags, and a plain-language explanation you can log or act on.

---

## 1. Install

```bash
pip install verdant
```

Python 3.11+. The SDK is async — call it from an `async def` with `await`.

## 2. Get your keys

VERDANT uses **two kinds of keys**, and it matters which lives where:

| Key | Where it goes | Purpose |
|---|---|---|
| **VERDANT API key** (`vd_live_...`) | Your app (`VERDANT_API_KEY`) | Authenticates you to VERDANT |
| **Provider keys** (Anthropic / Gemini) | The **dashboard** → Settings → Provider Keys | Let the VERDANT server run the reasoning stages |

1. Dashboard → **Settings → API keys → Generate key** → copy the `vd_live_...` value (shown once).
2. Dashboard → **Settings → Provider Keys** → paste your Anthropic and/or Gemini key.

You **do not** put provider keys in your app — the server uses the ones from the dashboard.

## 3. Pick a method

Everything runs through the hosted API — your VERDANT key is all you need. Pick based on
whether you want VERDANT to call the model for you, or call it yourself:

| Method | You call | Who runs your model |
|---|---|---|
| **`run()`** | `client.run(context_type, input_text)` | The VERDANT server |
| **`wrap(fn=...)`** | your own model, then VERDANT analyses the output | You (locally) |

Use `run()` for the simplest setup, or `wrap()` when you want to keep your own model call
(custom prompts, streaming, a provider VERDANT doesn't host, etc.).

## 4. Integrate

### `run()` — let VERDANT do everything

```python
import asyncio
from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")   # the key is all you need

async def main():
    result = await client.run(
        context_type="hiring",
        input_text="Evaluate this candidate for the senior analyst role.",
    )
    print(result.output)
    print(result.trust_score, result.flags)

asyncio.run(main())
```

### `wrap()` — wrap your own model call

Your model runs locally; the analysis runs on the server with your dashboard keys.
Return a **string** from your function so VERDANT scores the actual text:

```python
import asyncio
from google import genai
from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")

async def main():
    genai_client = genai.Client(api_key="AIza...")   # your own Gemini key

    def gen(**kwargs):
        return genai_client.models.generate_content(**kwargs).text   # return text

    result = await client.wrap(
        fn=gen,
        context_type="hiring",
        input_text="Evaluate this candidate for the senior analyst role.",
        model="gemini-2.5-flash",
        contents="Evaluate this candidate for the senior analyst role.",
    )
    print(result.output)          # your model's answer
    print(result.trust_score)     # scored server-side

asyncio.run(main())
```

Anything after `fn`, `context_type`, `input_text`, and `metadata` is forwarded to your
function as keyword arguments (here, `model=` and `contents=`).

## 5. Read the result

Every mode returns the same object:

```python
result.output        # your model's clean output
result.trust_score   # 0–100 composite score
result.flags         # e.g. ["proxy_language_detected"]
result.explanation   # plain-language rationale

# Full reasoning chain
audit = result.audit
audit.stages.intent.detected_intent          # e.g. "candidate_evaluation"
audit.stages.intent.context_type.value        # "hiring"
audit.stages.intent.confidence                # 0.0–1.0
audit.stages.baseline.baseline_name           # e.g. "ng_hiring_v2"
audit.stages.baseline.baseline_version        # e.g. "2.1"
audit.stages.bias.severity.value              # "low" | "medium" | "high" | "critical"
audit.stages.bias.bias_score                  # numeric bias signal
audit.stages.bias.matched_patterns            # ["proxy_language", ...]
audit.stages.trust.trust_score                # 0–100
audit.stages.trust.risk_level.value           # "low" | "medium" | "high" | "critical"
audit.stages.trust.alerts                     # e.g. ["Wrapped function call failed"]
```

A common pattern — pass `output` to your user, gate on `trust_score`, log the `audit`:

```python
if result.trust_score < 40:
    escalate_for_human_review(result.audit)
return result.output
```

## 6. Context types

Pass the context so VERDANT loads the right fairness baseline:

| `context_type` | Use case |
|---|---|
| `hiring` | Recruitment, candidate evaluation, screening |
| `lending` | Loan applications, credit scoring |
| `content` | Content moderation, publishing (aliases: `content_moderation`, `moderation`) |
| `healthcare` | Triage, diagnosis support |

Omit it and VERDANT infers it from the input text.

## 7. Error handling

If your wrapped function raises, VERDANT catches it — your app stays up. The audit still
records the run, the trust score is capped to critical, and `audit.error` holds the message.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `VerdantClient requires an api_key` | No key passed and `VERDANT_API_KEY` not set | Pass `VerdantClient(api_key="vd_live_...")` or set `VERDANT_API_KEY` |
| `VERDANT API returned 404` | Server doesn't have the endpoint yet | Update/redeploy the VERDANT API |
| heuristic-only scores | No provider key reachable | Add an Anthropic/Gemini key in the dashboard → Settings → Provider Keys |
| `result.output` is a big object, not text | Your `fn` returned a raw SDK response | Return the text, e.g. `...generate_content(**kwargs).text` |
| `401 Unauthorized` | Missing/invalid VERDANT key | Regenerate in Settings → API keys and update `VERDANT_API_KEY` |

## Reference

- Full API + result schema: [api-reference.md](./api-reference.md)
- Getting started: [quickstart.md](./quickstart.md)
