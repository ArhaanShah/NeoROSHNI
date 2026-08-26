/**
 * @vitest-environment jsdom
 */

import React from 'react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CommanderTeamsView from '@/components/CommanderTeamsView'
import ResponderTeamView from '@/components/ResponderTeamView'
import * as teamActions from '@/lib/team-actions'
import type { TeamDetailResponse, ResponderWithUserResponse } from '@/lib/api-types'

vi.mock('@/lib/team-actions', () => ({
  createTeamAction: vi.fn(),
  deleteTeamAction: vi.fn(),
  createResponderAction: vi.fn(),
  assignResponderAction: vi.fn(),
  removeResponderAction: vi.fn(),
}))

const mockTeams: TeamDetailResponse[] = [
  {
    team_id: 'team-1',
    name: 'Alpha Search & Rescue',
    commander_id: 'cmd-1',
    created_at: '2026-08-26T10:00:00Z',
    updated_at: '2026-08-26T10:00:00Z',
    members: [
      {
        user_id: 'resp-1',
        email: 'jane@example.com',
        phone_number: '+15551234567',
        full_name: 'Jane Doe',
        badge_number: 'RSP-101',
        specialization: 'Paramedic',
        team_id: 'team-1',
        team_name: 'Alpha Search & Rescue',
        is_active: true,
        created_at: '2026-08-26T10:00:00Z',
        updated_at: '2026-08-26T10:00:00Z',
      },
    ],
  },
]

const mockResponders: ResponderWithUserResponse[] = [
  {
    user_id: 'resp-1',
    email: 'jane@example.com',
    phone_number: '+15551234567',
    full_name: 'Jane Doe',
    badge_number: 'RSP-101',
    specialization: 'Paramedic',
    team_id: 'team-1',
    team_name: 'Alpha Search & Rescue',
    is_active: true,
    created_at: '2026-08-26T10:00:00Z',
    updated_at: '2026-08-26T10:00:00Z',
  },
  {
    user_id: 'resp-2',
    email: 'john@example.com',
    phone_number: '+15559876543',
    full_name: 'John Smith',
    badge_number: 'RSP-102',
    specialization: 'K9 Search',
    team_id: null,
    team_name: null,
    is_active: true,
    created_at: '2026-08-26T10:00:00Z',
    updated_at: '2026-08-26T10:00:00Z',
  },
]

describe('CommanderTeamsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders teams, member rosters, and all responders', () => {
    render(<CommanderTeamsView teams={mockTeams} responders={mockResponders} />)

    expect(screen.getByText('Commander Team & Responder Management')).toBeDefined()
    expect(screen.getByRole('heading', { name: 'Alpha Search & Rescue' })).toBeDefined()
    expect(screen.getByRole('heading', { name: 'Alpha Search & Rescue' })).toBeDefined()
    expect(screen.getAllByText('Jane Doe').length).toBeGreaterThan(0)
    expect(screen.getByText(/Badge: RSP-101/)).toBeDefined()
    expect(screen.getByText('John Smith')).toBeDefined()
    expect(screen.getByText('Unassigned')).toBeDefined()
  })

  it('renders empty state when there are no teams', () => {
    render(<CommanderTeamsView teams={[]} responders={[]} />)
    expect(screen.getByText(/No teams created yet/i)).toBeDefined()
    expect(screen.getByText(/No responders provisioned yet/i)).toBeDefined()
  })

  it('submits create team form and calls createTeamAction', async () => {
    vi.mocked(teamActions.createTeamAction).mockResolvedValueOnce({ success: true })

    render(<CommanderTeamsView teams={mockTeams} responders={mockResponders} />)

    const input = screen.getByLabelText(/Team Name \*/i)
    fireEvent.change(input, { target: { value: 'Bravo Evac' } })

    const submitBtn = screen.getByRole('button', { name: /Create Team/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(teamActions.createTeamAction).toHaveBeenCalled()
      expect(screen.getByText(/Team created successfully!/i)).toBeDefined()
    })
  })

  it('displays error when create team fails', async () => {
    vi.mocked(teamActions.createTeamAction).mockResolvedValueOnce({ error: 'Team name already exists' })

    render(<CommanderTeamsView teams={mockTeams} responders={mockResponders} />)

    const input = screen.getByLabelText(/Team Name \*/i)
    fireEvent.change(input, { target: { value: 'Alpha Search & Rescue' } })

    const submitBtn = screen.getByRole('button', { name: /Create Team/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText('Team name already exists')).toBeDefined()
    })
  })

  it('submits create responder form and calls createResponderAction', async () => {
    vi.mocked(teamActions.createResponderAction).mockResolvedValueOnce({ success: true })

    render(<CommanderTeamsView teams={mockTeams} responders={mockResponders} />)

    fireEvent.change(screen.getByLabelText(/Full Name \*/i), { target: { value: 'Alice Brown' } })
    fireEvent.change(screen.getByLabelText(/Badge Number \*/i), { target: { value: 'RSP-103' } })
    fireEvent.change(screen.getByLabelText(/Email Address \*/i), { target: { value: 'alice@example.com' } })
    fireEvent.change(screen.getByLabelText(/Phone Number/i), { target: { value: '+15552223333' } })
    fireEvent.change(screen.getByLabelText(/Temporary Password \*/i), { target: { value: 'Password123!' } })

    const submitBtn = screen.getByRole('button', { name: /Provision Responder/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(teamActions.createResponderAction).toHaveBeenCalled()
      expect(screen.getByText(/Responder account provisioned successfully!/i)).toBeDefined()
    })
  })

  it('handles remove responder click', async () => {
    vi.mocked(teamActions.removeResponderAction).mockResolvedValueOnce({ success: true })

    render(<CommanderTeamsView teams={mockTeams} responders={mockResponders} />)

    const removeBtn = screen.getByRole('button', { name: /Remove/i })
    fireEvent.click(removeBtn)

    await waitFor(() => {
      expect(teamActions.removeResponderAction).toHaveBeenCalledWith('team-1', 'resp-1')
      expect(screen.getByText(/Removed Jane Doe from team/i)).toBeDefined()
    })
  })
})

describe('ResponderTeamView', () => {
  it('renders unassigned empty state when team is null', () => {
    render(<ResponderTeamView team={null} />)

    expect(screen.getByText('No Team Assigned')).toBeDefined()
    expect(screen.getByText(/You are currently not assigned to any response team/i)).toBeDefined()
  })

  it('renders team details, commander ID, and teammates', () => {
    render(<ResponderTeamView team={mockTeams[0]} currentUserId="resp-1" />)

    expect(screen.getByText('Alpha Search & Rescue')).toBeDefined()
    expect(screen.getByText('cmd-1')).toBeDefined()
    expect(screen.getByText('Jane Doe')).toBeDefined()
    expect(screen.getByText('(You)')).toBeDefined()
    expect(screen.getByText('Badge #RSP-101')).toBeDefined()
    expect(screen.getByText('Paramedic')).toBeDefined()
  })
})
