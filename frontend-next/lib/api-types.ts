/**
 * TypeScript types mirroring FastAPI auth schemas.
 * Keep in sync with backend/app/schemas/auth.py.
 */

export interface TokenPairResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export type UserRole = 'civilian' | 'responder' | 'commander'

export interface UserMeResponse {
  user_id: string
  email: string
  phone_number: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserProfileResponse {
  user_id: string
  full_name: string
  date_of_birth: string | null
  address: string | null
  emergency_contact_name: string | null
  emergency_contact_phone: string | null
}

export interface UserMedicalProfileResponse {
  user_id: string
  public_user_code: string
  blood_group: string | null
  known_allergies: string | null
  chronic_conditions: string | null
  current_medications: string | null
  other_medical_notes: string | null
  consent_flags: Record<string, unknown>
}

export interface ApiError {
  detail: string | Array<{ loc: (string | number)[]; msg: string; type: string }>
}

/** Shape returned by auth & team Server Actions on validation/API failure. */
export interface ActionError {
  error: string
}

export type AuthActionError = ActionError
export type TeamActionError = ActionError

// ---------------------------------------------------------------------------
// Team & Responder Types (Sprint 2 C4)
// ---------------------------------------------------------------------------

export interface TeamCreate {
  name: string
}

export interface TeamUpdate {
  name?: string | null
}

export interface TeamMemberAddRequest {
  responder_id: string
}

export interface ResponderCreate {
  email: string
  password: string
  phone_number: string
  full_name: string
  badge_number: string
  specialization?: string | null
  team_id?: string | null
}

export interface ResponderProfileResponse {
  user_id: string
  team_id: string | null
  badge_number: string
  specialization: string | null
  created_at: string
  updated_at: string
}

export interface ResponderWithUserResponse {
  user_id: string
  email: string
  phone_number: string
  full_name: string
  badge_number: string
  specialization: string | null
  team_id: string | null
  team_name: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TeamResponse {
  team_id: string
  name: string
  commander_id: string
  member_count: number
  created_at: string
  updated_at: string
}

export interface TeamDetailResponse {
  team_id: string
  name: string
  commander_id: string
  created_at: string
  updated_at: string
  members: ResponderWithUserResponse[]
}
