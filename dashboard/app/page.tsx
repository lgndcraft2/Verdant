import Link from "next/link";
import {
  ArrowIcon,
  CheckIcon,
  PulseIcon,
  ShieldIcon,
  TraceIcon,
  BookIcon,
} from "@/components/icons";

const stats = [
  { value: "5 stages", label: "every AI call becomes inspectable" },
  { value: "0 freestyle", label: "structured JSON at every step" },
  { value: "40 threshold", label: "webhooks fire below this score" },
  { value: "NDPR-native", label: "audit logs built for local compliance" },
];

const stages = [
  {
    n: "01",
    icon: TraceIcon,
    title: "Intent extraction",
    body: "Detects what the model is trying to do, the context type, and the signals that matter for the decision.",
  },
  {
    n: "02",
    icon: ShieldIcon,
    title: "Fairness baseline",
    body: "Loads the Nigerian demographic baseline for the active context: hiring, lending, content, or healthcare.",
  },
  {
    n: "03",
    icon: PulseIcon,
    title: "Bias pattern match",
    body: "Checks the response against known bias patterns, proxy terms, and explanation confidence.",
  },
  {
    n: "04",
    icon: CheckIcon,
    title: "Plain-language explanation",
    body: "Produces a human-readable reason for the output, so teams can defend the decision in plain English.",
  },
];

const useCases = [
  {
    title: "Hiring",
    body: "Screen candidate messages, shortlist summaries, and interview notes for proxy bias and explanation gaps.",
  },
  {
    title: "Lending",
    body: "Review approval language for geography, income, and class proxies before a credit decision ships.",
  },
  {
    title: "Content moderation",
    body: "Make moderation logic consistent, explainable, and less likely to over-penalize identity or dialect.",
  },
  {
    title: "Healthcare",
    body: "Highlight low-confidence outputs and safety ambiguity before an answer is treated like advice.",
  },
];

const codeSample = String.raw`from verdant import VerdantClient

client = VerdantClient(api_key="vd_live_...")

result = await client.wrap(
    fn=openai.chat.completions.create,
    context_type="hiring",
    input_text=user_prompt,
    model="gpt-4o",
    messages=[{"role": "user", "content": user_prompt}],
)

print(result.output)        # Clean AI response
print(result.trust_score)   # 0–100
print(result.flags)         # ["proxy_language_detected"]
print(result.explanation)   # Plain-language rationale`;

