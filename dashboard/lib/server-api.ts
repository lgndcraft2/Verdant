// Server-only data layer for the dashboard's read pages (overview, audits,
// reports). These hit the VERDANT API's key-protected read endpoints, so the
// request is made from the Next.js server with a VERDANT API key held in a
// server-only env var (VERDANT_API_KEY) — it never reaches the browser, and
// server-to-server calls aren't subject to CORS.

const API_URL =
  process.env.VERDANT_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  'https://verdant-be.onrender.com'

const KEY = process.env.VERDANT_API_KEY ?? ''

export type ServerFetch<T> =
  | { ok: true; data: T }
  | { ok: false; reason: 'unconfigured' | 'error'; message?: string }

export async function serverGet<T>(path: string, timeoutMs = 8000): Promise<ServerFetch<T>> {
  if (!KEY) return { ok: false, reason: 'unconfigured' }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(`${API_URL}${path}`, {
      headers: { Authorization: `Bearer ${KEY}` },
      cache: 'no-store',
      signal: controller.signal,
    })
    if (!res.ok) return { ok: false, reason: 'error', message: `API returned ${res.status}` }
    const body = await res.json()
    return { ok: true, data: body.data as T }
  } catch (err) {
    return { ok: false, reason: 'error', message: err instanceof Error ? err.message : 'request failed' }
  } finally {
    clearTimeout(timer)
  }
}

// ---- Response shapes (subset of the API's audit payload we render) ----

export interface AuditItem {
  id?: string
  audit_id?: string
  created_at?: string
  context_type?: string
  input_text?: string
  output_text?: string
  trust_score?: number
  flags?: string[]
  explanation?: string
  model_name?: string | null
  stages?: {
    intent?: { detected_intent?: string }
  }
}

export interface AuditList {
  items: AuditItem[]
  total: number
}

export interface NdprReport {
  generated_at: string
  window_days: number
  total_audits: number
  available_audits: number
  low_trust_decisions: number
  average_trust_score: number | null
  by_context_type: Record<string, number>
  flag_counts: Record<string, number>
  compliance_notes: string[]
}

export const getAudits = (limit = 50, offset = 0) =>
  serverGet<AuditList>(`/audits?limit=${limit}&offset=${offset}`)

export const getNdprReport = (days = 30) =>
  serverGet<NdprReport>(`/reports/ndpr?days=${days}`)
