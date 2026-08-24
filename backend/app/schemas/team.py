from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.validators import (
    sanitize_string,
    validate_badge_number,
    validate_phone_number,
)


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return sanitize_string(value, min_length=1, max_length=255)


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return sanitize_string(value, min_length=1, max_length=255)


class TeamMemberAddRequest(BaseModel):
    responder_id: UUID


class ResponderCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone_number: str = Field(min_length=8, max_length=32)
    full_name: str = Field(min_length=1, max_length=255)
    badge_number: str = Field(min_length=2, max_length=50)
    specialization: str | None = Field(default=None, max_length=255)
    team_id: UUID | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_phone_number(value)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        return sanitize_string(value, min_length=1, max_length=255)

    @field_validator("badge_number")
    @classmethod
    def validate_badge(cls, value: str) -> str:
        return validate_badge_number(value)

    @field_validator("specialization")
    @classmethod
    def validate_spec(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned if cleaned else None


class ResponderProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    team_id: UUID | None = None
    badge_number: str
    specialization: str | None = None
    created_at: datetime
    updated_at: datetime


class ResponderWithUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: EmailStr
    phone_number: str
    full_name: str
    badge_number: str
    specialization: str | None = None
    team_id: UUID | None = None
    team_name: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID
    name: str
    commander_id: UUID
    member_count: int = 0
    created_at: datetime
    updated_at: datetime


class TeamDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID
    name: str
    commander_id: UUID
    created_at: datetime
    updated_at: datetime
    members: list[ResponderWithUserResponse] = Field(default_factory=list)
