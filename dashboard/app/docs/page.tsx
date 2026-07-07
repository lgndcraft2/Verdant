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

const envVars = `# Required
VERDANT_API_KEY=vd_live_...
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

const tocItems = [
  { href: "#overview", label: "Overview" },
  { href: "#installation", label: "Installation" },
  { href: "#quickstart", label: "Quick start" },
  { href: "#result-object", label: "Result object" },
  { href: "#pipeline-stages", label: "Pipeline stages" },
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

              {/* ── Quick start ── */}
              <section id="quickstart">
                <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  Quick start
                </h2>
                <p className="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
                  Wrap your existing AI call. VERDANT intercepts the request,
                  runs the 5-stage pipeline, and returns the clean output
                  alongside a full audit payload.
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
