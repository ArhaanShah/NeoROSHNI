import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import type { TeamResponse, TeamDetailResponse, ResponderWithUserResponse } from '@/lib/api-types'
import CommanderTeamsView from '@/components/CommanderTeamsView'

const FASTAPI_BASE_URL =
  process.env.FASTAPI_BASE_URL ?? 'http://localhost:8000'

export default async function CommanderTeamsPage() {
  const store = await cookies()
  const accessToken = store.get('access_token')?.value

  if (!accessToken) {
    redirect('/login')
  }

  // 1. Fetch all teams
  let teams: TeamDetailResponse[] = []
  let responders: ResponderWithUserResponse[] = []

  try {
    const teamsRes = await fetch(`${FASTAPI_BASE_URL}/teams`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: 'no-store',
    })

    if (teamsRes.status === 401) {
      redirect('/login')
    }

    if (teamsRes.status === 403) {
      return (
        <main style={styles.container}>
          <div style={styles.errorCard}>
            <h2 style={styles.errorHeading}>Access Denied</h2>
            <p>Only Commander accounts have permission to access Team and Responder management.</p>
            <Link href="/dashboard" style={styles.link}>Return to Dashboard</Link>
          </div>
        </main>
      )
    }

    if (teamsRes.ok) {
      const teamList = (await teamsRes.json()) as TeamResponse[]
      // Fetch details for each team in parallel
      teams = await Promise.all(
        teamList.map(async (t) => {
          try {
            const detailRes = await fetch(`${FASTAPI_BASE_URL}/teams/${t.team_id}`, {
              headers: { Authorization: `Bearer ${accessToken}` },
              cache: 'no-store',
            })
            if (detailRes.ok) {
              return (await detailRes.json()) as TeamDetailResponse
            }
          } catch {
            // Fallback to basic team structure if detail fetch fails
          }
          return {
            team_id: t.team_id,
            name: t.name,
            commander_id: t.commander_id,
            created_at: t.created_at,
            updated_at: t.updated_at,
            members: [],
          }
        }),
      )
    }

    // 2. Fetch all responders
    const respRes = await fetch(`${FASTAPI_BASE_URL}/commander/responders`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: 'no-store',
    })

    if (respRes.ok) {
      responders = (await respRes.json()) as ResponderWithUserResponse[]
    }
  } catch {
    // Network or server error
  }

  return (
    <main style={styles.page}>
      <div style={styles.navBar}>
        <Link href="/dashboard" style={styles.link}>← Back to Dashboard</Link>
      </div>
      <CommanderTeamsView teams={teams} responders={responders} />
    </main>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    background: '#f9fafb',
    paddingBottom: '3rem',
  },
  navBar: {
    maxWidth: 1100,
    margin: '0 auto',
    padding: '1.5rem 1rem 0',
  },
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#f3f4f6',
    padding: '1rem',
  },
  errorCard: {
    background: '#fff',
    borderRadius: 8,
    padding: '2rem',
    maxWidth: 450,
    textAlign: 'center' as const,
    boxShadow: '0 1px 4px rgba(0,0,0,.12)',
  },
  errorHeading: {
    color: '#dc2626',
    margin: '0 0 1rem',
  },
  link: {
    display: 'inline-block',
    marginTop: '1rem',
    color: '#2563eb',
    textDecoration: 'none',
    fontWeight: 500,
  },
} as const
