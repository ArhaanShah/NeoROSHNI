from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RoleChecker
from app.core.security import hash_password
from app.database import get_db
from app.models.auth import User, UserMedicalProfile, UserProfile
from app.models.team import ResponderProfile, Team
from app.schemas.team import (
    ResponderCreate,
    ResponderWithUserResponse,
    TeamCreate,
    TeamDetailResponse,
    TeamMemberAddRequest,
    TeamResponse,
)

router = APIRouter(tags=["teams"])


def _build_default_public_code(email: str) -> str:
    local_part = email.split("@", 1)[0][:20].upper()
    timestamp = datetime.now(UTC).strftime("%H%M%S%f")
    return f"U-{local_part}-{timestamp}"


def _build_responder_response(
    profile: ResponderProfile,
    user: User | None = None,
    team_name: str | None = None,
) -> ResponderWithUserResponse:
    resolved_user = user or profile.user
    full_name = resolved_user.profile.full_name if resolved_user and resolved_user.profile else ""
    resolved_team_name = team_name or (profile.team.name if profile.team else None)

    return ResponderWithUserResponse(
        user_id=profile.user_id,
        email=resolved_user.email if resolved_user else "",
        phone_number=resolved_user.phone_number if resolved_user else "",
        full_name=full_name,
        badge_number=profile.badge_number,
        specialization=profile.specialization,
        team_id=profile.team_id,
        team_name=resolved_team_name,
        is_active=resolved_user.is_active if resolved_user else True,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _build_team_detail_response(team: Team) -> TeamDetailResponse:
    members = [_build_responder_response(m, team_name=team.name) for m in team.members]
    return TeamDetailResponse(
        team_id=team.team_id,
        name=team.name,
        commander_id=team.commander_id,
        created_at=team.created_at,
        updated_at=team.updated_at,
        members=members,
    )


# ---------------------------------------------------------
# Commander Responder Management
# ---------------------------------------------------------


@router.post(
    "/commander/responders",
    response_model=ResponderWithUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_responder(
    payload: ResponderCreate,
    current_user: User = Depends(RoleChecker(["commander"])),
    db: AsyncSession = Depends(get_db),
) -> ResponderWithUserResponse:
    existing_user = await db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    existing_phone = await db.scalar(select(User).where(User.phone_number == payload.phone_number))
    if existing_phone is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already registered")

    existing_badge = await db.scalar(
        select(ResponderProfile).where(ResponderProfile.badge_number == payload.badge_number)
    )
    if existing_badge is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Badge number already registered")

    team_name: str | None = None
    if payload.team_id is not None:
        team = await db.get(Team, payload.team_id)
        if team is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        team_name = team.name

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        phone_number=payload.phone_number,
        role="responder",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    user_profile = UserProfile(
        user_id=user.user_id,
        full_name=payload.full_name,
    )
    db.add(user_profile)

    medical_profile = UserMedicalProfile(
        user_id=user.user_id,
        public_user_code=_build_default_public_code(payload.email),
        consent_flags={},
    )
    db.add(medical_profile)

    responder_profile = ResponderProfile(
        user_id=user.user_id,
        team_id=payload.team_id,
        badge_number=payload.badge_number,
        specialization=payload.specialization,
    )
    db.add(responder_profile)

    try:
        await db.commit()
        await db.refresh(responder_profile)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Responder registration conflict") from exc

    return _build_responder_response(responder_profile, user=user, team_name=team_name)


@router.get(
    "/commander/responders",
    response_model=list[ResponderWithUserResponse],
)
async def list_responders(
    current_user: User = Depends(RoleChecker(["commander"])),
    db: AsyncSession = Depends(get_db),
) -> list[ResponderWithUserResponse]:
    stmt = (
        select(ResponderProfile)
        .options(
            selectinload(ResponderProfile.user).selectinload(User.profile),
            selectinload(ResponderProfile.team),
        )
        .order_by(ResponderProfile.created_at.desc())
    )
    results = (await db.scalars(stmt)).all()

    return [_build_responder_response(rp) for rp in results]


# ---------------------------------------------------------
# Team CRUD & Membership Management
# ---------------------------------------------------------


@router.post(
    "/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_team(
    payload: TeamCreate,
    current_user: User = Depends(RoleChecker(["commander"])),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    team = Team(
        name=payload.name,
        commander_id=current_user.user_id,
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)

    return TeamResponse(
        team_id=team.team_id,
        name=team.name,
        commander_id=team.commander_id,
        member_count=0,
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


@router.get(
    "/teams",
    response_model=list[TeamResponse],
)
async def list_teams(
    current_user: User = Depends(RoleChecker(["commander", "responder"])),
    db: AsyncSession = Depends(get_db),
) -> list[TeamResponse]:
    stmt = (
        select(Team)
        .options(selectinload(Team.members))
        .order_by(Team.created_at.desc())
    )
    teams = (await db.scalars(stmt)).all()

    return [
        TeamResponse(
            team_id=t.team_id,
            name=t.name,
            commander_id=t.commander_id,
            member_count=len(t.members),
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in teams
    ]


@router.get(
    "/teams/{team_id}",
    response_model=TeamDetailResponse,
)
async def get_team(
    team_id: UUID,
    current_user: User = Depends(RoleChecker(["commander", "responder"])),
    db: AsyncSession = Depends(get_db),
) -> TeamDetailResponse:
    stmt = (
        select(Team)
        .where(Team.team_id == team_id)
        .options(
            selectinload(Team.members).selectinload(ResponderProfile.user).selectinload(User.profile),
        )
    )
    team = (await db.scalars(stmt)).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    return _build_team_detail_response(team)


@router.delete(
    "/teams/{team_id}",
)
async def delete_team(
    team_id: UUID,
    current_user: User = Depends(RoleChecker(["commander"])),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    team = await db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    await db.execute(
        update(ResponderProfile)
        .where(ResponderProfile.team_id == team_id)
        .values(team_id=None)
    )
    await db.delete(team)
    await db.commit()

    return {"message": "Team deleted successfully"}


@router.post(
    "/teams/{team_id}/members",
    response_model=ResponderWithUserResponse,
)
async def add_team_member(
    team_id: UUID,
    payload: TeamMemberAddRequest,
    current_user: User = Depends(RoleChecker(["commander"])),
    db: AsyncSession = Depends(get_db),
) -> ResponderWithUserResponse:
    team = await db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    stmt = (
        select(ResponderProfile)
        .where(ResponderProfile.user_id == payload.responder_id)
        .options(
            selectinload(ResponderProfile.user).selectinload(User.profile),
        )
    )
    responder_profile = (await db.scalars(stmt)).first()
    if responder_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responder not found")

    responder_profile.team_id = team_id
    await db.commit()
    await db.refresh(responder_profile)

    return _build_responder_response(responder_profile, team_name=team.name)


@router.delete(
    "/teams/{team_id}/members/{responder_id}",
)
async def remove_team_member(
    team_id: UUID,
    responder_id: UUID,
    current_user: User = Depends(RoleChecker(["commander"])),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    team = await db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    responder_profile = await db.get(ResponderProfile, responder_id)
    if responder_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responder not found")

    if responder_profile.team_id != team_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Responder is not assigned to this team")

    responder_profile.team_id = None
    await db.commit()

    return {"message": "Responder unassigned from team"}


# ---------------------------------------------------------
# Responder Self-Service
# ---------------------------------------------------------


@router.get(
    "/responders/me/team",
    response_model=TeamDetailResponse | None,
)
async def get_my_team(
    current_user: User = Depends(RoleChecker(["responder"])),
    db: AsyncSession = Depends(get_db),
) -> TeamDetailResponse | None:
    stmt = select(ResponderProfile).where(ResponderProfile.user_id == current_user.user_id)
    responder_profile = (await db.scalars(stmt)).first()
    if responder_profile is None or responder_profile.team_id is None:
        return None

    team_stmt = (
        select(Team)
        .where(Team.team_id == responder_profile.team_id)
        .options(
            selectinload(Team.members).selectinload(ResponderProfile.user).selectinload(User.profile),
        )
    )
    team = (await db.scalars(team_stmt)).first()
    if team is None:
        return None

    return _build_team_detail_response(team)
