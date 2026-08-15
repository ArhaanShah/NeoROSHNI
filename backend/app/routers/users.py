from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.auth import User, UserMedicalProfile, UserProfile
from app.schemas.auth import (
    UserMedicalProfileResponse,
    UserMedicalProfileUpdateRequest,
    UserMeResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
)

router = APIRouter(prefix="/users", tags=["users"])


def _default_public_code(email: str) -> str:
    local_part = email.split("@", 1)[0][:20].upper()
    timestamp = datetime.now(UTC).strftime("%H%M%S%f")
    return f"U-{local_part}-{timestamp}"


@router.get("/me", response_model=UserMeResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse(
        user_id=str(user.user_id),
        email=user.email,
        phone_number=user.phone_number,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(user: User = Depends(get_current_user)) -> UserProfileResponse:
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.user_id, full_name=user.email)

    return UserProfileResponse(
        user_id=str(user.user_id),
        full_name=profile.full_name,
        date_of_birth=profile.date_of_birth,
        address=profile.address,
        emergency_contact_name=profile.emergency_contact_name,
        emergency_contact_phone=profile.emergency_contact_phone,
    )


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    payload: UserProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.user_id, full_name=payload.full_name or "")
        db.add(profile)

    for field_name, field_value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field_name, field_value)

    await db.commit()
    await db.refresh(profile)

    return UserProfileResponse(
        user_id=str(user.user_id),
        full_name=profile.full_name,
        date_of_birth=profile.date_of_birth,
        address=profile.address,
        emergency_contact_name=profile.emergency_contact_name,
        emergency_contact_phone=profile.emergency_contact_phone,
    )


@router.get("/me/medical", response_model=UserMedicalProfileResponse)
async def get_my_medical(user: User = Depends(get_current_user)) -> UserMedicalProfileResponse:
    medical = user.medical_profile
    if medical is None:
        medical = UserMedicalProfile(
            user_id=user.user_id,
            public_user_code=_default_public_code(user.email),
            consent_flags={},
        )

    return UserMedicalProfileResponse(
        user_id=str(user.user_id),
        public_user_code=medical.public_user_code,
        blood_group=medical.blood_group,
        known_allergies=medical.known_allergies,
        chronic_conditions=medical.chronic_conditions,
        current_medications=medical.current_medications,
        other_medical_notes=medical.other_medical_notes,
        consent_flags=medical.consent_flags,
    )


@router.put("/me/medical", response_model=UserMedicalProfileResponse)
async def update_my_medical(
    payload: UserMedicalProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserMedicalProfileResponse:
    medical = user.medical_profile
    if medical is None:
        medical = UserMedicalProfile(
            user_id=user.user_id,
            public_user_code=_default_public_code(user.email),
            consent_flags={},
        )
        db.add(medical)

    for field_name, field_value in payload.model_dump(exclude_unset=True).items():
        setattr(medical, field_name, field_value)

    await db.commit()
    await db.refresh(medical)

    return UserMedicalProfileResponse(
        user_id=str(user.user_id),
        public_user_code=medical.public_user_code,
        blood_group=medical.blood_group,
        known_allergies=medical.known_allergies,
        chronic_conditions=medical.chronic_conditions,
        current_medications=medical.current_medications,
        other_medical_notes=medical.other_medical_notes,
        consent_flags=medical.consent_flags,
    )
