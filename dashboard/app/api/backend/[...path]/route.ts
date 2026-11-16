import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.VERDANT_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'https://verdant-be.onrender.com'

async function forward(request: NextRequest, path: string[]) {
  if (request.method !== 'GET' && request.headers.get('origin') !== request.nextUrl.origin) {
    return NextResponse.json({ error: 'Invalid origin' }, { status: 403 })
  }
  const token = request.cookies.get('verdant_session')?.value
  if (!token) return NextResponse.json({ error: 'Not signed in' }, { status: 401 })
  const target = new URL(`${API_URL}/${path.join('/')}`)
  target.search = request.nextUrl.search
  const response = await fetch(target, {
    method: request.method,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: request.method === 'GET' ? undefined : await request.text(),
    cache: 'no-store',
  })
  return NextResponse.json(await response.json(), { status: response.status })
}

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return forward(request, params.path)
}
export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return forward(request, params.path)
}
