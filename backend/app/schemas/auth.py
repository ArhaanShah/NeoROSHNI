from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.validators import validate_optional_phone_number, validate_phone_number


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone_number: str = Field(min_length=8, max_length=32)
    full_name: str = Field(min_length=1, max_length=255)

    @field_validator("phone_number")
    @classmethod
    def phone_number_is_e164(cls, value: str) -> str:
        return validate_phone_number(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: EmailStr
    phone_number: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: str
    date_of_birth: date | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class UserProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    date_of_birth: date | None = None
    address: str | None = None
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=32)

    @field_validator("emergency_contact_phone")
    @classmethod
    def emergency_contact_phone_is_e164(cls, value: str | None) -> str | None:
        return validate_optional_phone_number(value)


class UserMedicalProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    public_user_code: str
    blood_group: str | None = None
    known_allergies: str | None = None
    chronic_conditions: str | None = None
    current_medications: str | None = None
    other_medical_notes: str | None = None
    consent_flags: dict


class UserMedicalProfileUpdateRequest(BaseModel):
    blood_group: str | None = Field(default=None, max_length=10)
    known_allergies: str | None = None
    chronic_conditions: str | None = None
    current_medications: str | None = None
    other_medical_notes: str | None = None
    consent_flags: dict | None = None
