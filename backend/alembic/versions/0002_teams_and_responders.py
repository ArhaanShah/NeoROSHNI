from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_teams_and_responders"
down_revision = "0001_auth_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("team_id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("commander_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["commander_id"], ["users.user_id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_teams_commander_id"), "teams", ["commander_id"], unique=False)
    op.create_index(op.f("ix_teams_name"), "teams", ["name"], unique=False)

    op.create_table(
        "responder_profiles",
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("badge_number", sa.String(length=50), nullable=False),
        sa.Column("specialization", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("badge_number", name="uq_responder_profiles_badge_number"),
    )
    op.create_index(op.f("ix_responder_profiles_badge_number"), "responder_profiles", ["badge_number"], unique=True)
    op.create_index(op.f("ix_responder_profiles_team_id"), "responder_profiles", ["team_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_responder_profiles_team_id"), table_name="responder_profiles")
    op.drop_index(op.f("ix_responder_profiles_badge_number"), table_name="responder_profiles")
    op.drop_table("responder_profiles")
    op.drop_index(op.f("ix_teams_name"), table_name="teams")
    op.drop_index(op.f("ix_teams_commander_id"), table_name="teams")
    op.drop_table("teams")
