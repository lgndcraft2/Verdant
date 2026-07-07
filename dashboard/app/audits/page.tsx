import { DashboardShell } from "@/components/dashboard-shell";

const audits = [
  {
    id: "vd_a7f3c91",
    title: "Candidate shortlist review",
    context: "Hiring",
    score: 84,
    flag: "proxy_language_detected",
    note: "Role phrasing may disadvantage candidates outside Lagos. Review qualification language.",
    model: "gpt-4o",
    timestamp: "2026-07-07 · 11:31 WAT",
  },
  {
    id: "vd_b2e9d44",
    title: "Loan pre-approval batch",
    context: "Lending",
    score: 61,
    flag: "geographic_bias",
    note: "Bias signal above alert threshold. Webhook dispatched to configured endpoint.",
    model: "claude-sonnet-4-6",
    timestamp: "2026-07-07 · 11:19 WAT",
  },
  {
    id: "vd_c5f1a77",
    title: "Moderation queue pass",
    context: "Content",
    score: 91,
    flag: null,
    note: "Explanation confidence high and consistent across all moderated items.",
    model: "gpt-4o",
    timestamp: "2026-07-07 · 11:02 WAT",
  },
  {
    id: "vd_d8a4b12",
    title: "Symptom triage review",
    context: "Healthcare",
    score: 73,
    flag: "low_confidence",
    note: "Output below expert-review threshold for healthcare context. Escalation recommended.",
    model: "claude-sonnet-4-6",
    timestamp: "2026-07-07 · 10:44 WAT",
  },
];

function TrustBadge({ score }: { score: number }) {
  const classes =
    score >= 70
      ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-500/20"
      : score >= 40
      ? "bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/20"
      : "bg-rose-50 text-rose-700 ring-1 ring-rose-200 dark:bg-rose-500/10 dark:text-rose-400 dark:ring-rose-500/20";

  return (
    <span
      className={`inline-flex w-10 shrink-0 items-center justify-center rounded-lg py-1.5 text-sm font-bold ${classes}`}
    >
      {score}
    </span>
  );
}

const contextColors: Record<string, string> = {
  Hiring: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
  Lending: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
  Content: "bg-sky-50 text-sky-700 dark:bg-sky-500/10 dark:text-sky-300",
  Healthcare: "bg-violet-50 text-violet-700 dark:bg-violet-500/10 dark:text-violet-300",
};

export default function AuditsPage() {
  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Audit explorer
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Review decisions by score, context type, and explanation quality
          </p>
        </div>

        {/* Audit list */}
        <div className="space-y-3">
          {audits.map((audit) => (
            <article
              key={audit.id}
              className="rounded-lg border border-rose-950/10 bg-white shadow-sm dark:border-white/10 dark:bg-white/5"
            >
              <div className="flex flex-col gap-4 p-5 md:flex-row md:items-start">
                <div className="flex flex-1 min-w-0 items-start gap-4">
                  <TrustBadge score={audit.score} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${contextColors[audit.context]}`}
                      >
                        {audit.context}
                      </span>
                      <h2 className="font-display text-lg font-semibold text-slate-950 dark:text-white">
                        {audit.title}
                      </h2>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {audit.note}
                    </p>
                    {audit.flag && (
                      <p className="mt-2 font-mono text-xs font-medium text-rose-600 dark:text-rose-400">
                        ⚠ {audit.flag}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-4 md:flex-col md:items-end md:gap-1.5">
                  <p className="font-mono text-xs text-slate-400">{audit.id}</p>
                  <p className="text-xs text-slate-400">{audit.timestamp}</p>
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs text-slate-500 dark:bg-white/10 dark:text-slate-400">
                    {audit.model}
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
