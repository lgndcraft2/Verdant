import Link from "next/link";
import { ArrowIcon, BookIcon, CheckIcon, PulseIcon, ShieldIcon, TraceIcon } from "@/components/icons";

const codeSample = String.raw`from verdant import VerdantClient
import openai

client = VerdantClient(api_key="vd_live_...")

result = await client.wrap(
    fn=openai.chat.completions.create,
    context_type="hiring",
    input_text=user_prompt,
    model="gpt-4o",
    messages=[{"role": "user", "content": user_prompt}],
)

# Pass to your product
print(result.output)        # Clean AI response for your user
print(result.trust_score)   # 0–100 composite score
print(result.flags)         # ["proxy_language_detected"]
print(result.explanation)   # "Role phrasing may disadvantage..."
print(result.audit)         # Full reasoning chain JSON`;

const hostedSample = String.raw`from verdant import VerdantClient

# Point the SDK at your VERDANT deployment. Provider keys (Claude, Gemini)
# live server-side — managed from the dashboard Settings page — so all you
# need locally is your VERDANT key.
client = VerdantClient(
    api_key="vd_live_...",
    base_url="https://verdant-be.onrender.com",   # or set VERDANT_API_URL
)

# run() executes the pipeline on the hosted API over HTTP and returns the
# same result object as wrap().
result = await client.run(
    context_type="hiring",
    input_text="Should we shortlist this candidate from Kano?",
)

print(result.output)        # Response generated server-side
print(result.trust_score)   # 0–100 composite score
print(result.flags)         # ["proxy_language_detected"]
print(result.explanation)   # Plain-language rationale`;

const nonAiSample = String.raw`from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")

# Your existing rules-based function — no AI involved
def legacy_lending_rules(applicant_data: dict) -> dict:
    if applicant_data["location"] == "Rural" and applicant_data["gender"] == "Female":
        return {"status": "rejected", "reason": "High risk demographic profile"}
    return {"status": "approved", "limit": 50000}

applicant = {"name": "Amina", "location": "Rural", "gender": "Female"}

# Wrap it exactly like an AI call
result = await client.wrap(
    fn=legacy_lending_rules,
    context_type="lending",
    input_text=str(applicant),
    applicant_data=applicant,
)

print(result.output)       # {"status": "rejected", ...}
print(result.trust_score)  # Low — bias detected
print(result.flags)        # ["demographic_bias", "gender_proxy"]`;

const rawValueSample = String.raw`from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")

# You already have the output from somewhere else
my_existing_output = "The candidate is rejected due to cultural fit concerns."

# Option 1: Lambda wrapper (quick one-liner)
result = await client.wrap(
    fn=lambda **kwargs: my_existing_output,
    context_type="hiring",
    input_text="Evaluate this candidate for the analyst role.",
)

# Option 2: Async function wrapper (if you prefer explicit code)
async def existing_output(**kwargs):
    return my_existing_output

result = await client.wrap(
    fn=existing_output,
    context_type="hiring",
    input_text="Evaluate this candidate for the analyst role.",
)

print(result.trust_score)  # Pipeline runs on the value as-is
print(result.flags)        # Any bias flags detected in the text
print(result.explanation)  # Plain-language reasoning`;

const errorHandlingSample = String.raw`from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")

async def flaky_ai_call(**kwargs):
    raise ConnectionError("API timeout")

# VERDANT catches the crash — your app stays up
result = await client.wrap(
    fn=flaky_ai_call,
    context_type="lending",
    input_text="Evaluate this loan application.",
)

print(result.output)       # "" (empty — no upstream output)
print(result.trust_score)  # ≤ 15 (capped to critical)
print(result.flags)        # []
print(result.explanation)  # "...The wrapped AI call failed: API timeout."

# The audit still records everything
print(result.audit.stages.trust.risk_level)  # "critical"
print(result.audit.stages.trust.alerts)      # ["Wrapped function call failed"]
print(result.audit.error)                    # "API timeout"`;

const auditBreakdownSample = String.raw`result = await client.wrap(fn=my_ai_call, context_type="hiring", ...)
audit = result.audit

# Top-level audit fields
audit.request_id       # UUID — unique per pipeline run
audit.created_at       # UTC timestamp
audit.context_type     # "hiring", "lending", etc.
audit.input_text       # The input you provided
audit.output_text      # Stringified AI output
audit.model_name       # "claude-sonnet-4-6"
audit.duration_ms      # Pipeline execution time
audit.error            # None if successful, error string if failed

# Per-stage outputs
audit.stages.intent.detected_intent     # e.g. "candidate_evaluation"
audit.stages.intent.confidence          # 0.0–1.0
audit.stages.baseline.baseline_name     # e.g. "ng_hiring_v3"
audit.stages.baseline.baseline_version  # e.g. "3.1"
audit.stages.bias.severity              # "low" | "medium" | "high" | "critical"
audit.stages.bias.matched_patterns      # ["proxy_language", ...]
audit.stages.explanation.caveats        # ["Limited context provided", ...]
audit.stages.trust.score_breakdown      # {"bias": 38.0, "explanation": 28.5, ...}
audit.stages.trust.risk_level           # "low" | "medium" | "high" | "critical"`;

