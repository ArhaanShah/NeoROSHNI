import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import type { TeamDetailResponse, UserMeResponse } from '@/lib/api-types'
import ResponderTeamView from '@/components/ResponderTeamView'

const FASTAPI_BASE_URL =
  process.env.FASTAPI_BASE_URL ?? 'http://localhost:8000'

export default async function ResponderTeamPage() {
  const store = await cookies()
  const accessToken = store.get('access_token')?.value

  if (!accessToken) {
    redirect('/login')
  }

  let team: TeamDetailResponse | null = null
  let currentUser: UserMeResponse | null = null

  try {
    const [meRes, teamRes] = await Promise.all([
      fetch(`${FASTAPI_BASE_URL}/users/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
        cache: 'no-store',
      }),
      fetch(`${FASTAPI_BASE_URL}/responders/me/team`, {
        headers: { Authorization: `Bearer ${accessToken}` },
        cache: 'no-store',
      }),
    ])

    if (meRes.status === 401 || teamRes.status === 401) {
      redirect('/login')
    }

    if (teamRes.status === 403) {
      return (
        <main style={styles.container}>
          <div style={styles.errorCard}>
            <h2 style={styles.errorHeading}>Access Denied</h2>
            <p>Only Responder accounts have an operational team roster view.</p>
            <Link href="/dashboard" style={styles.link}>Return to Dashboard</Link>
          </div>
        </main>
      )
    }

    if (meRes.ok) {
      currentUser = (await meRes.json()) as UserMeResponse
    }

    if (teamRes.ok) {
      team = (await teamRes.json()) as TeamDetailResponse | null
    }
  } catch {
    // Network or server error
  }

  return (
    <main style={styles.page}>
      <div style={styles.navBar}>
        <Link href="/dashboard" style={styles.link}>← Back to Dashboard</Link>
      </div>
      <ResponderTeamView team={team} currentUserId={currentUser?.user_id} />
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
    maxWidth: 800,
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
