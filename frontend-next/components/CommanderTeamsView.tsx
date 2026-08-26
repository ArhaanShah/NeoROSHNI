'use client'

import React, { useState } from 'react'
import type { TeamDetailResponse, ResponderWithUserResponse } from '@/lib/api-types'
import {
  createTeamAction,
  deleteTeamAction,
  createResponderAction,
  assignResponderAction,
  removeResponderAction,
} from '@/lib/team-actions'

interface CommanderTeamsViewProps {
  teams: TeamDetailResponse[]
  responders: ResponderWithUserResponse[]
}

export default function CommanderTeamsView({
  teams,
  responders,
}: CommanderTeamsViewProps) {
  const [teamError, setTeamError] = useState<string | null>(null)
  const [teamSuccess, setTeamSuccess] = useState<string | null>(null)
  const [teamLoading, setTeamLoading] = useState(false)

  const [respError, setRespError] = useState<string | null>(null)
  const [respSuccess, setRespSuccess] = useState<string | null>(null)
  const [respLoading, setRespLoading] = useState(false)

  const [actionError, setActionError] = useState<string | null>(null)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  const [selectedResponderForTeam, setSelectedResponderForTeam] = useState<Record<string, string>>({})

  async function handleCreateTeam(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setTeamError(null)
    setTeamSuccess(null)
    setTeamLoading(true)

    const form = e.currentTarget
    const formData = new FormData(form)
    const res = await createTeamAction(formData)

    setTeamLoading(false)
    if (res.error) {
      setTeamError(res.error)
    } else {
      setTeamSuccess('Team created successfully!')
      form.reset()
    }
  }

  async function handleDeleteTeam(teamId: string, teamName: string) {
    if (!confirm(`Are you sure you want to delete "${teamName}"? Responders will be unassigned.`)) {
      return
    }
    setActionError(null)
    setActionSuccess(null)

    const res = await deleteTeamAction(teamId)
    if (res.error) {
      setActionError(res.error)
    } else {
      setActionSuccess(`Team "${teamName}" deleted.`)
    }
  }

  async function handleCreateResponder(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setRespError(null)
    setRespSuccess(null)
    setRespLoading(true)

    const form = e.currentTarget
    const formData = new FormData(form)
    const res = await createResponderAction(formData)

    setRespLoading(false)
    if (res.error) {
      setRespError(res.error)
    } else {
      setRespSuccess('Responder account provisioned successfully!')
      form.reset()
    }
  }

  async function handleAssignMember(teamId: string) {
    const responderId = selectedResponderForTeam[teamId]
    if (!responderId) {
      setActionError('Please select a responder to assign.')
      return
    }

    setActionError(null)
    setActionSuccess(null)

    const res = await assignResponderAction(teamId, responderId)
    if (res.error) {
      setActionError(res.error)
    } else {
      setActionSuccess('Responder assigned to team.')
      setSelectedResponderForTeam((prev) => ({ ...prev, [teamId]: '' }))
    }
  }

  async function handleRemoveMember(teamId: string, responderId: string, responderName: string) {
    setActionError(null)
    setActionSuccess(null)

    const res = await removeResponderAction(teamId, responderId)
    if (res.error) {
      setActionError(res.error)
    } else {
      setActionSuccess(`Removed ${responderName || 'responder'} from team.`)
    }
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.heading}>Commander Team & Responder Management</h1>
        <p style={styles.subtext}>
          Provision responder accounts, manage disaster response teams, and organize assignments.
        </p>
      </header>

      {actionError && (
        <div role="alert" style={styles.alertError}>
          {actionError}
        </div>
      )}
      {actionSuccess && (
        <div role="status" style={styles.alertSuccess}>
          {actionSuccess}
        </div>
      )}

      {/* Grid with 2 columns: Creation forms */}
      <div style={styles.formsGrid}>
        {/* Create Team Form */}
        <div style={styles.card}>
          <h2 style={styles.cardHeading}>Create New Team</h2>
          <form onSubmit={handleCreateTeam} style={styles.form}>
            {teamError && <div role="alert" style={styles.alertError}>{teamError}</div>}
            {teamSuccess && <div role="status" style={styles.alertSuccess}>{teamSuccess}</div>}

            <div style={styles.field}>
              <label htmlFor="team-name" style={styles.label}>
                Team Name *
              </label>
              <input
                id="team-name"
                name="name"
                type="text"
                placeholder="e.g. Alpha Search & Rescue"
                required
                style={styles.input}
              />
            </div>

            <button type="submit" disabled={teamLoading} style={styles.buttonPrimary}>
              {teamLoading ? 'Creating…' : 'Create Team'}
            </button>
          </form>
        </div>

        {/* Provision Responder Form */}
        <div style={styles.card}>
          <h2 style={styles.cardHeading}>Provision Responder Account</h2>
          <form onSubmit={handleCreateResponder} style={styles.form}>
            {respError && <div role="alert" style={styles.alertError}>{respError}</div>}
            {respSuccess && <div role="status" style={styles.alertSuccess}>{respSuccess}</div>}

            <div style={styles.fieldRow}>
              <div style={styles.field}>
                <label htmlFor="resp-name" style={styles.label}>Full Name *</label>
                <input id="resp-name" name="full_name" type="text" placeholder="Jane Doe" required style={styles.input} />
              </div>
              <div style={styles.field}>
                <label htmlFor="resp-badge" style={styles.label}>Badge Number *</label>
                <input id="resp-badge" name="badge_number" type="text" placeholder="RSP-1001" required style={styles.input} />
              </div>
            </div>

            <div style={styles.fieldRow}>
              <div style={styles.field}>
                <label htmlFor="resp-email" style={styles.label}>Email Address *</label>
                <input id="resp-email" name="email" type="email" placeholder="jane@example.com" required style={styles.input} />
              </div>
              <div style={styles.field}>
                <label htmlFor="resp-phone" style={styles.label}>Phone Number (E.164) *</label>
                <input id="resp-phone" name="phone_number" type="text" placeholder="+15551234567" required style={styles.input} />
              </div>
            </div>

            <div style={styles.fieldRow}>
              <div style={styles.field}>
                <label htmlFor="resp-password" style={styles.label}>Temporary Password *</label>
                <input id="resp-password" name="password" type="password" placeholder="Min 8 characters" required minLength={8} style={styles.input} />
              </div>
              <div style={styles.field}>
                <label htmlFor="resp-specialization" style={styles.label}>Specialization</label>
                <input id="resp-specialization" name="specialization" type="text" placeholder="e.g. Paramedic, K9, Fire" style={styles.input} />
              </div>
            </div>

            <div style={styles.field}>
              <label htmlFor="resp-team" style={styles.label}>Assign to Team (Optional)</label>
              <select id="resp-team" name="team_id" style={styles.select}>
                <option value="">-- Unassigned (No initial team) --</option>
                {teams.map((t) => (
                  <option key={t.team_id} value={t.team_id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            <button type="submit" disabled={respLoading} style={styles.buttonPrimary}>
              {respLoading ? 'Provisioning…' : 'Provision Responder'}
            </button>
          </form>
        </div>
      </div>

      {/* Teams and Rosters */}
      <section style={styles.section}>
        <h2 style={styles.sectionHeading}>Teams & Member Rosters ({teams.length})</h2>
        {teams.length === 0 ? (
          <div style={styles.emptyCard}>No teams created yet. Create a team above to get started.</div>
        ) : (
          <div style={styles.teamsGrid}>
            {teams.map((team) => {
              const currentMemberIds = new Set(team.members.map((m) => m.user_id))
              const assignableResponders = responders.filter(
                (r) => !currentMemberIds.has(r.user_id)
              )

              return (
                <div key={team.team_id} style={styles.teamCard}>
                  <div style={styles.teamHeader}>
                    <div>
                      <h3 style={styles.teamTitle}>{team.name}</h3>
                      <span style={styles.badge}>{team.members.length} {team.members.length === 1 ? 'member' : 'members'}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteTeam(team.team_id, team.name)}
                      style={styles.deleteButton}
                    >
                      Delete Team
                    </button>
                  </div>

                  <div style={styles.memberSection}>
                    <h4 style={styles.subHeading}>Roster</h4>
                    {team.members.length === 0 ? (
                      <p style={styles.mutedText}>No responders assigned to this team.</p>
                    ) : (
                      <ul style={styles.memberList}>
                        {team.members.map((member) => (
                          <li key={member.user_id} style={styles.memberItem}>
                            <div>
                              <strong>{member.full_name || 'Unnamed'}</strong>
                              <span style={styles.memberMeta}>
                                Badge: {member.badge_number}
                                {member.specialization && ` • ${member.specialization}`}
                                {` • ${member.email}`}
                              </span>
                            </div>
                            <button
                              type="button"
                              onClick={() => handleRemoveMember(team.team_id, member.user_id, member.full_name)}
                              style={styles.removeButton}
                            >
                              Remove
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* Assign Responder to Team */}
                  <div style={styles.assignRow}>
                    <select
                      value={selectedResponderForTeam[team.team_id] || ''}
                      onChange={(e) =>
                        setSelectedResponderForTeam((prev) => ({
                          ...prev,
                          [team.team_id]: e.target.value,
                        }))
                      }
                      style={styles.selectSmall}
                    >
                      <option value="">-- Select responder to assign --</option>
                      {assignableResponders.map((r) => (
                        <option key={r.user_id} value={r.user_id}>
                          {r.full_name || r.email} ({r.badge_number}){r.team_name ? ` [Currently in ${r.team_name}]` : ' [Unassigned]'}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => handleAssignMember(team.team_id)}
                      style={styles.buttonSecondary}
                      disabled={!selectedResponderForTeam[team.team_id]}
                    >
                      Assign
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>

      {/* All Responders Overview */}
      <section style={styles.section}>
        <h2 style={styles.sectionHeading}>All Registered Responders ({responders.length})</h2>
        {responders.length === 0 ? (
          <div style={styles.emptyCard}>No responders provisioned yet. Use the form above to provision responder accounts.</div>
        ) : (
          <div style={styles.tableWrapper}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>Badge</th>
                  <th style={styles.th}>Full Name</th>
                  <th style={styles.th}>Email</th>
                  <th style={styles.th}>Phone</th>
                  <th style={styles.th}>Specialization</th>
                  <th style={styles.th}>Assigned Team</th>
                </tr>
              </thead>
              <tbody>
                {responders.map((r) => (
                  <tr key={r.user_id} style={styles.tr}>
                    <td style={styles.td}><strong>{r.badge_number}</strong></td>
                    <td style={styles.td}>{r.full_name || '—'}</td>
                    <td style={styles.td}>{r.email}</td>
                    <td style={styles.td}>{r.phone_number}</td>
                    <td style={styles.td}>{r.specialization || '—'}</td>
                    <td style={styles.td}>
                      {r.team_name ? (
                        <span style={styles.teamTag}>{r.team_name}</span>
                      ) : (
                        <span style={styles.unassignedTag}>Unassigned</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

const styles = {
  container: {
    maxWidth: 1100,
    margin: '0 auto',
    padding: '2rem 1rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '2rem',
    fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    borderBottom: '1px solid #e5e7eb',
    paddingBottom: '1rem',
  },
  heading: {
    fontSize: '1.75rem',
    fontWeight: 700,
    color: '#111827',
    margin: 0,
  },
  subtext: {
    color: '#6b7280',
    marginTop: '0.25rem',
    fontSize: '0.95rem',
  },
  alertError: {
    padding: '0.75rem 1rem',
    background: '#fef2f2',
    border: '1px solid #fca5a5',
    borderRadius: 6,
    color: '#b91c1c',
    fontSize: '0.875rem',
  },
  alertSuccess: {
    padding: '0.75rem 1rem',
    background: '#f0fdf4',
    border: '1px solid #86efac',
    borderRadius: 6,
    color: '#15803d',
    fontSize: '0.875rem',
  },
  formsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
    gap: '1.5rem',
  },
  card: {
    background: '#fff',
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '1.5rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  cardHeading: {
    fontSize: '1.25rem',
    fontWeight: 600,
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '1rem',
  },
  form: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.875rem',
  },
  fieldRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '0.75rem',
  },
  field: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.25rem',
  },
  label: {
    fontSize: '0.8125rem',
    fontWeight: 500,
    color: '#374151',
  },
  input: {
    padding: '0.5rem 0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: 6,
    fontSize: '0.9rem',
    outline: 'none',
  },
  select: {
    padding: '0.5rem 0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: 6,
    fontSize: '0.9rem',
    background: '#fff',
    outline: 'none',
  },
  selectSmall: {
    flex: 1,
    padding: '0.4rem 0.6rem',
    border: '1px solid #d1d5db',
    borderRadius: 6,
    fontSize: '0.85rem',
    background: '#fff',
    outline: 'none',
  },
  buttonPrimary: {
    marginTop: '0.5rem',
    padding: '0.5rem 1rem',
    background: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    fontWeight: 500,
    fontSize: '0.9rem',
    cursor: 'pointer',
  },
  buttonSecondary: {
    padding: '0.4rem 0.8rem',
    background: '#374151',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    fontSize: '0.85rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  section: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
  },
  sectionHeading: {
    fontSize: '1.35rem',
    fontWeight: 600,
    color: '#111827',
    margin: 0,
  },
  emptyCard: {
    padding: '2rem',
    background: '#f9fafb',
    border: '1px dashed #d1d5db',
    borderRadius: 8,
    textAlign: 'center' as const,
    color: '#6b7280',
  },
  teamsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
    gap: '1.25rem',
  },
  teamCard: {
    background: '#fff',
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '1.25rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  teamHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottom: '1px solid #f3f4f6',
    paddingBottom: '0.75rem',
  },
  teamTitle: {
    fontSize: '1.15rem',
    fontWeight: 600,
    margin: 0,
    color: '#111827',
  },
  badge: {
    display: 'inline-block',
    marginTop: '0.25rem',
    fontSize: '0.75rem',
    padding: '0.15rem 0.5rem',
    borderRadius: 9999,
    background: '#e0e7ff',
    color: '#3730a3',
    fontWeight: 500,
  },
  deleteButton: {
    padding: '0.3rem 0.6rem',
    background: '#fee2e2',
    color: '#dc2626',
    border: 'none',
    borderRadius: 4,
    fontSize: '0.75rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  memberSection: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  subHeading: {
    fontSize: '0.9rem',
    fontWeight: 600,
    color: '#4b5563',
    margin: 0,
  },
  mutedText: {
    fontSize: '0.85rem',
    color: '#9ca3af',
    margin: 0,
  },
  memberList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  memberItem: {
    padding: '0.5rem 0.75rem',
    background: '#f9fafb',
    borderRadius: 6,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '0.85rem',
  },
  memberMeta: {
    display: 'block',
    fontSize: '0.75rem',
    color: '#6b7280',
  },
  removeButton: {
    padding: '0.2rem 0.5rem',
    background: '#f3f4f6',
    border: '1px solid #d1d5db',
    borderRadius: 4,
    color: '#ef4444',
    fontSize: '0.75rem',
    cursor: 'pointer',
  },
  assignRow: {
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center',
    paddingTop: '0.5rem',
    borderTop: '1px solid #f3f4f6',
  },
  tableWrapper: {
    overflowX: 'auto' as const,
    border: '1px solid #e5e7eb',
    borderRadius: 8,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    background: '#fff',
    fontSize: '0.9rem',
  },
  th: {
    padding: '0.75rem 1rem',
    background: '#f9fafb',
    textAlign: 'left' as const,
    fontWeight: 600,
    color: '#4b5563',
    borderBottom: '1px solid #e5e7eb',
  },
  tr: {
    borderBottom: '1px solid #f3f4f6',
  },
  td: {
    padding: '0.75rem 1rem',
    color: '#374151',
  },
  teamTag: {
    display: 'inline-block',
    padding: '0.2rem 0.5rem',
    borderRadius: 4,
    background: '#ecfdf5',
    color: '#047857',
    fontSize: '0.8rem',
    fontWeight: 500,
  },
  unassignedTag: {
    display: 'inline-block',
    padding: '0.2rem 0.5rem',
    borderRadius: 4,
    background: '#fef3c7',
    color: '#92400e',
    fontSize: '0.8rem',
    fontWeight: 500,
  },
} as const
