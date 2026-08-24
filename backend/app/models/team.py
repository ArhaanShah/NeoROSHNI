from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.auth import User


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    commander_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    commander: Mapped["User"] = relationship(
        back_populates="commanded_teams",
        foreign_keys=[commander_id],
    )
    members: Mapped[list["ResponderProfile"]] = relationship(
        back_populates="team",
    )

    __table_args__ = (
        Index("ix_teams_name", "name"),
        Index("ix_teams_commander_id", "commander_id"),
    )


class ResponderProfile(Base):
    __tablename__ = "responder_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id", ondelete="SET NULL"),
        nullable=True,
    )
    badge_number: Mapped[str] = mapped_column(String(50), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(
        back_populates="responder_profile",
    )
    team: Mapped["Team | None"] = relationship(
        back_populates="members",
    )

    __table_args__ = (
        UniqueConstraint("badge_number", name="uq_responder_profiles_badge_number"),
        Index("ix_responder_profiles_badge_number", "badge_number", unique=True),
        Index("ix_responder_profiles_team_id", "team_id"),
    )
