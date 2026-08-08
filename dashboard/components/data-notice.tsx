import { ServerFetch } from '@/lib/server-api'

/** Renders a friendly banner for the non-success states of a server fetch. */
export function DataNotice({ result }: { result: Extract<ServerFetch<unknown>, { ok: false }> }) {
  const unconfigured = result.reason === 'unconfigured'
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm dark:border-amber-500/20 dark:bg-amber-500/10">
      <p className="font-semibold text-amber-800 dark:text-amber-300">
        {unconfigured ? 'Live data not connected yet' : "Couldn't reach the VERDANT API"}
      </p>
      <p className="mt-1 leading-6 text-amber-700/80 dark:text-amber-300/70">
        {unconfigured ? (
          <>
            Set <code className="rounded bg-amber-100 px-1.5 py-0.5 text-xs dark:bg-amber-500/20">VERDANT_API_KEY</code>{' '}
            in the dashboard environment to stream your live audit data here.
          </>
        ) : (
          <>The API didn&apos;t respond{result.message ? ` (${result.message})` : ''}. Showing nothing rather than stale data — try again shortly.</>
        )}
      </p>
    </div>
  )
}

/** Renders when the fetch succeeded but there are no records yet. */
export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-rose-950/10 bg-white px-5 py-10 text-center text-sm text-slate-500 shadow-sm dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
      {message}
    </div>
  )
}
