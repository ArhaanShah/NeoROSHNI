import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.database import db_session_factory
from app.models.auth import User
from app.models.team import ResponderProfile, Team


@pytest.mark.asyncio
async def test_team_and_responder_creation_and_relationships() -> None:
    async with db_session_factory() as session:
        commander = User(email="cmd@example.com", hashed_password="h", phone_number="+15550001", role="commander")
        session.add(commander)
        await session.flush()

        team = Team(name="Alpha Rescue", commander_id=commander.user_id)
        session.add(team)
        await session.flush()

        responder = User(email="resp@example.com", hashed_password="h", phone_number="+15550002", role="responder")
        session.add(responder)
        await session.flush()

        profile = ResponderProfile(
            user_id=responder.user_id, team_id=team.team_id, badge_number="B-101", specialization="Medic"
        )
        session.add(profile)
        await session.commit()

        # Verify relationship traversal
        res = await session.execute(
            select(Team)
            .where(Team.team_id == team.team_id)
            .options(selectinload(Team.commander), selectinload(Team.members).selectinload(ResponderProfile.user))
        )
        saved = res.scalar_one()
        assert saved.name == "Alpha Rescue"
        assert saved.commander.email == "cmd@example.com"
        assert len(saved.members) == 1
        assert saved.members[0].badge_number == "B-101"
        assert saved.members[0].user.email == "resp@example.com"


@pytest.mark.asyncio
async def test_duplicate_badge_number_rejected() -> None:
    async with db_session_factory() as session:
        u1 = User(email="u1@example.com", hashed_password="h", phone_number="+15550003", role="responder")
        u2 = User(email="u2@example.com", hashed_password="h", phone_number="+15550004", role="responder")
        session.add_all([u1, u2])
        await session.flush()

        session.add(ResponderProfile(user_id=u1.user_id, badge_number="B-DUP"))
        await session.flush()

        session.add(ResponderProfile(user_id=u2.user_id, badge_number="B-DUP"))
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()


@pytest.mark.asyncio
async def test_team_deletion_unlinks_responder_without_deleting_user() -> None:
    async with db_session_factory() as session:
        cmd = User(email="cmd2@example.com", hashed_password="h", phone_number="+15550005", role="commander")
        session.add(cmd)
        await session.flush()

        team = Team(name="Bravo Team", commander_id=cmd.user_id)
        session.add(team)
        await session.flush()

        resp = User(email="resp2@example.com", hashed_password="h", phone_number="+15550006", role="responder")
        session.add(resp)
        await session.flush()

        profile = ResponderProfile(user_id=resp.user_id, team_id=team.team_id, badge_number="B-102")
        session.add(profile)
        await session.commit()

        await session.delete(team)
        await session.commit()

        res = await session.execute(select(ResponderProfile).where(ResponderProfile.user_id == resp.user_id))
        saved_profile = res.scalar_one_or_none()
        assert saved_profile is not None
        assert saved_profile.team_id is None
