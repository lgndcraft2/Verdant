// Small presentation helpers shared by the dashboard data pages.

/** "hiring" -> "Hiring"; used for the context pill label. */
export function titleCaseContext(value?: string): string {
  if (!value) return 'Unknown'
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase()
}

/** "shortlist_candidate" -> "Shortlist candidate". */
export function humanize(value?: string): string {
  if (!value) return ''
  const spaced = value.replace(/[_-]+/g, ' ').trim()
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}

/** Best-effort short title for an audit row. */
export function auditTitle(intent?: string, inputText?: string): string {
  const fromIntent = humanize(intent)
  if (fromIntent) return fromIntent
  if (inputText) return inputText.length > 60 ? `${inputText.slice(0, 57)}…` : inputText
  return 'Untitled decision'
}

/** Compact relative time, e.g. "2 min ago", "3 hr ago", "5 d ago". */
export function relativeTime(iso?: string): string {
  if (!iso) return '—'
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return '—'
  const secs = Math.max(0, Math.round((Date.now() - then) / 1000))
  if (secs < 60) return 'just now'
  const mins = Math.round(secs / 60)
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs} hr ago`
  const days = Math.round(hrs / 24)
  return `${days} d ago`
}

/** Absolute timestamp for the audit detail line. */
export function formatTimestamp(iso?: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toISOString().replace('T', ' · ').slice(0, 19) + ' UTC'
}
