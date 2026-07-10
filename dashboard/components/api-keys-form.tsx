'use client'

import { useEffect, useState } from 'react'
import { API_URL, fetchWithTimeout, getAuthHeader } from '@/lib/api'

interface ApiKey {
  id: string
  key_prefix: string
  label: string | null
  active: boolean
  created_at: string | null
  last_used_at: string | null
}

function formatDate(value: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString()
}

export function ApiKeysForm() {
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [rawKey, setRawKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  const loadKeys = () =>
    getAuthHeader()
      .then((headers) => fetchWithTimeout(`${API_URL}/keys`, { headers }))
      .then((res) => res.json())
      .then((json) => {
        if (Array.isArray(json.data)) setKeys(json.data)
      })
      .catch((err) => console.error('Failed to fetch API keys:', err))

  useEffect(() => {
    loadKeys().finally(() => setLoading(false))
  }, [])

  const hasKey = keys.length > 0

  const issue = async (path: string) => {
    setWorking(true)
    setMessage(null)
    setRawKey(null)
    setCopied(false)
    try {
      const authHeader = await getAuthHeader()
      const res = await fetchWithTimeout(`${API_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader },
        body: JSON.stringify({}),
      })
      const json = await res.json()
      if (!res.ok) {
        throw new Error(json.error?.message || 'Failed to issue key')
      }
      setRawKey(json.data.raw_key)
      setMessage({ text: json.meta?.message || 'API key created.', type: 'success' })
      await loadKeys()
    } catch (err: any) {
      setMessage({ text: err.message || 'Something went wrong', type: 'error' })
    } finally {
      setWorking(false)
    }
  }

  const handleGenerate = () => issue('/keys')

  const handleRegenerate = () => {
    if (!window.confirm('Regenerate your API key? Your current key will stop working immediately.')) {
      return
    }
    return issue('/keys/regenerate')
  }

  const copyKey = async () => {
    if (!rawKey) return
    try {
      await navigator.clipboard.writeText(rawKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setMessage({ text: 'Copy failed — select and copy manually.', type: 'error' })
    }
  }

  return (
    <section className="rounded-lg border border-rose-950/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
      <h2 className="font-display text-xl font-semibold text-slate-950 dark:text-white">
        API keys
      </h2>
      <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
        Your VERDANT API key grants full access to your pipeline and audit logs. Use it as a
        Bearer token in the SDK or API. Keep it secret.
      </p>

      {message && (
        <div
          className={`mt-4 rounded-lg p-3 text-sm font-medium ${
            message.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-400'
              : 'bg-rose-50 text-rose-800 dark:bg-rose-500/10 dark:text-rose-400'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Freshly issued raw key — shown once */}
      {rawKey && (
        <div className="mt-4 rounded-lg border border-emerald-300 bg-emerald-50 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800 dark:text-emerald-300">
            Copy this key now — it won&apos;t be shown again
          </p>
          <div className="mt-2 flex items-center gap-3">
            <code className="flex-1 truncate rounded-md bg-white px-3 py-2 font-mono text-sm text-slate-800 dark:bg-slate-950 dark:text-slate-100">
              {rawKey}
            </code>
            <button
              onClick={copyKey}
              className="shrink-0 rounded-lg bg-emerald-700 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-800"
            >
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
        </div>
      )}

      {/* Existing key status */}
      <div className="mt-4">
        {loading ? (
          <div className="h-12 animate-pulse rounded-lg bg-slate-100 dark:bg-white/5" />
        ) : hasKey ? (
          <ul className="space-y-2">
            {keys.map((key) => (
              <li
                key={key.id}
                className="flex items-center justify-between gap-3 rounded-lg border border-rose-950/10 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-white/5"
              >
                <code className="truncate font-mono text-sm text-slate-600 dark:text-slate-300">
                  {key.key_prefix}
                  {'•'.repeat(16)}
                </code>
                <span className="shrink-0 text-xs text-slate-400">
                  Created {formatDate(key.created_at)}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="rounded-lg border border-dashed border-rose-950/15 px-4 py-3 text-sm text-slate-500 dark:border-white/10 dark:text-slate-400">
            No API key yet. Generate one to start using the SDK.
          </p>
        )}
      </div>

      <div className="mt-4">
        {hasKey ? (
          <button
            onClick={handleRegenerate}
            disabled={working}
            className="text-xs font-medium text-slate-500 transition-colors hover:text-rose-700 disabled:opacity-50 dark:hover:text-rose-400"
          >
            {working ? 'Working…' : 'Regenerate key →'}
          </button>
        ) : (
          <button
            onClick={handleGenerate}
            disabled={working}
            className="rounded-lg bg-rose-700 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-800 disabled:opacity-50"
          >
            {working ? 'Generating…' : 'Generate key'}
          </button>
        )}
      </div>
    </section>
  )
}
