import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

/**
 * Protected layout — defense-in-depth guard behind middleware.
 * Redirects to /login if the access_token cookie is absent.
 * Authorization (role checks) happens in FastAPI, not here.
 */
export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const store = await cookies()
  if (!store.has('access_token')) {
    redirect('/login')
  }

  return <>{children}</>
}
