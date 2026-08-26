from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import db_session_factory
from app.models.auth import RefreshToken, User, UserMedicalProfile, UserProfile


@pytest.mark.asyncio
async def test_auth_models_can_be_inserted_and_retrieved() -> None:
    email = f"auth-smoke-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone_number = f"+1555{datetime.now(UTC).strftime('%f')}"

    async with db_session_factory() as session:
        user = User(
            email=email,
            hashed_password="hashed-password",
            phone_number=phone_number,
            role="civilian",
            is_active=True,
        )
        session.add(user)
        await session.flush()

        profile = UserProfile(
            user_id=user.user_id,
            full_name="Auth Smoke User",
            address="123 Example St",
            emergency_contact_name="Emergency Contact",
            emergency_contact_phone="+15550000001",
        )
        medical = UserMedicalProfile(
            user_id=user.user_id,
            public_user_code=f"AS-{datetime.now(UTC).strftime('%f')}",
            blood_group="O+",
            known_allergies="Peanuts",
            chronic_conditions="None",
            current_medications="Vitamin D",
            other_medical_notes="No major issues",
            consent_flags={"share_medical": True},
        )
        refresh = RefreshToken(
            user_id=user.user_id,
            token_hash=f"abc123hashed-token-{datetime.now(UTC).strftime('%f')}",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        session.add_all([profile, medical, refresh])
        await session.commit()

        result = await session.execute(
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.profile),
                selectinload(User.medical_profile),
                selectinload(User.refresh_tokens),
            )
        )
        saved_user = result.scalar_one()

        assert saved_user.email == email
        assert saved_user.role == "civilian"
        assert saved_user.profile.full_name == "Auth Smoke User"
        assert saved_user.medical_profile.public_user_code.startswith("AS-")
        assert saved_user.refresh_tokens[0].token_hash.startswith("abc123hashed-token-")