export default function Home() {
  return (
    <main className="relative min-h-dvh overflow-hidden bg-[#fdfcfc] text-slate-950 dark:bg-[#100a0b] dark:text-slate-50">
      {/* Background decoration */}
      <div className="absolute inset-0 -z-10 bg-hero-grid bg-[length:56px_56px] opacity-[0.1] [mask-image:linear-gradient(to_bottom,black,transparent_92%)]" />
      <div className="absolute left-[-10rem] top-[-8rem] -z-10 h-80 w-80 rounded-full bg-rose-500/12 blur-3xl" />
      <div className="absolute right-[-6rem] top-40 -z-10 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl" />
      <div className="absolute bottom-0 left-1/3 -z-10 h-96 w-96 rounded-full bg-rose-600/8 blur-3xl" />

      {/* ── Header ──────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 border-b border-rose-950/10 bg-[#fdfcfc]/90 backdrop-blur-md dark:border-white/10 dark:bg-[#100a0b]/90">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-rose-700 font-display text-lg font-semibold text-white shadow-sm">
              V
            </span>
            <span>
              <span className="block font-display text-base font-semibold tracking-[0.24em] text-rose-800 dark:text-rose-300">
                VERDANT
              </span>
              <span className="block text-xs font-medium uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
                Inspectable AI governance
              </span>
            </span>
          </Link>

          <nav aria-label="Primary" className="hidden items-center gap-7 text-sm font-medium text-slate-600 dark:text-slate-300 md:flex">
            <Link href="#how-it-works" className="transition-colors hover:text-rose-800 dark:hover:text-white">
              How it works
            </Link>
            <Link href="#use-cases" className="transition-colors hover:text-rose-800 dark:hover:text-white">
              Use cases
            </Link>
            <Link href="#developers" className="transition-colors hover:text-rose-800 dark:hover:text-white">
              SDK
            </Link>
            <Link href="/docs" className="transition-colors hover:text-rose-800 dark:hover:text-white">
              Docs
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/overview"
              className="hidden min-h-11 items-center rounded-lg border border-rose-950/10 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors duration-300 hover:border-rose-500 hover:text-rose-800 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:text-white sm:inline-flex"
            >
              Dashboard
            </Link>
            <Link
              href="/docs"
              className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-rose-700 px-5 py-3 text-sm font-semibold text-white transition-transform duration-300 hover:-translate-y-0.5 hover:bg-rose-800 dark:bg-rose-600 dark:hover:bg-rose-500"
            >
              Read the docs
              <ArrowIcon className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ────────────────────────────────────────────── */}
      <section className="mx-auto max-w-7xl px-6 pb-16 pt-10 lg:px-8 lg:pb-24 lg:pt-16">
        <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
          {/* Left: copy + stats */}
          <div className="space-y-7">
            <div className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-800 shadow-sm dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300">
              <ShieldIcon className="h-4 w-4" aria-hidden="true" />
              NDPR-native accountability for AI teams
            </div>

            <div className="space-y-5">
              <h1 className="max-w-3xl font-display text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl lg:text-6xl">
                Make every AI decision{" "}
                <span className="bg-gradient-to-r from-rose-700 via-rose-500 to-emerald-600 bg-clip-text text-transparent">
                  inspectable
                </span>
                .
              </h1>
              <p className="max-w-2xl text-base leading-8 text-slate-600 dark:text-slate-300 sm:text-lg">
                VERDANT wraps any AI call and returns a structured reasoning
                chain: intent, fairness baseline, bias flags, a plain-language
                explanation, and a trust score. Built for Nigerian and African
                builders shipping AI into high-stakes contexts.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <Link
                href="/docs"
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-rose-700 px-5 py-3 text-sm font-semibold text-white shadow-sm transition-transform duration-300 hover:-translate-y-0.5 hover:bg-rose-800 dark:bg-rose-600 dark:hover:bg-rose-500"
              >
                Read the docs
                <ArrowIcon className="h-4 w-4" aria-hidden="true" />
              </Link>
              <Link
                href="/overview"
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-rose-950/10 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors duration-300 hover:border-rose-400 hover:text-rose-800 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:text-white"
              >
                View dashboard
              </Link>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-lg border border-rose-950/10 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-white/5"
                >
                  <p className="font-display text-xl font-semibold tracking-tight text-rose-800 dark:text-rose-300">
                    {stat.value}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Right: live audit card mock */}
          <div className="relative">
            <div className="absolute -left-4 top-8 -z-10 hidden h-20 w-20 rounded-lg border border-rose-100 bg-white shadow-sm dark:border-white/10 dark:bg-white/5 lg:block" />
            <div className="absolute -right-4 bottom-8 -z-10 hidden h-24 w-24 rounded-full bg-emerald-500/15 blur-2xl lg:block" />

            <div className="overflow-hidden rounded-xl border border-rose-950/10 bg-white shadow-soft dark:border-white/10 dark:bg-white/[0.04]">
              {/* Gradient top bar */}
              <div className="h-0.5 bg-gradient-to-r from-rose-600 via-rose-400 to-emerald-500" />

              {/* Audit header */}
              <div className="border-b border-slate-100 px-5 py-4 dark:border-white/10">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs text-slate-400 dark:text-slate-500">
                      audit_id: vd_a7f3c91
                    </p>
                    <p className="mt-0.5 text-sm font-semibold text-slate-900 dark:text-white">
                      Candidate Shortlist · Hiring
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-display text-4xl font-semibold leading-none text-emerald-600 dark:text-emerald-400">
                      84
                    </p>
                    <p className="mt-1 text-xs text-slate-400">/ 100 trust</p>
                  </div>
                </div>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-white/10">
                  <div
                    className="h-1.5 rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400"
                    style={{ width: "84%" }}
                  />
                </div>
              </div>

              {/* Pipeline stages */}
              <div className="space-y-2 px-5 py-4">
                {[
                  { n: "01", label: "Intent", detail: "Hiring — candidate review", ok: true },
                  { n: "02", label: "Baseline", detail: "NG hiring baseline v2.1", ok: true },
                  { n: "03", label: "Bias", detail: "2 proxy signals detected", ok: false },
                  { n: "04", label: "Explain", detail: "Rationale generated", ok: true },
                  { n: "05", label: "Trust", detail: "Score synthesized → 84", ok: true },
                ].map(({ n, label, detail, ok }) => (
                  <div
                    key={n}
                    className="flex items-center gap-3 rounded-lg bg-slate-50 px-3 py-2.5 dark:bg-white/[0.03]"
                  >
                    <span className="w-6 shrink-0 font-mono text-xs font-bold text-slate-300 dark:text-slate-600">
                      {n}
                    </span>
                    <span
                      className={`inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-white ${
                        ok ? "bg-emerald-500" : "bg-amber-500"
                      }`}
                    >
                      {ok ? (
                        <CheckIcon className="h-3 w-3" aria-hidden="true" />
                      ) : (
                        <PulseIcon className="h-3 w-3" aria-hidden="true" />
                      )}
                    </span>
                    <div className="min-w-0 flex-1">
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                        {label}
                      </span>
                      <span className="ml-2 text-xs text-slate-400">{detail}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Flag */}
              <div className="px-5 pb-5">
                <div className="rounded-lg border border-rose-100 bg-rose-50 px-4 py-3 dark:border-rose-500/20 dark:bg-rose-500/10">
                  <p className="text-xs font-semibold text-rose-700 dark:text-rose-400">
                    ⚠ proxy_language_detected
                  </p>
                  <p className="mt-1.5 text-xs leading-5 text-rose-800/80 dark:text-rose-300/70">
                    "Role phrasing may disadvantage candidates outside Lagos.
                    Review 'fluent in Lagos tech scene' qualifier."
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────── */}
      <section
        id="how-it-works"
        className="mx-auto max-w-7xl px-6 pb-16 lg:px-8 lg:pb-24"
      >
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-rose-700 dark:text-rose-400">
              How it works
            </p>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
              A 5-stage reasoning chain, not a black box.
            </h2>
          </div>
          <p className="max-w-xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            Every stage returns structured JSON, so teams can see which signal
            changed the outcome instead of guessing why the model behaved a
            certain way.
          </p>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-4">
          {stages.map((stage) => {
            const Icon = stage.icon;
            return (
              <article
                key={stage.title}
                className="relative overflow-hidden rounded-lg border border-rose-950/10 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/5"
              >
                <div className="absolute right-4 top-4 font-display text-5xl font-semibold text-rose-100 dark:text-rose-950/60">
                  {stage.n}
                </div>
                <div className="inline-flex h-11 w-11 items-center justify-center rounded-lg bg-slate-950 text-white dark:bg-white dark:text-slate-950">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <h3 className="mt-6 font-display text-lg font-semibold tracking-tight text-slate-950 dark:text-white">
                  {stage.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
                  {stage.body}
                </p>
              </article>
            );
          })}
        </div>
      </section>

      {/* ── Use cases ───────────────────────────────────────── */}
      <section
        id="use-cases"
        className="mx-auto max-w-7xl px-6 pb-16 lg:px-8 lg:pb-24"
      >
        <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="rounded-lg bg-gradient-to-br from-emerald-800 to-emerald-950 p-8 text-white shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-100/80">
              Where VERDANT fits
            </p>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              Built for the decisions that need a paper trail.
            </h2>
            <p className="mt-4 max-w-prose text-sm leading-7 text-white/80 sm:text-base">
              Hiring, lending, content moderation, and healthcare all need the
              same thing: a defensible record of why the model produced a result.
            </p>

            <div className="mt-6 space-y-3">
              {[
                "Alert below threshold by webhook",
                "Export NDPR-ready reports",
                "Override per client or deployment",
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-3 backdrop-blur-sm"
                >
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white text-emerald-800">
                    <CheckIcon className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <span className="text-sm font-medium text-white">{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {useCases.map((useCase) => (
              <article
                key={useCase.title}
                className="rounded-lg border border-rose-950/10 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/5"
              >
                <div className="inline-flex h-11 w-11 items-center justify-center rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400">
                  <ShieldIcon className="h-5 w-5" aria-hidden="true" />
                </div>
                <h3 className="mt-4 font-display text-lg font-semibold tracking-tight text-slate-950 dark:text-white">
                  {useCase.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
                  {useCase.body}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ── SDK / Developer section ──────────────────────────── */}
      <section
        id="developers"
        className="mx-auto max-w-7xl px-6 pb-16 lg:px-8 lg:pb-24"
      >
        <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="rounded-lg border border-rose-950/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-rose-700 dark:text-rose-400">
              Developer experience
            </p>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
              Wrap the model call you already have.
            </h2>
            <p className="mt-4 text-sm leading-7 text-slate-600 dark:text-slate-300">
              The SDK keeps your integration surface small. You call your model,
              VERDANT returns the clean output plus the audit payload, and your
              app decides what to show or log.
            </p>

            <div className="mt-6 overflow-hidden rounded-lg border border-rose-950/10 bg-slate-950">
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
                <span className="text-xs font-semibold uppercase tracking-[0.24em] text-rose-400">
                  Example wrapper
                </span>
                <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-white/70">
                  Python SDK
                </span>
              </div>
              <pre className="overflow-x-auto p-5 text-sm leading-7 text-slate-100">
                <code>{codeSample}</code>
              </pre>
            </div>
          </div>

          <div className="space-y-4 rounded-lg border border-rose-950/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-rose-700 dark:text-rose-400">
                  What the dashboard shows
                </p>
                <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
                  A feed you can hand to compliance, product, and engineering.
                </h2>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-800 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300">
                Trust score alerts on
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {[
                "Audit logs with timestamps, context type, and stage outputs",
                "Trust score trends across deployments and model versions",
                "Bias flags and explanation confidence at a glance",
                "NDPR compliance exports for stakeholders",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-lg border border-rose-950/10 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5"
                >
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-rose-700 text-white">
                      <CheckIcon className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <p className="text-sm leading-7 text-slate-700 dark:text-slate-300">
                      {item}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA band ────────────────────────────────────────── */}
      <section
        id="cta"
        className="mx-auto max-w-7xl px-6 pb-20 lg:px-8 lg:pb-28"
      >
        <div className="relative overflow-hidden rounded-lg bg-slate-950 px-6 py-10 text-white shadow-sm sm:px-8 sm:py-12">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(225,29,72,0.20),transparent_32%),radial-gradient(circle_at_bottom_left,rgba(16,185,129,0.14),transparent_30%)]" />

          <div className="relative grid gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-rose-400">
                Ready to ship with guardrails
              </p>
              <h2 className="mt-3 max-w-2xl font-display text-3xl font-semibold tracking-tight sm:text-4xl lg:text-5xl">
                Put a trace behind every AI output before it reaches a user.
              </h2>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                VERDANT gives your team a practical way to explain, audit, and
                defend model-driven decisions without changing the product
                surface your users already know.
              </p>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/docs"
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-rose-600 px-6 py-3 text-sm font-semibold text-white transition-transform duration-300 hover:-translate-y-0.5 hover:bg-rose-500"
                >
                  Read the docs
                  <ArrowIcon className="h-4 w-4" aria-hidden="true" />
                </Link>
                <Link
                  href="/overview"
                  className="inline-flex min-h-11 items-center justify-center rounded-lg border border-white/20 bg-white/10 px-6 py-3 text-sm font-semibold text-white transition-colors duration-300 hover:bg-white/[0.15]"
                >
                  View dashboard
                </Link>
              </div>
            </div>

            {/* Install snippet */}
            <div className="rounded-lg border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
              <p className="mb-3 text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">
                Get started in seconds
              </p>
              <div className="space-y-2 font-mono text-sm">
                <div className="flex items-center gap-3 rounded-lg bg-white/5 px-4 py-3">
                  <span className="select-none text-slate-500">$</span>
                  <code className="text-emerald-300">pip install verdant</code>
                </div>
                <div className="flex items-center gap-3 rounded-lg bg-white/5 px-4 py-3">
                  <span className="select-none text-slate-500">$</span>
                  <code className="truncate text-emerald-300">
                    export VERDANT_API_KEY=vd_live_...
                  </code>
                </div>
              </div>
              <Link
                href="/docs"
                className="mt-4 flex items-center gap-2 text-sm font-medium text-slate-400 transition-colors hover:text-rose-400"
              >
                <BookIcon className="h-3.5 w-3.5" aria-hidden="true" />
                Read the full quickstart guide
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="border-t border-rose-950/10 bg-white/60 px-6 py-10 dark:border-white/10 dark:bg-white/5">
        <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-[1.2fr_0.8fr_0.8fr] lg:px-2">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-rose-700 font-display text-base font-semibold text-white">
                V
              </span>
              <div>
                <p className="font-display text-lg font-semibold tracking-[0.2em] text-rose-800 dark:text-rose-300">
                  VERDANT
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  Inspectable AI governance for African builders.
                </p>
              </div>
            </div>
            <p className="mt-4 max-w-md text-sm leading-7 text-slate-600 dark:text-slate-300">
              Drop-in accountability for high-stakes AI. Every call gets a
              trace, a score, and a plain-language explanation.
            </p>
          </div>

          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
              Product
            </p>
            <ul className="mt-4 space-y-3 text-sm text-slate-700 dark:text-slate-300">
              <li>
                <Link className="transition-colors hover:text-rose-800 dark:hover:text-rose-300" href="#how-it-works">
                  How it works
                </Link>
              </li>
              <li>
                <Link className="transition-colors hover:text-rose-800 dark:hover:text-rose-300" href="#use-cases">
                  Use cases
                </Link>
              </li>
              <li>
                <Link className="transition-colors hover:text-rose-800 dark:hover:text-rose-300" href="#developers">
                  SDK
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
              Platform
            </p>
            <ul className="mt-4 space-y-3 text-sm text-slate-700 dark:text-slate-300">
              <li>
                <Link className="transition-colors hover:text-rose-800 dark:hover:text-rose-300" href="/docs">
                  Documentation
                </Link>
              </li>
              <li>
                <Link className="transition-colors hover:text-rose-800 dark:hover:text-rose-300" href="/overview">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link className="transition-colors hover:text-rose-800 dark:hover:text-rose-300" href="/audits">
                  Audits
                </Link>
              </li>
              <li>
                <Link className="transition-colors hover:text-rose-800 dark:hover:text-rose-300" href="/reports">
                  Reports
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mx-auto mt-8 flex max-w-7xl flex-col gap-2 border-t border-rose-950/10 pt-6 text-sm text-slate-500 dark:border-white/10 dark:text-slate-400 lg:flex-row lg:items-center lg:justify-between">
          <p>© 2026 VERDANT. Built for inspectable AI.</p>
          <p>NDPR-native. Structured JSON only. No hidden reasoning.</p>
        </div>
      </footer>
    </main>
  );
}
