import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname
  if (path === '/' || path.startsWith('/docs') || path.startsWith('/login') || path.startsWith('/api/auth/')) {
    return NextResponse.next()
  }
  const token = request.cookies.get('verdant_session')?.value
  if (!token) return NextResponse.redirect(new URL('/login', request.url))
  const api = process.env.VERDANT_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'https://verdant-be.onrender.com'
  try {
    const response = await fetch(`${api}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }, cache: 'no-store',
    })
    if (response.ok) return NextResponse.next()
  } catch {}
  const redirect = NextResponse.redirect(new URL('/login', request.url))
  redirect.cookies.delete('verdant_session')
  return redirect
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * Feel free to modify this pattern to include more paths.
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
