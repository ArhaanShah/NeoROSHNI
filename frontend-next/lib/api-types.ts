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
  detail: string
}

/** Shape returned by auth Server Actions on validation/API failure. */
export interface AuthActionError {
  error: string
}
