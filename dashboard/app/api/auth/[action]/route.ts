import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.VERDANT_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'https://verdant-be.onrender.com'
const COOKIE = 'verdant_session'

export async function POST(request: NextRequest, { params }: { params: { action: string } }) {
  if (request.headers.get('origin') !== request.nextUrl.origin) {
    return NextResponse.json({ error: 'Invalid origin' }, { status: 403 })
  }
  if (params.action !== 'login' && params.action !== 'register') {
    return NextResponse.json({ error: 'Unknown action' }, { status: 404 })
  }
  const response = await fetch(`${API_URL}/auth/${params.action}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: await request.text(), cache: 'no-store',
  })
  const body = await response.json()
  if (!response.ok) return NextResponse.json(body, { status: response.status })
  const result = NextResponse.json({ data: body.data.user })
  result.cookies.set(COOKIE, body.data.access_token, {
    httpOnly: true, secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax', path: '/', maxAge: 12 * 60 * 60,
  })
  return result
}

export async function GET(request: NextRequest, { params }: { params: { action: string } }) {
  if (params.action !== 'me') return NextResponse.json({ error: 'Unknown action' }, { status: 404 })
  const token = request.cookies.get(COOKIE)?.value
  if (!token) return NextResponse.json({ error: 'Not signed in' }, { status: 401 })
  const response = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` }, cache: 'no-store',
  })
  return NextResponse.json(await response.json(), { status: response.status })
}