const webhookPayloadSample = String.raw`# Webhook POST payload (sent automatically on low trust)
{
  "event": "verdant.audit.low_trust",
  "timestamp": "2026-07-08T22:30:00+00:00",
  "audit": {
    "audit_id": "550e8400-e29b-41d4-a716-446655440000",
    "context_type": "hiring",
    "trust_score": 28,
    "flags": ["proxy_language_detected", "demographic_bias"],
    "explanation": "The output uses language proxies...",
    "stages": { ... }
  }
}

# Headers included with every webhook
# X-Verdant-Event: verdant.audit.low_trust
# X-Verdant-Timestamp: 2026-07-08T22:30:00+00:00
# X-Verdant-Audit-Id: 550e8400-...
# X-Verdant-Signature: sha256=abc123...  (HMAC-SHA256)`;

const apiCurlSample = String.raw`# Every SDK-facing endpoint requires your VERDANT API key as a Bearer token.
# Generate one from the dashboard: Settings -> API keys -> Generate key.

# Run pipeline via REST API
curl -X POST https://verdant-be.onrender.com/pipeline/run \
  -H "Authorization: Bearer vd_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Evaluate this candidate",
    "context_type": "hiring",
    "metadata": {}
  }'

# Fetch audit logs
curl https://verdant-be.onrender.com/audits?limit=10&context_type=hiring \
  -H "Authorization: Bearer vd_live_..."

# Get a specific audit
curl https://verdant-be.onrender.com/audits/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer vd_live_..."

# Generate NDPR compliance report
curl https://verdant-be.onrender.com/reports/ndpr?days=30 \
  -H "Authorization: Bearer vd_live_..."

# Manually dispatch webhooks for an audit
curl -X POST "https://verdant-be.onrender.com/webhooks/dispatch?audit_id=550e8400-...&force=true" \
  -H "Authorization: Bearer vd_live_..."`;

const envVars = `# Required
VERDANT_API_KEY=vd_live_...

# Hosted mode — point the SDK at a running API. Omit to run the pipeline
# in-process (in which case the provider keys below are used locally).
VERDANT_API_URL=https://verdant-be.onrender.com

# Provider keys (server-side, or in-process mode)
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Cache
REDIS_URL=redis://localhost:6379

# Webhooks
WEBHOOK_SECRET=whsec_...

# Config
ENVIRONMENT=development
LOG_LEVEL=info
TRUST_SCORE_ALERT_THRESHOLD=40`;

const configSample = `from verdant import VerdantClient, VerdantConfig

config = VerdantConfig(
    trust_score_alert_threshold=60,  # Default: 40
    baseline_version="v2.1",         # Pin a baseline
    webhook_url="https://...",        # Override endpoint
    log_level="debug",
)

client = VerdantClient(api_key="vd_live_...", config=config)`;

const contextTypes = [
  { type: "hiring", desc: "Recruitment, candidate evaluation, job screening.", aliases: "—" },
  { type: "lending", desc: "Loan applications, credit scoring, financial assessment.", aliases: "—" },
  { type: "content", desc: "Content moderation, text review, publishing decisions.", aliases: "content_moderation, moderation" },
  { type: "healthcare", desc: "Patient triage, diagnosis support, treatment recommendations.", aliases: "—" },
];

const auditFields = [
  { field: "request_id", type: "UUID", desc: "Unique identifier for this pipeline run." },
  { field: "created_at", type: "datetime", desc: "UTC timestamp of when the pipeline executed." },
  { field: "context_type", type: "str", desc: "The active context: hiring, lending, content, or healthcare." },
  { field: "input_text", type: "str", desc: "The input text passed to the pipeline." },
  { field: "output_text", type: "str", desc: "Stringified version of the AI output." },
  { field: "stages", type: "object", desc: "Full per-stage structured outputs (intent, baseline, bias, explanation, trust)." },
  { field: "trust_score", type: "int", desc: "The composite 0–100 trust score." },
  { field: "flags", type: "list[str]", desc: "All bias flags triggered during the pipeline." },
  { field: "explanation", type: "str", desc: "Plain-language explanation string." },
  { field: "model_name", type: "str", desc: "AI model used (default: claude-sonnet-4-6)." },
  { field: "duration_ms", type: "int", desc: "Pipeline execution time in milliseconds." },
  { field: "error", type: "str | null", desc: "Error message if the wrapped function failed, null otherwise." },
];

