/**
 * @vitest-environment node
 *
 * Unit tests for auth Server Actions.
 *
 * next/headers and next/navigation are mocked so the tests run in a plain
 * Node environment without the Next.js runtime.  We verify that:
 *   - Successful flows set the correct httpOnly cookies and call redirect.
 *   - Failed API responses return { error } and do NOT call redirect.
 *   - logout() revokes the refresh token server-side AND clears both cookies.
 *   - refreshTokens() clears cookies and redirects on revoked/expired token.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

// ---------------------------------------------------------------------------
// Mock next/headers — must be declared before importing the module under test.
// vi.hoisted() runs before module resolution so the factory is available when
// vi.mock() registers the mock.
// ---------------------------------------------------------------------------
const mockCookieStore = vi.hoisted(() => ({
  get: vi.fn<(name: string) => { value: string } | undefined>(),
  has: vi.fn<(name: string) => boolean>(),
  set: vi.fn(),
  delete: vi.fn(),
}))

vi.mock('next/headers', () => ({
  cookies: vi.fn(() => Promise.resolve(mockCookieStore)),
}))

// ---------------------------------------------------------------------------
// Mock next/navigation
// ---------------------------------------------------------------------------
const mockRedirect = vi.hoisted(() => vi.fn<(url: string) => never>())

vi.mock('next/navigation', () => ({
  redirect: mockRedirect,
}))

// ---------------------------------------------------------------------------
// Import module under test AFTER mocks are registered.
// ---------------------------------------------------------------------------
import { login, logout, refreshTokens, register } from '@/lib/auth-actions'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeOkResponse(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  } as unknown as Response
}

function makeErrorResponse(status: number, detail: string): Response {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ detail }),
  } as unknown as Response
}

const TOKENS = {
  access_token: 'test-access-token',
  refresh_token: 'test-refresh-token',
  token_type: 'bearer',
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('login()', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  it('sets httpOnly access and refresh cookies on success, then redirects', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(makeOkResponse(TOKENS))

    const fd = new FormData()
    fd.set('email', 'user@example.com')
    fd.set('password', 'StrongPass123!')

    await login(fd)

    expect(mockCookieStore.set).toHaveBeenCalledWith(
      'access_token',
      TOKENS.access_token,
      expect.objectContaining({ httpOnly: true }),
    )
    expect(mockCookieStore.set).toHaveBeenCalledWith(
      'refresh_token',
      TOKENS.refresh_token,
      expect.objectContaining({ httpOnly: true }),
    )
    expect(mockRedirect).toHaveBeenCalledWith('/dashboard')
  })

  it('returns { error } on bad credentials and does NOT redirect or set cookies', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(
      makeErrorResponse(401, 'Invalid credentials'),
    )

    const fd = new FormData()
    fd.set('email', 'user@example.com')
    fd.set('password', 'wrong')

    const result = await login(fd)

    expect(result).toEqual({ error: 'Invalid credentials' })
    expect(mockCookieStore.set).not.toHaveBeenCalled()
    expect(mockRedirect).not.toHaveBeenCalled()
  })

  it('returns a generic error when fetch throws (network failure)', async () => {
    vi.mocked(global.fetch).mockRejectedValueOnce(new Error('ECONNREFUSED'))

    const fd = new FormData()
    fd.set('email', 'user@example.com')
    fd.set('password', 'StrongPass123!')

    const result = await login(fd)

    expect(result?.error).toMatch(/Unable to reach/i)
    expect(mockRedirect).not.toHaveBeenCalled()
  })

  it('calls FastAPI /auth/login with the correct JSON body', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(makeOkResponse(TOKENS))

    const fd = new FormData()
    fd.set('email', 'user@example.com')
    fd.set('password', 'StrongPass123!')

    await login(fd)

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/login'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'user@example.com', password: 'StrongPass123!' }),
      }),
    )
  })
})

describe('register()', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  it('sets cookies and redirects on success', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(makeOkResponse(TOKENS))

    const fd = new FormData()
    fd.set('email', 'new@example.com')
    fd.set('password', 'StrongPass123!')
    fd.set('phone_number', '+15551234567')
    fd.set('full_name', 'Test User')

    await register(fd)

    expect(mockCookieStore.set).toHaveBeenCalledWith(
      'access_token',
      TOKENS.access_token,
      expect.objectContaining({ httpOnly: true }),
    )
    expect(mockRedirect).toHaveBeenCalledWith('/dashboard')
  })

  it('returns { error } on 409 conflict (duplicate email)', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(
      makeErrorResponse(409, 'Email already registered'),
    )

    const fd = new FormData()
    fd.set('email', 'existing@example.com')
    fd.set('password', 'StrongPass123!')
    fd.set('phone_number', '+15551234567')
    fd.set('full_name', 'Test User')

    const result = await register(fd)

    expect(result).toEqual({ error: 'Email already registered' })
    expect(mockCookieStore.set).not.toHaveBeenCalled()
    expect(mockRedirect).not.toHaveBeenCalled()
  })

  it('returns a generic error on network failure', async () => {
    vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Network error'))

    const fd = new FormData()
    fd.set('email', 'user@example.com')
    fd.set('password', 'StrongPass123!')
    fd.set('phone_number', '+15551234567')
    fd.set('full_name', 'Test User')

    const result = await register(fd)

    expect(result?.error).toMatch(/Unable to reach/i)
  })

  it('formats 422 validation error arrays into human-readable strings', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: () =>
        Promise.resolve({
          detail: [
            {
              type: 'value_error',
              loc: ['body', 'phone_number'],
              msg: 'Value error, Phone number must be E.164 format',
              input: '123',
            },
          ],
        }),
    } as unknown as Response)

    const fd = new FormData()
    fd.set('email', 'user@example.com')
    fd.set('password', 'StrongPass123!')
    fd.set('phone_number', '123')
    fd.set('full_name', 'Test User')

    const result = await register(fd)

    expect(result).toEqual({
      error: 'phone_number: Value error, Phone number must be E.164 format',
    })
  })
})

describe('logout()', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  it('calls FastAPI /auth/logout with the refresh token, clears cookies, and redirects', async () => {
    mockCookieStore.get.mockImplementation((name: string) =>
      name === 'refresh_token' ? { value: 'my-refresh-token' } : undefined,
    )
    vi.mocked(global.fetch).mockResolvedValueOnce(makeOkResponse({ message: 'Logged out' }))

    await logout()

    // Verified server-side revocation call
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/logout'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ refresh_token: 'my-refresh-token' }),
      }),
    )

    // Both cookies cleared
    expect(mockCookieStore.delete).toHaveBeenCalledWith('access_token')
    expect(mockCookieStore.delete).toHaveBeenCalledWith('refresh_token')

    // Redirected to login
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })

  it('still clears cookies and redirects even if the FastAPI logout call fails', async () => {
    mockCookieStore.get.mockImplementation((name: string) =>
      name === 'refresh_token' ? { value: 'my-refresh-token' } : undefined,
    )
    vi.mocked(global.fetch).mockRejectedValueOnce(new Error('ECONNREFUSED'))

    await logout()

    expect(mockCookieStore.delete).toHaveBeenCalledWith('access_token')
    expect(mockCookieStore.delete).toHaveBeenCalledWith('refresh_token')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })

  it('skips the FastAPI call when no refresh_token cookie is present', async () => {
    mockCookieStore.get.mockReturnValue(undefined)

    await logout()

    expect(global.fetch).not.toHaveBeenCalled()
    expect(mockCookieStore.delete).toHaveBeenCalledWith('access_token')
    expect(mockCookieStore.delete).toHaveBeenCalledWith('refresh_token')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })
})

describe('refreshTokens()', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  it('updates cookies with the new token pair on success', async () => {
    const newTokens = {
      access_token: 'new-access',
      refresh_token: 'new-refresh',
      token_type: 'bearer',
    }
    mockCookieStore.get.mockImplementation((name: string) =>
      name === 'refresh_token' ? { value: 'old-refresh-token' } : undefined,
    )
    vi.mocked(global.fetch).mockResolvedValueOnce(makeOkResponse(newTokens))

    await refreshTokens()

    expect(mockCookieStore.set).toHaveBeenCalledWith(
      'access_token',
      'new-access',
      expect.objectContaining({ httpOnly: true }),
    )
    expect(mockCookieStore.set).toHaveBeenCalledWith(
      'refresh_token',
      'new-refresh',
      expect.objectContaining({ httpOnly: true }),
    )
    expect(mockRedirect).not.toHaveBeenCalled()
  })

  it('clears cookies and redirects to /login when FastAPI returns 401 (revoked token)', async () => {
    mockCookieStore.get.mockImplementation((name: string) =>
      name === 'refresh_token' ? { value: 'revoked-token' } : undefined,
    )
    vi.mocked(global.fetch).mockResolvedValueOnce(
      makeErrorResponse(401, 'Refresh token revoked'),
    )

    await refreshTokens()

    expect(mockCookieStore.delete).toHaveBeenCalledWith('access_token')
    expect(mockCookieStore.delete).toHaveBeenCalledWith('refresh_token')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })

  it('clears cookies and redirects when no refresh_token cookie exists', async () => {
    mockCookieStore.get.mockReturnValue(undefined)

    await refreshTokens()

    expect(global.fetch).not.toHaveBeenCalled()
    expect(mockCookieStore.delete).toHaveBeenCalledWith('access_token')
    expect(mockCookieStore.delete).toHaveBeenCalledWith('refresh_token')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })
})
