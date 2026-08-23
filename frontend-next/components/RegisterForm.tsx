'use client'

import { useState } from 'react'
import { register } from '@/lib/auth-actions'

/**
 * Register form client component.
 *
 * Calls the `register` Server Action on submit.  All FastAPI interaction
 * happens server-to-server.  Tokens never reach browser JS.
 */
export default function RegisterForm() {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const formData = new FormData(e.currentTarget)
    const result = await register(formData)

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
        <label htmlFor="full_name" style={styles.label}>
          Full name
        </label>
        <input
          id="full_name"
          name="full_name"
          type="text"
          autoComplete="name"
          required
          style={styles.input}
        />
      </div>

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
        <label htmlFor="phone_number" style={styles.label}>
          Phone number{' '}
          <span style={styles.hint}>(E.164, e.g. +15551234567)</span>
        </label>
        <input
          id="phone_number"
          name="phone_number"
          type="tel"
          autoComplete="tel"
          placeholder="+15551234567"
          required
          style={styles.input}
        />
      </div>

      <div style={styles.field}>
        <label htmlFor="password" style={styles.label}>
          Password{' '}
          <span style={styles.hint}>(min 8 characters)</span>
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          required
          style={styles.input}
        />
      </div>

      <button type="submit" disabled={loading} style={styles.button}>
        {loading ? 'Creating account…' : 'Create account'}
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
  hint: { fontWeight: 400, color: '#9ca3af', fontSize: '.75rem' },
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
