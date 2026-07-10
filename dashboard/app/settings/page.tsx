import { DashboardShell } from "@/components/dashboard-shell";
import { ApiKeysForm } from "@/components/api-keys-form";
import { ProviderKeysForm } from "@/components/provider-keys-form";
import { signOut } from "@/app/auth/actions";

export default function SettingsPage() {
  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Settings
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Configure VERDANT for your deployment
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          {/* API Keys */}
          <ApiKeysForm />

          {/* Webhook thresholds */}
          <section className="rounded-lg border border-rose-950/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
            <h2 className="font-display text-xl font-semibold text-slate-950 dark:text-white">
              Webhook thresholds
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              Outputs with trust scores below this value trigger a webhook POST
              to your configured endpoint.
            </p>
            <div className="mt-4 rounded-lg border border-rose-950/10 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Alert threshold
                </p>
                <div className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 shadow-sm ring-1 ring-rose-950/10 dark:bg-white/10 dark:ring-white/10">
                  <p className="font-display text-xl font-semibold text-rose-700 dark:text-rose-400">
                    40
                  </p>
                  <p className="text-xs text-slate-400">/ 100</p>
                </div>
              </div>
              <p className="mt-2 text-xs text-slate-400">
                Webhooks fire when{" "}
                <code className="font-mono">trust_score &lt; 40</code>.
                Configurable via{" "}
                <code className="font-mono">VerdantConfig</code>.
              </p>
            </div>
          </section>

          {/* Baseline overrides */}
          <section className="rounded-lg border border-rose-950/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
            <h2 className="font-display text-xl font-semibold text-slate-950 dark:text-white">
              Baseline overrides
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              Override the default Nigerian fairness baseline per context or
              deployment.
            </p>
            <div className="mt-4 space-y-2">
              {[
                { context: "Hiring", version: "v2.1 (default)" },
                { context: "Lending", version: "v2.1 (default)" },
                { context: "Content", version: "v2.1 (default)" },
                { context: "Healthcare", version: "v1.8 (pinned)" },
              ].map(({ context, version }) => (
                <div
                  key={context}
                  className="flex items-center justify-between rounded-lg border border-rose-950/10 bg-slate-50 px-4 py-2.5 dark:border-white/10 dark:bg-white/5"
                >
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    {context}
                  </p>
                  <p className="font-mono text-xs text-slate-400">{version}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Provider Keys */}
          <ProviderKeysForm />

          {/* Account */}
          <section className="rounded-lg border border-rose-950/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
            <h2 className="font-display text-xl font-semibold text-slate-950 dark:text-white">
              Account
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              Sign out of your VERDANT account on this device.
            </p>
            <form action={signOut} className="mt-4">
              <button
                type="submit"
                className="inline-flex min-h-11 items-center justify-center rounded-lg border border-rose-950/10 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors duration-300 hover:border-rose-400 hover:text-rose-800 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:text-white"
              >
                Log out
              </button>
            </form>
          </section>
        </div>
      </div>
    </DashboardShell>
  );
}
