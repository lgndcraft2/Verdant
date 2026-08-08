import { DashboardShell } from "@/components/dashboard-shell";
import { DataNotice, EmptyState } from "@/components/data-notice";
import { CheckIcon, PulseIcon, ShieldIcon, TraceIcon } from "@/components/icons";
import { getAudits, getNdprReport } from "@/lib/server-api";
import { auditTitle, relativeTime, titleCaseContext } from "@/lib/format";

export const dynamic = "force-dynamic";

const pipelineStages = [
  { n: "01", label: "Intent extraction", icon: TraceIcon, healthy: true },
  { n: "02", label: "Fairness baseline", icon: ShieldIcon, healthy: true },
  { n: "03", label: "Bias pattern match", icon: PulseIcon, healthy: true },
  { n: "04", label: "Explanation gen", icon: CheckIcon, healthy: true },
  { n: "05", label: "Trust synthesis", icon: CheckIcon, healthy: true },
];

function TrustBadge({ score }: { score: number }) {
  const classes =
    score >= 70
      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400"
      : score >= 40
      ? "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300"
      : "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400";

  return (
    <span
      className={`inline-flex w-10 shrink-0 items-center justify-center rounded-lg py-1 text-sm font-bold ${classes}`}
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

export default async function OverviewPage() {
  const [report, audits] = await Promise.all([getNdprReport(7), getAudits(5, 0)]);

  const stats = report.ok
    ? [
        {
          label: "Avg trust score",
          value: report.data.average_trust_score != null ? String(report.data.average_trust_score) : "—",
          unit: report.data.average_trust_score != null ? "/100" : "",
          trend: `${report.data.total_audits} decisions scored`,
          positive: null as boolean | null,
        },
        {
          label: "Total audits (7d)",
          value: report.data.total_audits.toLocaleString(),
          unit: "",
          trend: `${report.data.available_audits.toLocaleString()} on record`,
          positive: null as boolean | null,
        },
        {
          label: "Low-trust decisions (7d)",
          value: String(report.data.low_trust_decisions),
          unit: "",
          trend: "Below alert threshold",
          positive: report.data.low_trust_decisions === 0 ? true : (false as boolean | null),
        },
        {
          label: "Active contexts",
          value: String(Object.keys(report.data.by_context_type).length),
          unit: "",
          trend:
            Object.keys(report.data.by_context_type).map(titleCaseContext).join(" · ") || "None yet",
          positive: null as boolean | null,
        },
      ]
    : [];

  const recent = audits.ok
    ? audits.data.items.map((a) => ({
        id: a.id ?? a.audit_id ?? "",
        context: titleCaseContext(a.context_type),
        title: auditTitle(a.stages?.intent?.detected_intent, a.input_text),
        score: a.trust_score ?? 0,
        flag: a.flags && a.flags.length > 0 ? a.flags[0] : null,
        time: relativeTime(a.created_at),
      }))
    : [];

  return (
    <DashboardShell>
      <div className="space-y-8">
        {/* Page header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-display text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
              Overview
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Trust score feed and pipeline health · last 7 days
            </p>
          </div>
          <div className="inline-flex items-center gap-2 self-start rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
            Pipeline healthy
          </div>
        </div>

        {!report.ok && <DataNotice result={report} />}

        {/* Stat cards */}
        {report.ok && (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-lg border border-rose-950/10 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/5"
              >
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  {stat.label}
                </p>
                <div className="mt-2 flex items-end gap-1">
                  <p className="font-display text-3xl font-semibold text-slate-950 dark:text-white">
                    {stat.value}
                  </p>
                  {stat.unit && (
                    <p className="mb-0.5 text-sm text-slate-400">{stat.unit}</p>
                  )}
                </div>
                <p
                  className={`mt-1 text-xs ${
                    stat.positive === true
                      ? "text-emerald-600 dark:text-emerald-400"
                      : stat.positive === false
                      ? "text-rose-600 dark:text-rose-400"
                      : "text-slate-400"
                  }`}
                >
                  {stat.trend}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Feed + pipeline health */}
        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          {/* Recent audits */}
          <div className="rounded-lg border border-rose-950/10 bg-white shadow-sm dark:border-white/10 dark:bg-white/5">
            <div className="flex items-center justify-between border-b border-rose-950/10 px-5 py-4 dark:border-white/10">
              <h2 className="font-display text-lg font-semibold text-slate-950 dark:text-white">
                Recent audits
              </h2>
              <a
                href="/audits"
                className="text-xs font-medium text-rose-700 transition-colors hover:text-rose-800 dark:text-rose-400 dark:hover:text-rose-300"
              >
                View all →
              </a>
            </div>
            {recent.length > 0 ? (
              <div className="divide-y divide-rose-950/5 dark:divide-white/5">
                {recent.map((audit) => (
                  <div key={audit.id} className="flex items-center gap-4 px-5 py-3.5">
                    <TrustBadge score={audit.score} />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${contextColors[audit.context] ?? "bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300"}`}
                        >
                          {audit.context}
                        </span>
                        <p className="truncate text-sm font-medium text-slate-900 dark:text-white">
                          {audit.title}
                        </p>
                      </div>
                      {audit.flag && (
                        <p className="mt-0.5 truncate font-mono text-xs text-rose-600 dark:text-rose-400">
                          {audit.flag}
                        </p>
                      )}
                    </div>
                    <p className="shrink-0 text-xs text-slate-400">{audit.time}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-5">
                {audits.ok ? (
                  <EmptyState message="No audits yet — run a decision through the SDK and it will appear here." />
                ) : (
                  <DataNotice result={audits} />
                )}
              </div>
            )}
          </div>

          {/* Pipeline health */}
          <div className="rounded-lg border border-rose-950/10 bg-white shadow-sm dark:border-white/10 dark:bg-white/5">
            <div className="border-b border-rose-950/10 px-5 py-4 dark:border-white/10">
              <h2 className="font-display text-lg font-semibold text-slate-950 dark:text-white">
                Pipeline health
              </h2>
            </div>
            <div className="space-y-2 p-4">
              {pipelineStages.map(({ n, label, icon: Icon, healthy }) => (
                <div
                  key={n}
                  className="flex items-center gap-3 rounded-lg bg-slate-50 px-3 py-2.5 dark:bg-white/[0.03]"
                >
                  <span className="w-6 shrink-0 font-mono text-xs font-bold text-slate-300 dark:text-slate-600">
                    {n}
                  </span>
                  <Icon
                    className="h-4 w-4 shrink-0 text-slate-400"
                    aria-hidden="true"
                  />
                  <span className="min-w-0 flex-1 truncate text-sm text-slate-700 dark:text-slate-200">
                    {label}
                  </span>
                  <span
                    className={`h-2 w-2 shrink-0 rounded-full ${
                      healthy ? "bg-emerald-500" : "bg-rose-500"
                    }`}
                    aria-label={healthy ? "Healthy" : "Degraded"}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
