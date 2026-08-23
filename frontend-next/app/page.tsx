import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

/**
 * Root page: redirect based on session cookie presence.
 * The middleware already handles most redirect logic, but this covers the
 * root path specifically.
 */
export default async function RootPage() {
  const store = await cookies()
  const hasSession = store.has('access_token')

  if (hasSession) {
    redirect('/dashboard')
  } else {
    redirect('/login')
  }
}
