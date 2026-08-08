import { FileTextIcon } from "@/components/icons";
import { DashboardShell } from "@/components/dashboard-shell";
import { DataNotice } from "@/components/data-notice";
import { getNdprReport } from "@/lib/server-api";
import { titleCaseContext } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ReportsPage() {
  const result = await getNdprReport(30);
  const report = result.ok ? result.data : null;

  const contexts = report ? Object.entries(report.by_context_type) : [];
  const flags = report ? Object.entries(report.flag_counts) : [];

  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-display text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
              Reports
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Export NDPR-ready compliance summaries for stakeholders · last 30 days
            </p>
          </div>
          {report && (
            <a
              href="/api/reports/ndpr?days=30"
              className="inline-flex min-h-10 items-center gap-2 self-start rounded-lg bg-rose-700 px-4 py-2.5 text-sm font-semibold text-white transition-transform duration-300 hover:-translate-y-0.5 hover:bg-rose-800"
            >
              <FileTextIcon className="h-4 w-4" aria-hidden="true" />
              Export NDPR report (JSON)
            </a>
          )}
        </div>

        {!result.ok && <DataNotice result={result} />}

        {report && (
          <>
            {/* Live summary tiles */}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                {
                  label: "Audits in window",
                  value: report.total_audits.toLocaleString(),
                  sub: `${report.available_audits.toLocaleString()} on record`,
                },
                {
                  label: "Average trust score",
                  value: report.average_trust_score != null ? `${report.average_trust_score}` : "—",
                  sub: report.average_trust_score != null ? "out of 100" : "no data yet",
                },
                {
                  label: "Low-trust decisions",
                  value: report.low_trust_decisions.toLocaleString(),
                  sub: "below alert threshold",
                },
                {
                  label: "Distinct bias flags",
                  value: flags.length.toLocaleString(),
                  sub: `${flags.reduce((n, [, c]) => n + c, 0)} occurrences`,
                },
              ].map((tile) => (
                <div
                  key={tile.label}
                  className="rounded-lg border border-rose-950/10 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/5"
                >
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{tile.label}</p>
                  <p className="mt-2 font-display text-3xl font-semibold text-slate-950 dark:text-white">
                    {tile.value}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">{tile.sub}</p>
                </div>
              ))}
            </div>

            {/* Breakdown cards */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-rose-950/10 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/5">
                <div className="flex items-center gap-3">
                  <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400">
                    <FileTextIcon className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <h2 className="font-display text-lg font-semibold text-slate-950 dark:text-white">
                    Decisions by context
                  </h2>
                </div>
                <div className="mt-4 space-y-2">
                  {contexts.length > 0 ? (
                    contexts.map(([ctx, count]) => (
                      <div key={ctx} className="flex items-center justify-between text-sm">
                        <span className="text-slate-600 dark:text-slate-300">{titleCaseContext(ctx)}</span>
                        <span className="font-mono text-slate-900 dark:text-white">{count}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-400">No decisions recorded in this window yet.</p>
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-rose-950/10 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/5">
                <div className="flex items-center gap-3">
                  <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400">
                    <FileTextIcon className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <h2 className="font-display text-lg font-semibold text-slate-950 dark:text-white">
                    Top bias flags
                  </h2>
                </div>
                <div className="mt-4 space-y-2">
                  {flags.length > 0 ? (
                    flags.slice(0, 6).map(([flag, count]) => (
                      <div key={flag} className="flex items-center justify-between text-sm">
                        <span className="font-mono text-rose-600 dark:text-rose-400">{flag}</span>
                        <span className="font-mono text-slate-900 dark:text-white">{count}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-400">No bias flags raised in this window — clean run.</p>
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {/* NDPR info panel */}
        <div className="rounded-lg border border-rose-950/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-rose-700 dark:text-rose-400">
            NDPR compliance
          </p>
          <h2 className="mt-3 font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Every report is audit-ready.
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            VERDANT exports include timestamps, context types, trust scores, bias
            flags, and the plain-language explanations generated for each decision.
            Each report meets the documentation requirements under the Nigeria Data
            Protection Regulation.
          </p>
        </div>
      </div>
    </DashboardShell>
  );
}