const apiEndpoints = [
  { method: "POST", path: "/pipeline/run", desc: "Execute the 5-stage reasoning pipeline on an input. Returns full audit payload with trust score, flags, and explanation." },
  { method: "GET", path: "/audits", desc: "List audit logs with pagination. Supports filtering by context_type. Query params: limit, offset, context_type." },
  { method: "GET", path: "/audits/{audit_id}", desc: "Retrieve a single audit record by ID. Returns the full stage breakdown and metadata." },
  { method: "GET", path: "/reports/ndpr", desc: "Generate an NDPR compliance report. Aggregates trust scores, flag counts, and context breakdown. Query param: days (default 30)." },
  { method: "POST", path: "/webhooks/dispatch", desc: "Manually dispatch webhook alerts for a specific audit. Query params: audit_id, force (bypass threshold check)." },
];

const tocItems = [
  { href: "#overview", label: "Overview" },
  { href: "#installation", label: "Installation" },
  { href: "#api-keys", label: "API keys" },
  { href: "#quickstart", label: "Quick start" },
  { href: "#hosted-mode", label: "Hosted mode" },
  { href: "#result-object", label: "Result object" },
  { href: "#context-types", label: "Context types" },
  { href: "#pipeline-stages", label: "Pipeline stages" },
  { href: "#audit-payload", label: "Audit payload" },
  { href: "#wrapping-non-ai", label: "Wrapping non-AI functions" },
  { href: "#wrapping-values", label: "Wrapping existing values" },
  { href: "#error-handling", label: "Error handling" },
  { href: "#api-reference", label: "REST API reference" },
  { href: "#webhooks", label: "Webhooks" },
  { href: "#env-vars", label: "Environment variables" },
  { href: "#configuration", label: "Configuration" },
];

const resultFields = [
  { field: "output", type: "str", desc: "Clean AI response — pass this to your user." },
  { field: "trust_score", type: "int", desc: "0–100 composite trust score." },
  { field: "flags", type: "list[str]", desc: "Detected bias flags, e.g. proxy_language_detected." },
  { field: "explanation", type: "str", desc: "Plain-language rationale for the output." },
  { field: "audit", type: "dict", desc: "Full reasoning chain JSON with all 5 stage outputs." },
  { field: "context_type", type: "str", desc: "Active context: hiring, lending, content, or healthcare." },
];

const pipelineStages = [
  {
    n: "1",
    title: "Intent extraction",
    body: "Detects what the model is trying to do, the context type (hiring, lending, etc.), and which demographic signals matter for this decision.",
  },
  {
    n: "2",
    title: "Fairness baseline load",
    body: "Loads the versioned Nigerian demographic baseline for the active context. Baselines account for ethnic diversity, regional economic disparity, and gender dynamics in Nigerian professional contexts.",
  },
  {
    n: "3",
    title: "Bias pattern match",
    body: "Checks the response against known bias patterns, proxy terms, and explanation confidence gaps. Flags are added to the result if patterns match.",
  },
  {
    n: "4",
    title: "Explanation generation",
    body: "Produces a plain-language explanation using Claude. This explanation is what your stakeholders will read — it needs to be coherent, specific, and defensible.",
  },
  {
    n: "5",
    title: "Trust synthesis",
    body: "Computes the 0–100 trust score from all stage signals. Weighted: bias (40%), explanation confidence (30%), intent alignment (20%), historical consistency (10%).",
  },
];

