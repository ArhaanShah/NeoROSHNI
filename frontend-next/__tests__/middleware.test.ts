/**
 * @vitest-environment node
 *
 * Unit tests for Next.js middleware.
 *
 * Checks that public routes (/login, /register, etc.) are allowed through unconditionally,
 * while protected routes redirect to /login if the access_token cookie is missing.
 */

import { describe, expect, it, vi } from 'vitest'
import { NextRequest, NextResponse } from 'next/server'
import { middleware } from '@/middleware'

// Mock next/server
vi.mock('next/server', () => {
  class MockNextResponse {
    static next() {
      return { status: 200, headers: new Map(), type: 'next' }
    }
    static redirect(url: URL) {
      return { status: 307, headers: new Map([['location', url.toString()]]), type: 'redirect' }
    }
  }
  return {
    NextRequest: class MockNextRequest {
      url: string
      nextUrl: { pathname: string }
      cookies: {
        has: (name: string) => boolean
        get: (name: string) => { value: string } | undefined
      }
      constructor(url: string, cookiesMap: Record<string, string> = {}) {
        this.url = url
        const urlObj = new URL(url)
        this.nextUrl = { pathname: urlObj.pathname }
        this.cookies = {
          has: (name: string) => !!cookiesMap[name],
          get: (name: string) => cookiesMap[name] ? { value: cookiesMap[name] } : undefined,
        }
      }
    },
    NextResponse: MockNextResponse,
  }
})

describe('middleware()', () => {
  it('allows public paths unconditionally', () => {
    const publicPaths = ['/login', '/register', '/_next/static/chunks/main.js', '/favicon.ico']

    for (const path of publicPaths) {
      const req = new NextRequest(`http://localhost:3000${path}`)
      const res = middleware(req as unknown as NextRequest)
      expect(res).toBeDefined()
      expect((res as any).type).toBe('next')
    }
  })

  it('redirects to /login if access_token cookie is missing on protected paths', () => {
    const protectedPaths = ['/dashboard', '/dashboard/settings', '/profile']

    for (const path of protectedPaths) {
      const req = new NextRequest(`http://localhost:3000${path}`)
      const res = middleware(req as unknown as NextRequest)
      expect(res).toBeDefined()
      expect((res as any).type).toBe('redirect')
      expect((res as any).headers.get('location')).toBe('http://localhost:3000/login')
    }
  })

  it('allows protected paths if access_token cookie is present', () => {
    const req = new (NextRequest as any)('http://localhost:3000/dashboard', { access_token: 'valid-token' })
    const res = middleware(req as unknown as NextRequest)
    expect(res).toBeDefined()
    expect((res as any).type).toBe('next')
  })
})
