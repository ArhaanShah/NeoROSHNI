import React from 'react'
import type { TeamDetailResponse } from '@/lib/api-types'

interface ResponderTeamViewProps {
  team: TeamDetailResponse | null
  currentUserId?: string
}

export default function ResponderTeamView({
  team,
  currentUserId,
}: ResponderTeamViewProps) {
  if (!team) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyCard}>
          <h2 style={styles.heading}>No Team Assigned</h2>
          <p style={styles.emptyText}>
            You are currently not assigned to any response team.
          </p>
          <p style={styles.mutedText}>
            Your incident commander will assign you to an operational team when disaster response operations commence.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          <div>
            <span style={styles.tag}>Operational Team</span>
            <h1 style={styles.teamName}>{team.name}</h1>
          </div>
          <span style={styles.badge}>
            {team.members.length} {team.members.length === 1 ? 'Responder' : 'Responders'}
          </span>
        </div>

        <div style={styles.metaRow}>
          <div>
            <span style={styles.metaLabel}>Commander ID:</span>{' '}
            <span style={styles.metaValue}>{team.commander_id}</span>
          </div>
          <div>
            <span style={styles.metaLabel}>Created:</span>{' '}
            <span style={styles.metaValue}>
              {new Date(team.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        <section style={styles.rosterSection}>
          <h2 style={styles.rosterHeading}>Team Roster & Fellow Responders</h2>
          <div style={styles.memberList}>
            {team.members.map((member) => {
              const isMe = currentUserId && member.user_id === currentUserId
              return (
                <div
                  key={member.user_id}
                  style={isMe ? styles.memberCardMe : styles.memberCard}
                >
                  <div style={styles.memberHeader}>
                    <div>
                      <strong style={styles.memberName}>
                        {member.full_name || 'Unnamed Responder'}
                        {isMe && <span style={styles.youBadge}> (You)</span>}
                      </strong>
                      <span style={styles.badgeNumber}>Badge #{member.badge_number}</span>
                    </div>
                    {member.specialization && (
                      <span style={styles.specBadge}>{member.specialization}</span>
                    )}
                  </div>
                  <div style={styles.memberContact}>
                    <span>Email: {member.email}</span>
                    <span>Phone: {member.phone_number}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      </div>
    </div>
  )
}

const styles = {
  container: {
    maxWidth: 800,
    margin: '0 auto',
    padding: '2rem 1rem',
    fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  card: {
    background: '#fff',
    borderRadius: 8,
    border: '1px solid #e5e7eb',
    padding: '2rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  emptyCard: {
    background: '#fff',
    borderRadius: 8,
    border: '1px dashed #d1d5db',
    padding: '3rem 2rem',
    textAlign: 'center' as const,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  heading: {
    fontSize: '1.5rem',
    fontWeight: 700,
    color: '#111827',
    margin: '0 0 0.5rem',
  },
  emptyText: {
    fontSize: '1.1rem',
    color: '#4b5563',
    margin: '0 0 0.5rem',
  },
  mutedText: {
    fontSize: '0.9rem',
    color: '#9ca3af',
    margin: 0,
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottom: '1px solid #e5e7eb',
    paddingBottom: '1.25rem',
  },
  tag: {
    textTransform: 'uppercase' as const,
    fontSize: '0.75rem',
    fontWeight: 700,
    letterSpacing: '0.05em',
    color: '#2563eb',
  },
  teamName: {
    fontSize: '1.75rem',
    fontWeight: 700,
    color: '#111827',
    margin: '0.25rem 0 0',
  },
  badge: {
    padding: '0.25rem 0.75rem',
    background: '#e0e7ff',
    color: '#3730a3',
    borderRadius: 9999,
    fontSize: '0.85rem',
    fontWeight: 600,
  },
  metaRow: {
    display: 'flex',
    gap: '2rem',
    padding: '1rem 0',
    borderBottom: '1px solid #f3f4f6',
    fontSize: '0.85rem',
  },
  metaLabel: {
    color: '#6b7280',
    fontWeight: 500,
  },
  metaValue: {
    color: '#1f2937',
    fontWeight: 600,
  },
  rosterSection: {
    marginTop: '1.5rem',
  },
  rosterHeading: {
    fontSize: '1.15rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: '0 0 1rem',
  },
  memberList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.75rem',
  },
  memberCard: {
    padding: '1rem',
    background: '#f9fafb',
    borderRadius: 6,
    border: '1px solid #e5e7eb',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  memberCardMe: {
    padding: '1rem',
    background: '#eff6ff',
    borderRadius: 6,
    border: '1px solid #bfdbfe',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  memberHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  memberName: {
    fontSize: '1rem',
    color: '#111827',
  },
  youBadge: {
    color: '#2563eb',
    fontWeight: 600,
  },
  badgeNumber: {
    display: 'block',
    fontSize: '0.8rem',
    color: '#6b7280',
    marginTop: '0.15rem',
  },
  specBadge: {
    padding: '0.2rem 0.5rem',
    background: '#f3f4f6',
    border: '1px solid #e5e7eb',
    borderRadius: 4,
    fontSize: '0.75rem',
    color: '#374151',
    fontWeight: 500,
  },
  memberContact: {
    display: 'flex',
    gap: '1.5rem',
    fontSize: '0.8rem',
    color: '#6b7280',
  },
} as const
