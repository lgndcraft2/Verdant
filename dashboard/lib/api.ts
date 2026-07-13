import { createClient } from '@/lib/supabase/client'

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'https://verdant-be.onrender.com'

// Abort a request after `ms` so a down backend fails fast instead of hanging
// the page on the browser's default (multi-minute) TCP timeout.
export async function fetchWithTimeout(
  input: string,
  init: RequestInit = {},
  ms = 8000,
): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), ms)
  try {
    return await fetch(input, { ...init, signal: controller.signal })
  } finally {
    clearTimeout(timer)
  }
}

// Authorization header carrying the current Supabase session token, which the
// API verifies before allowing key/provider management.
export async function getAuthHeader(): Promise<Record<string, string>> {
  const supabase = createClient()
  const {
    data: { session },
  } = await supabase.auth.getSession()
  return session ? { Authorization: `Bearer ${session.access_token}` } : {}
}
