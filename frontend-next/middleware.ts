import { type NextRequest, NextResponse } from 'next/server'

/**
 * Public paths that do not require an access-token cookie.
 * The middleware checks cookie presence only — no JWT verification happens here.
 * FastAPI remains the authorization boundary.
 */
const PUBLIC_PREFIXES = ['/login', '/register', '/_next', '/favicon.ico']

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl

  // Allow public paths through unconditionally.
  if (PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return NextResponse.next()
  }

  // Gate everything else on cookie presence only — no role logic here.
  const hasAccessToken = request.cookies.has('access_token')
  if (!hasAccessToken) {
    const loginUrl = new URL('/login', request.url)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  // Run on all paths except static files and image optimisation routes.
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
