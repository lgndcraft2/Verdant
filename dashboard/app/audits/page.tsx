import { DashboardShell } from "@/components/dashboard-shell";
import { DataNotice, EmptyState } from "@/components/data-notice";
import { getAudits } from "@/lib/server-api";
import { auditTitle, formatTimestamp, titleCaseContext } from "@/lib/format";

export const dynamic = "force-dynamic";

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

export default async function AuditsPage() {
  const result = await getAudits(50, 0);

  const audits = result.ok
    ? result.data.items.map((a) => ({
        id: a.id ?? a.audit_id ?? "",
        title: auditTitle(a.stages?.intent?.detected_intent, a.input_text),
        context: titleCaseContext(a.context_type),
        score: a.trust_score ?? 0,
        flag: a.flags && a.flags.length > 0 ? a.flags.join(", ") : null,
        note: a.explanation || "No explanation recorded for this decision.",
        model: a.model_name ?? "—",
        timestamp: formatTimestamp(a.created_at),
      }))
    : [];

  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-display text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
              Audit explorer
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Review decisions by score, context type, and explanation quality
            </p>
          </div>
          {result.ok && (
            <span className="self-start rounded-lg border border-rose-950/10 bg-white px-3 py-2 text-xs font-medium text-slate-500 shadow-sm dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
              {result.data.total.toLocaleString()} total · showing {audits.length}
            </span>
          )}
        </div>

        {!result.ok && <DataNotice result={result} />}
        {result.ok && audits.length === 0 && (
          <EmptyState message="No audits yet — run a decision through the SDK (client.run / client.wrap) and it will appear here." />
        )}

        {/* Audit list */}
        {audits.length > 0 && (
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
                          className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${contextColors[audit.context] ?? "bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300"}`}
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
                    <p className="font-mono text-xs text-slate-400">{audit.id.slice(0, 10)}</p>
                    <p className="text-xs text-slate-400">{audit.timestamp}</p>
                    <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs text-slate-500 dark:bg-white/10 dark:text-slate-400">
                      {audit.model}
                    </span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