export default function DocsPage() {
  return (
    <div className="min-h-dvh bg-[#fdfcfc] text-slate-950 dark:bg-[#100a0b] dark:text-slate-50">
      {/* ── Header ── */}
      <header className="sticky top-0 z-30 border-b border-rose-950/10 bg-[#fdfcfc]/90 backdrop-blur-md dark:border-white/10 dark:bg-[#100a0b]/90">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-700 font-display text-sm font-semibold text-white shadow-sm">
              V
            </span>
            <span className="font-display text-sm font-semibold tracking-[0.24em] text-rose-800 dark:text-rose-300">
              VERDANT
            </span>
          </Link>

          <nav aria-label="Docs navigation" className="hidden items-center gap-6 text-sm font-medium text-slate-600 dark:text-slate-300 md:flex">
            <Link href="/" className="transition-colors hover:text-rose-800 dark:hover:text-white">
              Home
            </Link>
            <Link href="/#how-it-works" className="transition-colors hover:text-rose-800 dark:hover:text-white">
              How it works
            </Link>
            <span className="font-semibold text-rose-700 dark:text-rose-400">Docs</span>
          </nav>

          <Link
            href="/overview"
            className="inline-flex min-h-9 items-center gap-2 rounded-lg bg-rose-700 px-4 py-2 text-sm font-semibold text-white transition-transform duration-300 hover:-translate-y-0.5 hover:bg-rose-800"
          >
            Dashboard
            <ArrowIcon className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
        <div className="lg:grid lg:grid-cols-[220px_1fr] lg:gap-12 xl:grid-cols-[240px_1fr]">
          {/* ── Table of contents ── */}
          <aside className="hidden lg:block">
            <div className="sticky top-24 space-y-0.5">
              <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                On this page
              </p>
              {tocItems.map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  className="block rounded-lg px-3 py-2 text-sm text-slate-600 transition-colors hover:bg-rose-50 hover:text-rose-800 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-white"
                >
                  {label}
                </Link>
              ))}
            </div>
          </aside>

          {/* ── Main content ── */}
          <main className="min-w-0">
            {/* Page header */}
            <div className="mb-10 border-b border-rose-950/10 pb-8 dark:border-white/10">
              <div className="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-300">
                <BookIcon className="h-3.5 w-3.5" aria-hidden="true" />
                Getting started
              </div>
              <h1 className="mt-4 font-display text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl">
                VERDANT SDK
              </h1>
              <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-300">
                A lightweight, NDPR-native SDK that wraps any AI integration
                and returns a structured reasoning chain — bias flags,
                plain-language explanations, and a trust score.
              </p>
            </div>

            <div className="space-y-16">
              {/* ── Overview ── */}
              <section id="overview">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Overview
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  VERDANT is designed for Nigerian and African developers
                  shipping AI into high-stakes contexts. Every AI call passes
                  through a 5-stage reasoning pipeline that produces structured,
                  auditable outputs — no freestyle AI responses, no hidden
                  reasoning.
                </p>
                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  {[
                    {
                      title: "Drop-in wrapper",
                      body: "Wrap OpenAI, Anthropic, or Gemini calls without rewriting your product flow.",
                    },
                    {
                      title: "Nigerian baselines",
                      body: "Fairness baselines tuned to local demographic reality, not imported Western defaults.",
                    },
                    {
                      title: "Compliance trail",
                      body: "Persist audit payloads, export NDPR-ready reports, and send webhook alerts.",
                    },
                    {
                      title: "Readable by anyone",
                      body: "Give non-technical reviewers a plain-language explanation instead of model internals.",
                    },
                  ].map(({ title, body }) => (
                    <div
                      key={title}
                      className="rounded-lg border border-rose-950/10 bg-white p-4 dark:border-white/10 dark:bg-white/5"
                    >
                      <p className="font-semibold text-slate-900 dark:text-white">{title}</p>
                      <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                        {body}
                      </p>
                    </div>
                  ))}
                </div>
              </section>

              {/* ── Installation ── */}
              <section id="installation">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Installation
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  Install the VERDANT Python SDK using pip. Requires Python
                  3.11+.
                </p>
                <div className="mt-4 overflow-hidden rounded-lg bg-slate-950">
                  <div className="flex items-center gap-3 px-5 py-3.5">
                    <span className="select-none font-mono text-slate-500">$</span>
                    <code className="font-mono text-sm text-emerald-300">
                      pip install verdant
                    </code>
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
                  Dependencies:{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-white/10">
                    httpx
                  </code>
                  ,{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-white/10">
                    pydantic
                  </code>
                  ,{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-white/10">
                    anthropic
                  </code>
                  .
                </p>
              </section>

              {/* ── API keys ── */}
              <section id="api-keys">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  API keys
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  Your VERDANT API key authenticates every SDK and REST call.
                  Generate one from the dashboard — open{" "}
                  <Link
                    href="/settings"
                    className="font-semibold text-rose-700 underline-offset-2 hover:underline dark:text-rose-400"
                  >
                    Settings → API keys
                  </Link>{" "}
                  and click <strong>Generate key</strong>. Pass it to the client
                  as{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    api_key
                  </code>{" "}
                  or set{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    VERDANT_API_KEY
                  </code>
                  .
                </p>
                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  {[
                    { title: "Shown once", body: "The full vd_live_ key is displayed a single time at creation. Copy it immediately." },
                    { title: "Hashed at rest", body: "Only a prefix and a SHA-256 hash are stored — VERDANT can never show the key again." },
                    { title: "Regenerate anytime", body: "Regenerating revokes the old key immediately and issues a fresh one. Update your env after." },
                  ].map(({ title, body }) => (
                    <div
                      key={title}
                      className="rounded-lg border border-rose-950/10 bg-white p-4 dark:border-white/10 dark:bg-white/5"
                    >
                      <p className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
                        <ShieldIcon className="h-4 w-4 text-rose-700 dark:text-rose-400" aria-hidden="true" />
                        {title}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                        {body}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-6 py-5 dark:border-amber-500/20 dark:bg-amber-500/10">
                  <p className="font-semibold text-amber-800 dark:text-amber-300">
                    Lost your key?
                  </p>
                  <p className="mt-2 text-sm leading-7 text-amber-700/80 dark:text-amber-300/70">
                    Keys can&apos;t be recovered — only regenerated. Use{" "}
                    <strong>Regenerate key</strong> in Settings, then update{" "}
                    <code className="rounded bg-amber-100 px-1.5 py-0.5 text-xs dark:bg-amber-500/20">
                      VERDANT_API_KEY
                    </code>{" "}
                    everywhere it&apos;s used. The previous key stops working the
                    moment you regenerate.
                  </p>
                </div>
              </section>

              {/* ── Quick start ── */}
              <section id="quickstart">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Quick start
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  Wrap your existing AI call. VERDANT intercepts the request,
                  runs the 5-stage pipeline, and returns the clean output
                  alongside a full audit payload. This runs the pipeline{" "}
                  <strong>in-process</strong> using your provider keys.
                </p>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-400">
                      Python
                    </span>
                    <span className="font-mono text-xs text-slate-500">
                      verdant_example.py
                    </span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                    <code>{codeSample}</code>
                  </pre>
                </div>
              </section>

              {/* ── Hosted mode ── */}
              <section id="hosted-mode">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Hosted mode (SaaS)
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  Set{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    base_url
                  </code>{" "}
                  (or the{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    VERDANT_API_URL
                  </code>{" "}
                  env var) and the SDK runs the pipeline on your VERDANT
                  deployment over HTTP via{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    client.run()
                  </code>
                  . Provider keys (Claude, Gemini) stay server-side — managed
                  from the dashboard — so your app only carries a VERDANT key.
                  Leave{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    base_url
                  </code>{" "}
                  unset to run in-process with{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    wrap()
                  </code>
                  .
                </p>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-400">
                      Python
                    </span>
                    <span className="font-mono text-xs text-slate-500">
                      hosted_example.py
                    </span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                    <code>{hostedSample}</code>
                  </pre>
                </div>
                <div className="mt-6 grid gap-4 sm:grid-cols-3">
                  <div className="rounded-lg border border-rose-950/10 bg-white p-5 dark:border-white/10 dark:bg-white/5">
                    <p className="font-semibold text-slate-900 dark:text-white">
                      wrap() — in-process
                    </p>
                    <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                      Runs the pipeline in your own process and wraps a local
                      callable. You supply the provider keys. Best for local
                      development and self-hosted workloads.
                    </p>
                  </div>
                  <div className="rounded-lg border border-rose-950/10 bg-white p-5 dark:border-white/10 dark:bg-white/5">
                    <p className="font-semibold text-slate-900 dark:text-white">
                      run() — hosted
                    </p>
                    <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                      Sends the input to your VERDANT API, which generates and
                      analyses the output with server-side provider keys and logs
                      the audit to the dashboard.
                    </p>
                  </div>
                  <div className="rounded-lg border border-rose-950/10 bg-white p-5 dark:border-white/10 dark:bg-white/5">
                    <p className="font-semibold text-slate-900 dark:text-white">
                      wrap(remote_analysis=True) — hybrid
                    </p>
                    <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                      Runs your own model call locally, then analyses the output
                      on the server with dashboard-managed keys — so you keep your
                      call but need no local provider keys.
                    </p>
                  </div>
                </div>
              </section>

              {/* ── Result object ── */}
              <section id="result-object">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Result object
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    client.wrap()
                  </code>{" "}
                  returns a structured{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    VerdantResult
                  </code>{" "}
                  object. All fields are always present.
                </p>
                <div className="mt-6 overflow-hidden rounded-lg border border-rose-950/10 dark:border-white/10">
                  <table className="w-full text-sm">
                    <thead className="border-b border-rose-950/10 bg-slate-50 dark:border-white/10 dark:bg-white/5">
                      <tr>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Field
                        </th>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Type
                        </th>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rose-950/5 dark:divide-white/5">
                      {resultFields.map(({ field, type, desc }) => (
                        <tr key={field} className="bg-white dark:bg-transparent">
                          <td className="px-5 py-3.5 font-mono text-xs font-semibold text-rose-700 dark:text-rose-400">
                            {field}
                          </td>
                          <td className="px-5 py-3.5 font-mono text-xs text-slate-500 dark:text-slate-400">
                            {type}
                          </td>
                          <td className="px-5 py-3.5 text-slate-600 dark:text-slate-300">
                            {desc}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* ── Context types ── */}
              <section id="context-types">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Context types
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  VERDANT uses context types to load the correct Nigerian
                  demographic baseline for each decision. Pass{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    context_type
                  </code>{" "}
                  when wrapping a call. If omitted, the pipeline infers it from
                  the input text.
                </p>
                <div className="mt-6 overflow-hidden rounded-lg border border-rose-950/10 dark:border-white/10">
                  <table className="w-full text-sm">
                    <thead className="border-b border-rose-950/10 bg-slate-50 dark:border-white/10 dark:bg-white/5">
                      <tr>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Type
                        </th>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Use case
                        </th>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Aliases
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rose-950/5 dark:divide-white/5">
                      {contextTypes.map(({ type, desc, aliases }) => (
                        <tr key={type} className="bg-white dark:bg-transparent">
                          <td className="px-5 py-3.5 font-mono text-xs font-semibold text-rose-700 dark:text-rose-400">
                            {type}
                          </td>
                          <td className="px-5 py-3.5 text-slate-600 dark:text-slate-300">
                            {desc}
                          </td>
                          <td className="px-5 py-3.5 font-mono text-xs text-slate-500 dark:text-slate-400">
                            {aliases}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 rounded-lg border border-sky-200 bg-sky-50 px-6 py-5 dark:border-sky-500/20 dark:bg-sky-500/10">
                  <p className="font-semibold text-sky-800 dark:text-sky-300">
                    Alias resolution
                  </p>
                  <p className="mt-2 text-sm leading-7 text-sky-700/80 dark:text-sky-300/70">
                    You can pass aliases like{" "}
                    <code className="rounded bg-sky-100 px-1.5 py-0.5 text-xs dark:bg-sky-500/20">
                      content_moderation
                    </code>{" "}
                    or{" "}
                    <code className="rounded bg-sky-100 px-1.5 py-0.5 text-xs dark:bg-sky-500/20">
                      moderation
                    </code>{" "}
                    and they&apos;ll resolve to{" "}
                    <code className="rounded bg-sky-100 px-1.5 py-0.5 text-xs dark:bg-sky-500/20">
                      content
                    </code>
                    . Unsupported values raise a{" "}
                    <code className="rounded bg-sky-100 px-1.5 py-0.5 text-xs dark:bg-sky-500/20">
                      ValueError
                    </code>
                    .
                  </p>
                </div>
              </section>

              {/* ── Pipeline stages ── */}
              <section id="pipeline-stages">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Pipeline stages
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  Every AI call passes through 5 stages. Each stage returns
                  structured JSON — no freestyle outputs. If a trust score looks
                  wrong, the stage outputs tell you exactly where the signal
                  came from.
                </p>
                <div className="mt-6 space-y-3">
                  {pipelineStages.map(({ n, title, body }) => (
                    <div
                      key={n}
                      className="flex gap-4 rounded-lg border border-rose-950/10 bg-white p-5 dark:border-white/10 dark:bg-white/5"
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-rose-700 text-sm font-bold text-white">
                        {n}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900 dark:text-white">
                          {title}
                        </p>
                        <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                          {body}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* ── Audit payload ── */}
              <section id="audit-payload">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Audit payload
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  Every pipeline run produces an{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    AuditPayload
                  </code>{" "}
                  accessible via{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    result.audit
                  </code>
                  . This is the full reasoning chain that gets persisted to
                  Supabase and powers the dashboard.
                </p>
                <div className="mt-6 overflow-hidden rounded-lg border border-rose-950/10 dark:border-white/10">
                  <table className="w-full text-sm">
                    <thead className="border-b border-rose-950/10 bg-slate-50 dark:border-white/10 dark:bg-white/5">
                      <tr>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Field
                        </th>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Type
                        </th>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rose-950/5 dark:divide-white/5">
                      {auditFields.map(({ field, type, desc }) => (
                        <tr key={field} className="bg-white dark:bg-transparent">
                          <td className="px-5 py-3.5 font-mono text-xs font-semibold text-rose-700 dark:text-rose-400">
                            {field}
                          </td>
                          <td className="px-5 py-3.5 font-mono text-xs text-slate-500 dark:text-slate-400">
                            {type}
                          </td>
                          <td className="px-5 py-3.5 text-slate-600 dark:text-slate-300">
                            {desc}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-400">
                      Python
                    </span>
                    <span className="font-mono text-xs text-slate-500">
                      audit_fields.py
                    </span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                    <code>{auditBreakdownSample}</code>
                  </pre>
                </div>
                <div className="mt-4 rounded-lg border border-violet-200 bg-violet-50 px-6 py-5 dark:border-violet-500/20 dark:bg-violet-500/10">
                  <p className="font-semibold text-violet-800 dark:text-violet-300">
                    Trust score breakdown
                  </p>
                  <p className="mt-2 text-sm leading-7 text-violet-700/80 dark:text-violet-300/70">
                    Access{" "}
                    <code className="rounded bg-violet-100 px-1.5 py-0.5 text-xs dark:bg-violet-500/20">
                      audit.stages.trust.score_breakdown
                    </code>{" "}
                    to see the per-signal scores. The trust score is a weighted
                    composite: bias signal strength (40%), explanation confidence
                    (30%), intent alignment (20%), and historical pattern
                    consistency (10%).
                  </p>
                </div>
              </section>

              {/* ── Wrapping non-AI functions ── */}
              <section id="wrapping-non-ai">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Wrapping non-AI functions
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  VERDANT doesn&apos;t care how the output was generated. You can
                  wrap legacy rules engines, deterministic scoring functions, or
                  any callable that makes a high-stakes decision. The pipeline
                  evaluates the relationship between input and output —
                  not the source.
                </p>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-400">
                      Python
                    </span>
                    <span className="font-mono text-xs text-slate-500">
                      non_ai_example.py
                    </span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                    <code>{nonAiSample}</code>
                  </pre>
                </div>
                <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 px-6 py-5 dark:border-amber-500/20 dark:bg-amber-500/10">
                  <p className="font-semibold text-amber-800 dark:text-amber-300">
                    Why wrap non-AI logic?
                  </p>
                  <p className="mt-2 text-sm leading-7 text-amber-700/80 dark:text-amber-300/70">
                    Many high-stakes systems in Nigerian fintech, HR-tech, and
                    health-tech still use deterministic rules or heuristics. These
                    can encode demographic bias just like an LLM can. VERDANT
                    gives you the same inspectability, audit trail, and NDPR
                    compliance for any decision-making function.
                  </p>
                </div>
              </section>

              {/* ── Wrapping existing values ── */}
              <section id="wrapping-values">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Wrapping existing values
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  If you already have the AI output as a string or object and
                  just want VERDANT to audit it, wrap it in a lambda or a simple
                  function. Don&apos;t pass a raw value directly to{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    fn
                  </code>
                  {" "}— it expects a callable.
                </p>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-400">
                      Python
                    </span>
                    <span className="font-mono text-xs text-slate-500">
                      wrap_existing_value.py
                    </span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                    <code>{rawValueSample}</code>
                  </pre>
                </div>
                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-5 py-4 dark:border-emerald-500/20 dark:bg-emerald-500/10">
                    <p className="flex items-center gap-2 font-semibold text-emerald-800 dark:text-emerald-300">
                      <CheckIcon className="h-4 w-4" aria-hidden="true" />
                      Do this
                    </p>
                    <p className="mt-2 text-sm leading-6 text-emerald-700/80 dark:text-emerald-300/70">
                      <code className="rounded bg-emerald-100 px-1.5 py-0.5 text-xs dark:bg-emerald-500/20">
                        fn=lambda **kwargs: my_value
                      </code>
                    </p>
                  </div>
                  <div className="rounded-lg border border-red-200 bg-red-50 px-5 py-4 dark:border-red-500/20 dark:bg-red-500/10">
                    <p className="flex items-center gap-2 font-semibold text-red-800 dark:text-red-300">
                      <ShieldIcon className="h-4 w-4" aria-hidden="true" />
                      Don&apos;t do this
                    </p>
                    <p className="mt-2 text-sm leading-6 text-red-700/80 dark:text-red-300/70">
                      <code className="rounded bg-red-100 px-1.5 py-0.5 text-xs dark:bg-red-500/20">
                        fn=my_value
                      </code>{" "}
                      — crashes with{" "}
                      <code className="rounded bg-red-100 px-1.5 py-0.5 text-xs dark:bg-red-500/20">
                        TypeError
                      </code>
                    </p>
                  </div>
                </div>
              </section>

              {/* ── Error handling ── */}
              <section id="error-handling">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Error handling
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  If the wrapped function throws an exception, VERDANT catches it
                  gracefully. Your application stays up. The pipeline still runs
                  and records a full audit — but the trust score is capped and
                  the risk level is set to critical.
                </p>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-400">
                      Python
                    </span>
                    <span className="font-mono text-xs text-slate-500">
                      error_handling.py
                    </span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                    <code>{errorHandlingSample}</code>
                  </pre>
                </div>
                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  {[
                    { label: "Trust score", value: "≤ 15", note: "Capped to critical threshold" },
                    { label: "Risk level", value: "critical", note: "Always set on failure" },
                    { label: "Output", value: "Empty string", note: "No upstream data available" },
                  ].map(({ label, value, note }) => (
                    <div
                      key={label}
                      className="rounded-lg border border-rose-950/10 bg-white p-4 dark:border-white/10 dark:bg-white/5"
                    >
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                        {label}
                      </p>
                      <p className="mt-1 font-display text-xl font-semibold text-rose-700 dark:text-rose-400">
                        {value}
                      </p>
                      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                        {note}
                      </p>
                    </div>
                  ))}
                </div>
              </section>

              {/* ── REST API reference ── */}
              <section id="api-reference">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  REST API reference
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  If you&apos;re integrating via HTTP instead of the Python SDK,
                  the FastAPI backend exposes these endpoints. Each one requires
                  your VERDANT API key as a{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    Authorization: Bearer
                  </code>{" "}
                  header. All responses use a consistent envelope:{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    {"{ data, meta, error }"}
                  </code>
                </p>
                <div className="mt-6 overflow-hidden rounded-lg border border-rose-950/10 dark:border-white/10">
                  <table className="w-full text-sm">
                    <thead className="border-b border-rose-950/10 bg-slate-50 dark:border-white/10 dark:bg-white/5">
                      <tr>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Method
                        </th>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Endpoint
                        </th>
                        <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rose-950/5 dark:divide-white/5">
                      {apiEndpoints.map(({ method, path, desc }) => (
                        <tr key={path} className="bg-white dark:bg-transparent">
                          <td className="px-5 py-3.5">
                            <span
                              className={`inline-flex rounded px-2 py-0.5 text-xs font-bold ${
                                method === "POST"
                                  ? "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300"
                                  : "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300"
                              }`}
                            >
                              {method}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 font-mono text-xs font-semibold text-rose-700 dark:text-rose-400">
                            {path}
                          </td>
                          <td className="px-5 py-3.5 text-slate-600 dark:text-slate-300">
                            {desc}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-400">
                      cURL
                    </span>
                    <span className="font-mono text-xs text-slate-500">
                      examples
                    </span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                    <code>{apiCurlSample}</code>
                  </pre>
                </div>
              </section>

              {/* ── Webhooks ── */}
              <section id="webhooks">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Webhooks
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  When a pipeline result falls below your configured trust score
                  threshold (default: 40), VERDANT automatically dispatches a
                  signed webhook POST to all active endpoints. Each webhook is
                  HMAC-SHA256 signed so you can verify authenticity.
                </p>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-400">
                      JSON
                    </span>
                    <span className="font-mono text-xs text-slate-500">
                      webhook_payload.json
                    </span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                    <code>{webhookPayloadSample}</code>
                  </pre>
                </div>
                <div className="mt-6 space-y-3">
                  {[
                    {
                      title: "HMAC-SHA256 signing",
                      body: "Every webhook payload is signed with your WEBHOOK_SECRET. Verify the X-Verdant-Signature header to confirm the request came from VERDANT.",
                    },
                    {
                      title: "Per-webhook thresholds",
                      body: "Each webhook endpoint can have its own min_trust_score threshold. A webhook with threshold 60 will fire more often than one set to 20.",
                    },
                    {
                      title: "Manual dispatch",
                      body: "Use POST /webhooks/dispatch?audit_id=...&force=true to re-send webhooks for any audit, even if the trust score is above threshold.",
                    },
                  ].map(({ title, body }) => (
                    <div
                      key={title}
                      className="flex gap-4 rounded-lg border border-rose-950/10 bg-white p-5 dark:border-white/10 dark:bg-white/5"
                    >
                      <div className="mt-0.5">
                        <PulseIcon className="h-5 w-5 text-rose-700 dark:text-rose-400" aria-hidden="true" />
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900 dark:text-white">
                          {title}
                        </p>
                        <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                          {body}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* ── Environment variables ── */}
              <section id="env-vars">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Environment variables
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  Copy{" "}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm dark:bg-white/10">
                    .env.example
                  </code>{" "}
                  from the repo root and populate with your credentials.
                </p>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="border-b border-white/10 px-5 py-3">
                    <span className="font-mono text-xs text-slate-500">.env</span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-300">
                    <code>{envVars}</code>
                  </pre>
                </div>
              </section>

              {/* ── Configuration ── */}
              <section id="configuration" className="pb-20">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Configuration
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  The SDK reads from environment variables by default. Pass a
                  config object to the client for per-deployment overrides.
                </p>
                <div className="mt-4 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-400">
                      Python
                    </span>
                  </div>
                  <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                    <code>{configSample}</code>
                  </pre>
                </div>

                <div className="mt-8 rounded-lg border border-rose-100 bg-rose-50 px-6 py-5 dark:border-rose-500/20 dark:bg-rose-500/10">
                  <p className="font-semibold text-rose-800 dark:text-rose-300">
                    Trust score alert threshold
                  </p>
                  <p className="mt-2 text-sm leading-7 text-rose-700/80 dark:text-rose-300/70">
                    The default threshold is{" "}
                    <strong className="text-rose-800 dark:text-rose-300">40</strong>.
                    Outputs with trust scores below this value trigger a webhook
                    POST to your configured endpoint. Lower it to catch more
                    edge cases; raise it in high-volume contexts where you want
                    fewer alerts.
                  </p>
                </div>
              </section>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
