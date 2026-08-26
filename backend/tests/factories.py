from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.auth import User, UserMedicalProfile, UserProfile
from app.models.team import ResponderProfile, Team


def _build_public_code(email: str) -> str:
    local_part = email.split("@", 1)[0][:20].upper()
    timestamp = datetime.now(UTC).strftime("%H%M%S%f")
    return f"U-{local_part}-{timestamp}"


async def create_user(
    session: AsyncSession,
    *,
    email: str | None = None,
    password: str = "StrongPass123!",
    phone_number: str | None = None,
    role: str = "civilian",
    full_name: str = "Test User",
    is_active: bool = True,
) -> User:
    unique_suffix = uuid4().hex[:8]
    user_email = email or f"user_{unique_suffix}@example.com"
    user_phone = phone_number or f"+1555{unique_suffix[:7]}"

    user = User(
        email=user_email,
        hashed_password=hash_password(password),
        phone_number=user_phone,
        role=role,
        is_active=is_active,
    )
    session.add(user)
    await session.flush()

    user_profile = UserProfile(
        user_id=user.user_id,
        full_name=full_name,
    )
    session.add(user_profile)

    medical_profile = UserMedicalProfile(
        user_id=user.user_id,
        public_user_code=_build_public_code(user_email),
        consent_flags={},
    )
    session.add(medical_profile)

    await session.commit()
    await session.refresh(user)
    return user


async def create_user_with_token(
    session: AsyncSession,
    *,
    email: str | None = None,
    password: str = "StrongPass123!",
    phone_number: str | None = None,
    role: str = "civilian",
    full_name: str = "Test User",
    is_active: bool = True,
) -> tuple[User, str]:
    user = await create_user(
        session,
        email=email,
        password=password,
        phone_number=phone_number,
        role=role,
        full_name=full_name,
        is_active=is_active,
    )
    token = create_access_token(user_id=user.user_id, role=user.role)
    return user, token


async def create_team(
    session: AsyncSession,
    commander: User,
    *,
    name: str = "Alpha Search",
) -> Team:
    team = Team(
        name=name,
        commander_id=commander.user_id,
    )
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team


async def create_responder(
    session: AsyncSession,
    *,
    email: str | None = None,
    password: str = "StrongPass123!",
    phone_number: str | None = None,
    full_name: str = "Test Responder",
    badge_number: str | None = None,
    specialization: str | None = "Search and Rescue",
    team: Team | None = None,
    is_active: bool = True,
) -> tuple[User, ResponderProfile]:
    unique_suffix = uuid4().hex[:8]
    user_email = email or f"responder_{unique_suffix}@example.com"
    user_phone = phone_number or f"+1555{unique_suffix[:7]}"
    badge = badge_number or f"B-{unique_suffix[:6].upper()}"

    user = User(
        email=user_email,
        hashed_password=hash_password(password),
        phone_number=user_phone,
        role="responder",
        is_active=is_active,
    )
    session.add(user)
    await session.flush()

    user_profile = UserProfile(
        user_id=user.user_id,
        full_name=full_name,
    )
    session.add(user_profile)

    medical_profile = UserMedicalProfile(
        user_id=user.user_id,
        public_user_code=_build_public_code(user_email),
        consent_flags={},
    )
    session.add(medical_profile)

    responder_profile = ResponderProfile(
        user_id=user.user_id,
        team_id=team.team_id if team else None,
        badge_number=badge,
        specialization=specialization,
    )
    session.add(responder_profile)

    await session.commit()
    await session.refresh(user)
    await session.refresh(responder_profile)
    return user, responder_profile
