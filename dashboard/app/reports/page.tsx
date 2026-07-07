import { ArrowIcon, FileTextIcon } from "@/components/icons";
import { DashboardShell } from "@/components/dashboard-shell";

const reports = [
  {
    title: "Monthly NDPR export",
    desc: "Full audit log with context types, trust scores, and explanation quality for the past 30 days.",
    format: "PDF + JSON",
    generated: "2026-07-01",
    status: "ready",
  },
  {
    title: "Bias trend summary",
    desc: "Flag frequency and pattern trends by context type, model version, and time window.",
    format: "CSV + PDF",
    generated: "2026-07-05",
    status: "ready",
  },
  {
    title: "Model version comparison",
    desc: "Trust score distributions and bias flag rates across model versions used in this deployment.",
    format: "PDF",
    generated: "2026-07-06",
    status: "processing",
  },
];

const statusClasses: Record<string, string> = {
  ready:
    "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400",
  processing:
    "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400",
};

export default function ReportsPage() {
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
              Export NDPR-ready compliance summaries for stakeholders
            </p>
          </div>
          <button className="inline-flex min-h-10 items-center gap-2 self-start rounded-lg bg-rose-700 px-4 py-2.5 text-sm font-semibold text-white transition-transform duration-300 hover:-translate-y-0.5 hover:bg-rose-800">
            Generate report
          </button>
        </div>

        {/* Report cards */}
        <div className="grid gap-4 md:grid-cols-3">
          {reports.map((report) => (
            <div
              key={report.title}
              className="flex flex-col rounded-lg border border-rose-950/10 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/5"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400">
                  <FileTextIcon className="h-5 w-5" aria-hidden="true" />
                </div>
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusClasses[report.status]}`}
                >
                  {report.status}
                </span>
              </div>

              <h2 className="mt-4 font-display text-lg font-semibold text-slate-950 dark:text-white">
                {report.title}
              </h2>
              <p className="mt-2 flex-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {report.desc}
              </p>

              <div className="mt-4 flex items-center justify-between border-t border-rose-950/10 pt-4 dark:border-white/10">
                <div className="space-y-0.5">
                  <p className="text-xs text-slate-400">Format: {report.format}</p>
                  <p className="text-xs text-slate-400">
                    Generated: {report.generated}
                  </p>
                </div>
                {report.status === "ready" && (
                  <button className="inline-flex items-center gap-1.5 text-sm font-medium text-rose-700 transition-colors hover:text-rose-800 dark:text-rose-400 dark:hover:text-rose-300">
                    Download
                    <ArrowIcon className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* NDPR info panel */}
        <div className="rounded-lg border border-rose-950/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-rose-700 dark:text-rose-400">
            NDPR compliance
          </p>
          <h2 className="mt-3 font-display text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Every report is audit-ready.
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            VERDANT exports include timestamps, context types, trust scores,
            bias flags, and the plain-language explanations generated for each
            decision. Each report meets the documentation requirements under the
            Nigeria Data Protection Regulation.
          </p>
        </div>
      </div>
    </DashboardShell>
  );
}
