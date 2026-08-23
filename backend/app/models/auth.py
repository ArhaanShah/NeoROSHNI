from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from app.models.team import ResponderProfile, Team


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    medical_profile: Mapped["UserMedicalProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    responder_profile: Mapped["ResponderProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    commanded_teams: Mapped[list["Team"]] = relationship(
        back_populates="commander",
        cascade="all, delete-orphan",
        foreign_keys="Team.commander_id",
    )

    __table_args__ = (
        CheckConstraint("role IN ('civilian', 'responder', 'commander')", name="ck_users_role"),
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("phone_number", name="uq_user_phone_number"),
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_phone_number", "phone_number", unique=True),
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="profile")


class UserMedicalProfile(Base):
    __tablename__ = "user_medical_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    public_user_code: Mapped[str] = mapped_column(String(50), nullable=False)
    blood_group: Mapped[str | None] = mapped_column(String(10), nullable=True)
    known_allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    chronic_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_medications: Mapped[str | None] = mapped_column(Text, nullable=True)
    other_medical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_flags: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="medical_profile")

    __table_args__ = (
        UniqueConstraint("public_user_code", name="uq_user_medical_profiles_public_user_code"),
        Index("ix_user_medical_profiles_public_user_code", "public_user_code", unique=True),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    refresh_token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        Index("ix_refresh_tokens_token_hash", "token_hash", unique=True),
    )
