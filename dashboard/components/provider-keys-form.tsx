'use client'

import { useEffect, useState } from 'react'
import { API_URL, fetchWithTimeout, getAuthHeader } from '@/lib/api'

interface ProviderStatus {
  anthropic: boolean
  gemini: boolean
}

export function ProviderKeysForm() {
  const [status, setStatus] = useState<ProviderStatus>({ anthropic: false, gemini: false })
  const [anthropicKey, setAnthropicKey] = useState('')
  const [geminiKey, setGeminiKey] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState<'anthropic' | 'gemini' | null>(null)
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  useEffect(() => {
    getAuthHeader()
      .then((headers) => fetchWithTimeout(`${API_URL}/providers/keys`, { headers }))
      .then((res) => res.json())
      .then((json) => {
        if (json.data) {
          setStatus({
            anthropic: json.data.anthropic || false,
            gemini: json.data.gemini || false,
          })
        }
      })
      .catch((err) => console.error('Failed to fetch provider keys status:', err))
      .finally(() => setLoading(false))
  }, [])

  const handleSubmit = async (provider: 'anthropic' | 'gemini', key: string) => {
    if (!key) return
    setSubmitting(provider)
    setMessage(null)

    try {
      const authHeader = await getAuthHeader()
      const res = await fetchWithTimeout(`${API_URL}/providers/keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader },
        body: JSON.stringify({ provider, api_key: key }),
      })
      const json = await res.json()

      if (!res.ok) {
        throw new Error(json.error?.message || 'Failed to update key')
      }

      setStatus((prev) => ({ ...prev, [provider]: true }))
      if (provider === 'anthropic') setAnthropicKey('')
      if (provider === 'gemini') setGeminiKey('')
      
      setMessage({ text: `${provider} key updated successfully`, type: 'success' })
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' })
    } finally {
      setSubmitting(null)
    }
  }

  return (
    <section className="rounded-lg border border-rose-950/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
      <h2 className="font-display text-xl font-semibold text-slate-950 dark:text-white">
        LLM Provider Keys
      </h2>
      <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
        Supply the API keys for the language models. VERDANT abstracts these costs and complexity away from your developers.
      </p>

      {message && (
        <div className={`mt-4 rounded-lg p-3 text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-400' : 'bg-rose-50 text-rose-800 dark:bg-rose-500/10 dark:text-rose-400'}`}>
          {message.text}
        </div>
      )}

      <div className="mt-6 space-y-6">
        {/* Anthropic */}
        <div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Anthropic Claude (Primary)
            </label>
            {loading ? (
              <div className="h-5 w-16 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
            ) : status.anthropic ? (
              <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-500/20">
                Configured
              </span>
            ) : (
              <span className="inline-flex items-center rounded-md bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700 ring-1 ring-inset ring-rose-600/10 dark:bg-rose-500/10 dark:text-rose-400 dark:ring-rose-500/20">
                Missing
              </span>
            )}
          </div>
          <div className="mt-2 flex gap-3">
            <input
              type="password"
              placeholder="sk-ant-..."
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-rose-500 focus:outline-none focus:ring-1 focus:ring-rose-500 dark:border-white/10 dark:bg-white/5 dark:text-white"
            />
            <button
              onClick={() => handleSubmit('anthropic', anthropicKey)}
              disabled={!anthropicKey || submitting === 'anthropic'}
              className="shrink-0 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
            >
              {submitting === 'anthropic' ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>

        {/* Gemini */}
        <div className="border-t border-slate-200 pt-6 dark:border-white/10">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Google Gemini (Fallback)
            </label>
            {loading ? (
              <div className="h-5 w-16 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
            ) : status.gemini ? (
              <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-500/20">
                Configured
              </span>
            ) : (
              <span className="inline-flex items-center rounded-md bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700 ring-1 ring-inset ring-rose-600/10 dark:bg-rose-500/10 dark:text-rose-400 dark:ring-rose-500/20">
                Missing
              </span>
            )}
          </div>
          <div className="mt-2 flex gap-3">
            <input
              type="password"
              placeholder="AIza..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-rose-500 focus:outline-none focus:ring-1 focus:ring-rose-500 dark:border-white/10 dark:bg-white/5 dark:text-white"
            />
            <button
              onClick={() => handleSubmit('gemini', geminiKey)}
              disabled={!geminiKey || submitting === 'gemini'}
              className="shrink-0 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
            >
              {submitting === 'gemini' ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}
