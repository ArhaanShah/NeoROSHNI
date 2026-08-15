from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.database import get_db
from app.models.auth import RefreshToken, User, UserMedicalProfile, UserProfile
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, TokenPairResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_default_public_code(email: str) -> str:
    local_part = email.split("@", 1)[0][:20].upper()
    timestamp = datetime.now(UTC).strftime("%H%M%S%f")
    return f"U-{local_part}-{timestamp}"


async def _issue_token_pair(db: AsyncSession, user: User) -> TokenPairResponse:
    access_token = create_access_token(user.user_id, user.role)
    refresh_token, expires_at = create_refresh_token(user.user_id)

    db.add(
        RefreshToken(
            user_id=user.user_id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )
    )
    await db.commit()

    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=TokenPairResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenPairResponse:
    existing_user = await db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    existing_phone = await db.scalar(select(User).where(User.phone_number == payload.phone_number))
    if existing_phone is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        phone_number=payload.phone_number,
        role="civilian",
        is_active=True,
    )

    db.add(user)
    await db.flush()

    db.add(
        UserProfile(
            user_id=user.user_id,
            full_name=payload.full_name,
        )
    )
    db.add(
        UserMedicalProfile(
            user_id=user.user_id,
            public_user_code=_build_default_public_code(payload.email),
            consent_flags={},
        )
    )

    try:
        return await _issue_token_pair(db, user)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User registration conflict") from exc


@router.post("/login", response_model=TokenPairResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPairResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")

    return await _issue_token_pair(db, user)


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPairResponse:
    decode_token(payload.refresh_token, expected_type="refresh")

    token_hash = hash_refresh_token(payload.refresh_token)
    token_record = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if token_record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown refresh token")

    if token_record.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    now = datetime.now(UTC)
    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = await db.get(User, token_record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    token_record.revoked_at = now
    await db.flush()

    access_token = create_access_token(user.user_id, user.role)
    new_refresh_token, new_expires_at = create_refresh_token(user.user_id)
    db.add(
        RefreshToken(
            user_id=user.user_id,
            token_hash=hash_refresh_token(new_refresh_token),
            expires_at=new_expires_at,
        )
    )
    await db.commit()

    return TokenPairResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        decode_token(payload.refresh_token, expected_type="refresh")
    except HTTPException:
        # Logout should be idempotent and not leak token validity details.
        return {"message": "Logged out"}

    token_hash = hash_refresh_token(payload.refresh_token)
    token_record = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if token_record is not None and token_record.revoked_at is None:
        token_record.revoked_at = datetime.now(UTC)
        await db.commit()

    return {"message": "Logged out"}
