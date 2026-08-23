'use server'

/**
 * Server Actions for auth flows.
 *
 * All FastAPI calls happen server-to-server — tokens are NEVER passed to
 * browser JavaScript.  Cookies are set as httpOnly so they are invisible
 * to client-side code.
 *
 * FastAPI remains the authorization boundary; this file is the session
 * holder only.
 */

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import type { AuthActionError, TokenPairResponse } from '@/lib/api-types'

const FASTAPI_BASE_URL =
  process.env.FASTAPI_BASE_URL ?? 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

async function setAuthCookies(tokens: TokenPairResponse): Promise<void> {
  const store = await cookies()
  const isProd = process.env.NODE_ENV === 'production'

  store.set('access_token', tokens.access_token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: isProd,
    path: '/',
    // Mirror the FastAPI TTL so the cookie expires roughly when the JWT does.
    maxAge: 15 * 60, // 15 minutes
  })

  store.set('refresh_token', tokens.refresh_token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: isProd,
    path: '/',
    maxAge: 14 * 24 * 60 * 60, // 14 days
  })
}

async function clearAuthCookies(): Promise<void> {
  const store = await cookies()
  store.delete('access_token')
  store.delete('refresh_token')
}

function extractErrorMessage(data: unknown, fallback: string): string {
  if (typeof data === 'object' && data !== null && 'detail' in data) {
    const detail = (data as { detail: unknown }).detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const messages = detail
        .map((item) => {
          if (typeof item === 'string') return item
          if (typeof item === 'object' && item !== null && 'msg' in item) {
            const loc = Array.isArray((item as { loc?: unknown[] }).loc)
              ? (item as { loc: unknown[] }).loc.filter((l) => l !== 'body').join('.')
              : ''
            const msg = String((item as { msg: unknown }).msg)
            return loc ? `${loc}: ${msg}` : msg
          }
          return null
        })
        .filter(Boolean)
      if (messages.length > 0) {
        return messages.join('; ')
      }
    }
  }
  return fallback
}

// ---------------------------------------------------------------------------
// Public Server Actions
// ---------------------------------------------------------------------------

/**
 * Register a new civilian account.
 * On success: sets httpOnly cookies and redirects to /dashboard.
 * On failure: returns { error } so the form can display it.
 */
export async function register(
  formData: FormData,
): Promise<AuthActionError | undefined> {
  const body = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
    phone_number: formData.get('phone_number') as string,
    full_name: formData.get('full_name') as string,
  }

  let res: Response
  try {
    res = await fetch(`${FASTAPI_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
    })
  } catch {
    return { error: 'Unable to reach the authentication server. Try again.' }
  }

  if (!res.ok) {
    let data: unknown
    try {
      data = await res.json()
    } catch {
      return { error: 'Registration failed' }
    }
    return { error: extractErrorMessage(data, 'Registration failed') }
  }

  const tokens = (await res.json()) as TokenPairResponse
  await setAuthCookies(tokens)
  redirect('/dashboard')
}

/**
 * Authenticate an existing user.
 * On success: sets httpOnly cookies and redirects to /dashboard.
 * On failure: returns { error }.
 */
export async function login(
  formData: FormData,
): Promise<AuthActionError | undefined> {
  const body = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  let res: Response
  try {
    res = await fetch(`${FASTAPI_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
    })
  } catch {
    return { error: 'Unable to reach the authentication server. Try again.' }
  }

  if (!res.ok) {
    let data: unknown
    try {
      data = await res.json()
    } catch {
      return { error: 'Login failed' }
    }
    return { error: extractErrorMessage(data, 'Login failed') }
  }

  const tokens = (await res.json()) as TokenPairResponse
  await setAuthCookies(tokens)
  redirect('/dashboard')
}

/**
 * Revoke the refresh token server-side, clear cookies, and send the user
 * to the login page.
 *
 * The FastAPI /auth/logout call is best-effort — if it fails (e.g. the
 * refresh token is already expired), we still clear the cookies locally
 * so the user is logged out from the browser perspective.
 *
 * A stolen access token will still work until its TTL expires (~15 min).
 * A stolen refresh token that has been revoked here will be rejected
 * immediately by FastAPI on the next /auth/refresh attempt.
 */
export async function logout(): Promise<never> {
  const store = await cookies()
  const refreshToken = store.get('refresh_token')?.value

  if (refreshToken) {
    // Best-effort server-side revocation. Swallow errors so logout is always
    // idempotent from the user's perspective.
    try {
      await fetch(`${FASTAPI_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
        cache: 'no-store',
      })
    } catch {
      // Swallow — cookie clearing below is the hard guarantee.
    }
  }

  await clearAuthCookies()
  redirect('/login')
}

/**
 * Silently rotate the access/refresh token pair.
 * Called by the dashboard layout when the access token is near expiry.
 * On failure: clears cookies and sends the user to login.
 */
export async function refreshTokens(): Promise<void> {
  const store = await cookies()
  const refreshToken = store.get('refresh_token')?.value

  if (!refreshToken) {
    await clearAuthCookies()
    redirect('/login')
    return
  }

  let res: Response
  try {
    res = await fetch(`${FASTAPI_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: 'no-store',
    })
  } catch {
    await clearAuthCookies()
    redirect('/login')
    return
  }

  if (!res.ok) {
    // Revoked or expired refresh token — force re-login.
    await clearAuthCookies()
    redirect('/login')
    return
  }

  const tokens = (await res.json()) as TokenPairResponse
  await setAuthCookies(tokens)
}
