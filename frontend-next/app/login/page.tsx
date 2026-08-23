import LoginForm from '@/components/LoginForm'

export const metadata = { title: 'Sign in — NeoROSHNI' }

export default function LoginPage() {
  return (
    <main style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.heading}>NeoROSHNI</h1>
        <p style={styles.sub}>Sign in to your account</p>
        <LoginForm />
        <p style={styles.footer}>
          No account?{' '}
          <a href="/register" style={styles.link}>
            Register
          </a>
        </p>
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
    maxWidth: 400,
    boxShadow: '0 1px 4px rgba(0,0,0,.12)',
  },
  heading: { margin: '0 0 .25rem', fontSize: '1.5rem' },
  sub: { margin: '0 0 1.5rem', color: '#6b7280' },
  footer: { marginTop: '1rem', textAlign: 'center' as const, fontSize: '.875rem' },
  link: { color: '#2563eb' },
} as const
