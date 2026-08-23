'use client'

import { useState } from 'react'
import { login } from '@/lib/auth-actions'

/**
 * Login form client component.
 *
 * Calls the `login` Server Action on submit.
 * The Server Action runs on the server, calls FastAPI server-to-server,
 * sets httpOnly cookies, and then redirects to /dashboard on success.
 * On failure it returns { error } which we display here.
 *
 * Tokens are never accessible to browser JS.
 */
export default function LoginForm() {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const formData = new FormData(e.currentTarget)
    const result = await login(formData)

    // If the action redirected, `result` is never reached.
    if (result?.error) {
      setError(result.error)
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate style={styles.form}>
      {error && (
        <div role="alert" style={styles.error}>
          {error}
        </div>
      )}

      <div style={styles.field}>
        <label htmlFor="email" style={styles.label}>
          Email address
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          style={styles.input}
        />
      </div>

      <div style={styles.field}>
        <label htmlFor="password" style={styles.label}>
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          style={styles.input}
        />
      </div>

      <button type="submit" disabled={loading} style={styles.button}>
        {loading ? 'Signing in…' : 'Sign in'}
      </button>
    </form>
  )
}

const styles = {
  form: { display: 'flex', flexDirection: 'column' as const, gap: '.75rem' },
  error: {
    padding: '.75rem',
    background: '#fef2f2',
    border: '1px solid #fca5a5',
    borderRadius: 6,
    color: '#b91c1c',
    fontSize: '.875rem',
  },
  field: { display: 'flex', flexDirection: 'column' as const, gap: '.25rem' },
  label: { fontSize: '.875rem', fontWeight: 500, color: '#374151' },
  input: {
    padding: '.5rem .75rem',
    border: '1px solid #d1d5db',
    borderRadius: 6,
    fontSize: '1rem',
    outline: 'none',
  },
  button: {
    marginTop: '.5rem',
    padding: '.625rem',
    background: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    fontSize: '1rem',
    cursor: 'pointer',
  },
} as const
