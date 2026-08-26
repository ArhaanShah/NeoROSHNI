'use server'

/**
 * Server Actions for Team & Responder management (Sprint 2 C4).
 *
 * All requests forward the commander's httpOnly `access_token`
 * to FastAPI backend. The access token is never exposed to browser JS.
 */

import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

const FASTAPI_BASE_URL =
  process.env.FASTAPI_BASE_URL ?? 'http://localhost:8000'

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

async function getAccessToken(): Promise<string | null> {
  const store = await cookies()
  return store.get('access_token')?.value ?? null
}

export type ActionResponse = {
  success?: boolean
  error?: string
}

/**
 * Create a new team (Commander only).
 */
export async function createTeamAction(
  formData: FormData,
): Promise<ActionResponse> {
  const token = await getAccessToken()
  if (!token) {
    return { error: 'Authentication required' }
  }

  const name = (formData.get('name') as string)?.trim()
  if (!name) {
    return { error: 'Team name is required' }
  }

  try {
    const res = await fetch(`${FASTAPI_BASE_URL}/teams`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name }),
      cache: 'no-store',
    })

    if (!res.ok) {
      let data: unknown
      try {
        data = await res.json()
      } catch {
        return { error: 'Failed to create team' }
      }
      return { error: extractErrorMessage(data, 'Failed to create team') }
    }

    revalidatePath('/dashboard/commander/teams')
    return { success: true }
  } catch {
    return { error: 'Unable to reach the server. Please try again.' }
  }
}

/**
 * Delete a team by ID (Commander only).
 */
export async function deleteTeamAction(
  teamId: string,
): Promise<ActionResponse> {
  const token = await getAccessToken()
  if (!token) {
    return { error: 'Authentication required' }
  }

  try {
    const res = await fetch(`${FASTAPI_BASE_URL}/teams/${teamId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: 'no-store',
    })

    if (!res.ok) {
      let data: unknown
      try {
        data = await res.json()
      } catch {
        return { error: 'Failed to delete team' }
      }
      return { error: extractErrorMessage(data, 'Failed to delete team') }
    }

    revalidatePath('/dashboard/commander/teams')
    return { success: true }
  } catch {
    return { error: 'Unable to reach the server. Please try again.' }
  }
}

/**
 * Provision a new responder account (Commander only).
 */
export async function createResponderAction(
  formData: FormData,
): Promise<ActionResponse> {
  const token = await getAccessToken()
  if (!token) {
    return { error: 'Authentication required' }
  }

  const teamIdRaw = formData.get('team_id') as string | null
  const specializationRaw = formData.get('specialization') as string | null

  const payload = {
    email: (formData.get('email') as string)?.trim(),
    password: formData.get('password') as string,
    phone_number: (formData.get('phone_number') as string)?.trim(),
    full_name: (formData.get('full_name') as string)?.trim(),
    badge_number: (formData.get('badge_number') as string)?.trim(),
    specialization: specializationRaw?.trim() || null,
    team_id: teamIdRaw && teamIdRaw.trim() !== '' ? teamIdRaw.trim() : null,
  }

  try {
    const res = await fetch(`${FASTAPI_BASE_URL}/commander/responders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
      cache: 'no-store',
    })

    if (!res.ok) {
      let data: unknown
      try {
        data = await res.json()
      } catch {
        return { error: 'Failed to create responder' }
      }
      return { error: extractErrorMessage(data, 'Failed to create responder') }
    }

    revalidatePath('/dashboard/commander/teams')
    return { success: true }
  } catch {
    return { error: 'Unable to reach the server. Please try again.' }
  }
}

/**
 * Assign a responder to a team (Commander only).
 */
export async function assignResponderAction(
  teamId: string,
  responderId: string,
): Promise<ActionResponse> {
  const token = await getAccessToken()
  if (!token) {
    return { error: 'Authentication required' }
  }

  try {
    const res = await fetch(`${FASTAPI_BASE_URL}/teams/${teamId}/members`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ responder_id: responderId }),
      cache: 'no-store',
    })

    if (!res.ok) {
      let data: unknown
      try {
        data = await res.json()
      } catch {
        return { error: 'Failed to assign responder' }
      }
      return { error: extractErrorMessage(data, 'Failed to assign responder') }
    }

    revalidatePath('/dashboard/commander/teams')
    return { success: true }
  } catch {
    return { error: 'Unable to reach the server. Please try again.' }
  }
}

/**
 * Remove a responder from a team (Commander only).
 */
export async function removeResponderAction(
  teamId: string,
  responderId: string,
): Promise<ActionResponse> {
  const token = await getAccessToken()
  if (!token) {
    return { error: 'Authentication required' }
  }

  try {
    const res = await fetch(`${FASTAPI_BASE_URL}/teams/${teamId}/members/${responderId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: 'no-store',
    })

    if (!res.ok) {
      let data: unknown
      try {
        data = await res.json()
      } catch {
        return { error: 'Failed to remove responder' }
      }
      return { error: extractErrorMessage(data, 'Failed to remove responder') }
    }

    revalidatePath('/dashboard/commander/teams')
    return { success: true }
  } catch {
    return { error: 'Unable to reach the server. Please try again.' }
  }
}
