import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { logout } from '@/lib/auth-actions'
import type { UserMeResponse } from '@/lib/api-types'

const FASTAPI_BASE_URL =
  process.env.FASTAPI_BASE_URL ?? 'http://localhost:8000'

/**
 * Minimal protected dashboard shell.
 * Fetches /users/me server-side, attaching the access token from the
 * httpOnly cookie as an Authorization header.  The token never leaves
 * the server process.
 */
export default async function DashboardPage() {
  const store = await cookies()
  const accessToken = store.get('access_token')?.value

  if (!accessToken) {
    redirect('/login')
  }

  let user: UserMeResponse
  try {
    const res = await fetch(`${FASTAPI_BASE_URL}/users/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: 'no-store',
    })

    if (res.status === 401) {
      // Access token expired — redirect to login so user re-authenticates.
      redirect('/login')
    }

    if (!res.ok) {
      redirect('/login')
    }

    user = (await res.json()) as UserMeResponse
  } catch {
    redirect('/login')
  }

  return (
    <main style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.heading}>Dashboard</h1>
        <dl style={styles.dl}>
          <dt style={styles.dt}>Email</dt>
          <dd style={styles.dd}>{user.email}</dd>
          <dt style={styles.dt}>Role</dt>
          <dd style={styles.dd}>{user.role}</dd>
          <dt style={styles.dt}>Account status</dt>
          <dd style={styles.dd}>{user.is_active ? 'Active' : 'Inactive'}</dd>
        </dl>

        {user.role === 'commander' && (
          <div style={styles.roleActionBox}>
            <a href="/dashboard/commander/teams" style={styles.actionBtn}>
              Manage Teams & Responders →
            </a>
          </div>
        )}

        {user.role === 'responder' && (
          <div style={styles.roleActionBox}>
            <a href="/dashboard/responder/team" style={styles.actionBtn}>
              View My Team & Teammates →
            </a>
          </div>
        )}

        {/* Logout form — Server Action is invoked via form submission */}
        <form action={logout} style={styles.form}>
          <button type="submit" style={styles.logoutBtn}>
            Sign out
          </button>
        </form>
      </div>
    </main>
  )
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#f3f4f6',
  },
  card: {
    background: '#fff',
    borderRadius: 8,
    padding: '2rem',
    width: '100%',
    maxWidth: 480,
    boxShadow: '0 1px 4px rgba(0,0,0,.12)',
  },
  heading: { margin: '0 0 1.25rem', fontSize: '1.5rem' },
  dl: { margin: '0 0 1.5rem' },
  dt: { fontWeight: 600, marginTop: '.75rem', color: '#374151' },
  dd: { margin: '.25rem 0 0', color: '#6b7280' },
  roleActionBox: { marginTop: '1.25rem', marginBottom: '0.5rem' },
  actionBtn: {
    display: 'block',
    padding: '.625rem 1rem',
    background: '#2563eb',
    color: '#fff',
    borderRadius: 6,
    textDecoration: 'none',
    textAlign: 'center' as const,
    fontWeight: 500,
    fontSize: '0.95rem',
  },
  form: { marginTop: '1.5rem' },
  logoutBtn: {
    padding: '.5rem 1.25rem',
    background: '#ef4444',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: '1rem',
    width: '100%',
  },
} as const
