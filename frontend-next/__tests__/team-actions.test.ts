/**
 * @vitest-environment node
 *
 * Unit tests for Team and Responder Server Actions (Sprint 2 C4).
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

// ---------------------------------------------------------------------------
// Mock next/headers
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
// Mock next/cache
// ---------------------------------------------------------------------------
const mockRevalidatePath = vi.hoisted(() => vi.fn<(path: string) => void>())

vi.mock('next/cache', () => ({
  revalidatePath: mockRevalidatePath,
}))

import {
  createTeamAction,
  deleteTeamAction,
  createResponderAction,
  assignResponderAction,
  removeResponderAction,
} from '@/lib/team-actions'

function makeOkResponse(body: unknown, status = 200): Response {
  return {
    ok: true,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response
}

function makeErrorResponse(status: number, detail: string | unknown[]): Response {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ detail }),
  } as unknown as Response
}

describe('Team Server Actions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
    mockCookieStore.get.mockImplementation((name: string) =>
      name === 'access_token' ? { value: 'commander-access-token' } : undefined,
    )
  })

  describe('createTeamAction()', () => {
    it('creates team successfully and revalidates path', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeOkResponse({
          team_id: 'team-123',
          name: 'Alpha Search & Rescue',
          commander_id: 'cmd-1',
          member_count: 0,
        }, 201),
      )

      const fd = new FormData()
      fd.set('name', 'Alpha Search & Rescue')

      const res = await createTeamAction(fd)

      expect(res).toEqual({ success: true })
      expect(mockRevalidatePath).toHaveBeenCalledWith('/dashboard/commander/teams')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/teams'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer commander-access-token',
          }),
          body: JSON.stringify({ name: 'Alpha Search & Rescue' }),
        }),
      )
    })

    it('returns error when not authenticated', async () => {
      mockCookieStore.get.mockReturnValue(undefined)

      const fd = new FormData()
      fd.set('name', 'Alpha Search & Rescue')

      const res = await createTeamAction(fd)
      expect(res).toEqual({ error: 'Authentication required' })
      expect(global.fetch).not.toHaveBeenCalled()
    })

    it('returns error when team name is empty', async () => {
      const fd = new FormData()
      fd.set('name', '   ')

      const res = await createTeamAction(fd)
      expect(res).toEqual({ error: 'Team name is required' })
      expect(global.fetch).not.toHaveBeenCalled()
    })

    it('handles backend error gracefully', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeErrorResponse(400, 'Team name invalid'),
      )

      const fd = new FormData()
      fd.set('name', 'Bad Team')

      const res = await createTeamAction(fd)
      expect(res).toEqual({ error: 'Team name invalid' })
    })

    it('handles network failure gracefully', async () => {
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Connection refused'))

      const fd = new FormData()
      fd.set('name', 'Alpha Search & Rescue')

      const res = await createTeamAction(fd)
      expect(res.error).toMatch(/Unable to reach the server/i)
    })
  })

  describe('deleteTeamAction()', () => {
    it('deletes team successfully', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeOkResponse({ message: 'Team deleted successfully' }),
      )

      const res = await deleteTeamAction('team-123')

      expect(res).toEqual({ success: true })
      expect(mockRevalidatePath).toHaveBeenCalledWith('/dashboard/commander/teams')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/teams/team-123'),
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({
            Authorization: 'Bearer commander-access-token',
          }),
        }),
      )
    })

    it('returns error on 404', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeErrorResponse(404, 'Team not found'),
      )

      const res = await deleteTeamAction('non-existent')
      expect(res).toEqual({ error: 'Team not found' })
    })
  })

  describe('createResponderAction()', () => {
    it('provisions responder account with team assignment', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeOkResponse({
          user_id: 'user-resp-1',
          email: 'responder@example.com',
          phone_number: '+15551234567',
          full_name: 'Jane Doe',
          badge_number: 'RSP-101',
          specialization: 'Paramedic',
          team_id: 'team-123',
          team_name: 'Alpha Search & Rescue',
          is_active: true,
        }, 201),
      )

      const fd = new FormData()
      fd.set('email', 'responder@example.com')
      fd.set('password', 'SecurePassword123!')
      fd.set('phone_number', '+15551234567')
      fd.set('full_name', 'Jane Doe')
      fd.set('badge_number', 'RSP-101')
      fd.set('specialization', 'Paramedic')
      fd.set('team_id', 'team-123')

      const res = await createResponderAction(fd)

      expect(res).toEqual({ success: true })
      expect(mockRevalidatePath).toHaveBeenCalledWith('/dashboard/commander/teams')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/commander/responders'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'responder@example.com',
            password: 'SecurePassword123!',
            phone_number: '+15551234567',
            full_name: 'Jane Doe',
            badge_number: 'RSP-101',
            specialization: 'Paramedic',
            team_id: 'team-123',
          }),
        }),
      )
    })

    it('returns error on duplicate badge number (409 Conflict)', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeErrorResponse(409, 'Badge number already registered'),
      )

      const fd = new FormData()
      fd.set('email', 'responder@example.com')
      fd.set('password', 'SecurePassword123!')
      fd.set('phone_number', '+15551234567')
      fd.set('full_name', 'Jane Doe')
      fd.set('badge_number', 'DUPLICATE')

      const res = await createResponderAction(fd)
      expect(res).toEqual({ error: 'Badge number already registered' })
    })

    it('parses 422 validation errors into readable format', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeErrorResponse(422, [
          { loc: ['body', 'badge_number'], msg: 'Badge number must be alphanumeric' },
        ]),
      )

      const fd = new FormData()
      fd.set('email', 'responder@example.com')
      fd.set('password', 'SecurePassword123!')
      fd.set('phone_number', '+15551234567')
      fd.set('full_name', 'Jane Doe')
      fd.set('badge_number', '!!')

      const res = await createResponderAction(fd)
      expect(res.error).toContain('badge_number: Badge number must be alphanumeric')
    })
  })

  describe('assignResponderAction()', () => {
    it('assigns responder to team', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeOkResponse({
          user_id: 'user-resp-1',
          team_id: 'team-123',
          badge_number: 'RSP-101',
        }),
      )

      const res = await assignResponderAction('team-123', 'user-resp-1')

      expect(res).toEqual({ success: true })
      expect(mockRevalidatePath).toHaveBeenCalledWith('/dashboard/commander/teams')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/teams/team-123/members'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ responder_id: 'user-resp-1' }),
        }),
      )
    })
  })

  describe('removeResponderAction()', () => {
    it('removes responder from team', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeOkResponse({ message: 'Responder unassigned from team' }),
      )

      const res = await removeResponderAction('team-123', 'user-resp-1')

      expect(res).toEqual({ success: true })
      expect(mockRevalidatePath).toHaveBeenCalledWith('/dashboard/commander/teams')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/teams/team-123/members/user-resp-1'),
        expect.objectContaining({
          method: 'DELETE',
        }),
      )
    })

    it('returns error when responder is not assigned to target team (400 Bad Request)', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        makeErrorResponse(400, 'Responder is not assigned to this team'),
      )

      const res = await removeResponderAction('team-123', 'user-resp-1')
      expect(res).toEqual({ error: 'Responder is not assigned to this team' })
    })
  })
})
