from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.database import db_session_factory
from app.main import app
from app.models.auth import User
from app.models.team import ResponderProfile
from tests.factories import create_responder, create_team, create_user_with_token


@pytest.mark.asyncio
async def test_account_provisioning_and_login_flow() -> None:
    """Commander provisions a responder; responder can immediately log in and access profile & team."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with db_session_factory() as session:
            _, cmd_token = await create_user_with_token(session, role="commander", email="cmd_prov@example.com")

        # 1. Commander creates a team
        team_res = await client.post(
            "/teams",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"name": "Alpha Search and Rescue"},
        )
        assert team_res.status_code == 201
        team_data = team_res.json()
        team_id = team_data["team_id"]

        # 2. Commander provisions a responder assigned directly to the team
        resp_payload = {
            "email": "medic_john@example.com",
            "password": "StrongPass123!",
            "phone_number": "+15551112233",
            "full_name": "John Medic",
            "badge_number": "MED-001",
            "specialization": "Lead Paramedic",
            "team_id": team_id,
        }
        prov_res = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json=resp_payload,
        )
        assert prov_res.status_code == 201
        created = prov_res.json()
        assert created["email"] == "medic_john@example.com"
        assert created["badge_number"] == "MED-001"
        assert created["team_id"] == team_id
        assert created["team_name"] == "Alpha Search and Rescue"
        assert created["is_active"] is True

        # 3. Commander lists responders
        list_res = await client.get(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert list_res.status_code == 200
        responders = list_res.json()
        assert any(r["badge_number"] == "MED-001" for r in responders)

        # 4. Responder logs in via /auth/login
        login_res = await client.post(
            "/auth/login",
            json={"email": "medic_john@example.com", "password": "StrongPass123!"},
        )
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert "access_token" in login_data
        resp_token = login_data["access_token"]

        # 5. Responder checks /users/me
        me_res = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {resp_token}"},
        )
        assert me_res.status_code == 200
        assert me_res.json()["role"] == "responder"

        # 6. Responder checks /responders/me/team
        my_team_res = await client.get(
            "/responders/me/team",
            headers={"Authorization": f"Bearer {resp_token}"},
        )
        assert my_team_res.status_code == 200
        my_team = my_team_res.json()
        assert my_team["team_id"] == team_id
        assert len(my_team["members"]) == 1
        assert my_team["members"][0]["badge_number"] == "MED-001"


@pytest.mark.asyncio
async def test_atomic_rollback_on_duplicate_conflict() -> None:
    """Duplicate email, phone, or badge fails with 409 and rolls back partial records."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with db_session_factory() as session:
            _, cmd_token = await create_user_with_token(session, role="commander", email="cmd_atomic@example.com")

        base_payload = {
            "email": "atomic_resp@example.com",
            "password": "StrongPass123!",
            "phone_number": "+15552223344",
            "full_name": "Atomic User",
            "badge_number": "ATOMIC-01",
        }

        # Provision first responder successfully
        res1 = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json=base_payload,
        )
        assert res1.status_code == 201

        # Attempt 1: Duplicate Email
        dup_email_payload = {
            **base_payload,
            "phone_number": "+15552223399",
            "badge_number": "ATOMIC-02",
        }
        res_dup_email = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json=dup_email_payload,
        )
        assert res_dup_email.status_code == 409
        assert "Email already registered" in res_dup_email.json()["detail"]

        # Attempt 2: Duplicate Phone Number
        dup_phone_payload = {
            **base_payload,
            "email": "different_email@example.com",
            "badge_number": "ATOMIC-03",
        }
        res_dup_phone = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json=dup_phone_payload,
        )
        assert res_dup_phone.status_code == 409
        assert "Phone number already registered" in res_dup_phone.json()["detail"]

        # Attempt 3: Duplicate Badge Number
        dup_badge_payload = {
            **base_payload,
            "email": "another_email@example.com",
            "phone_number": "+15552223388",
        }
        res_dup_badge = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json=dup_badge_payload,
        )
        assert res_dup_badge.status_code == 409
        assert "Badge number already registered" in res_dup_badge.json()["detail"]

        # Verify database state: no orphan User records created for the failed attempts
        async with db_session_factory() as session:
            diff_user = await session.scalar(select(User).where(User.email == "different_email@example.com"))
            another_user = await session.scalar(select(User).where(User.email == "another_email@example.com"))
            assert diff_user is None
            assert another_user is None


@pytest.mark.asyncio
async def test_team_lifecycle_create_get_update_list_delete() -> None:
    """Commander creates, gets, updates, lists, and deletes a team."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with db_session_factory() as session:
            _, cmd_token = await create_user_with_token(session, role="commander", email="cmd_life@example.com")

        # 1. Create team
        create_res = await client.post(
            "/teams",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"name": "Bravo Logistics"},
        )
        assert create_res.status_code == 201
        team_id = create_res.json()["team_id"]
        assert create_res.json()["name"] == "Bravo Logistics"
        assert create_res.json()["member_count"] == 0

        # 2. Get team detail
        get_res = await client.get(
            f"/teams/{team_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "Bravo Logistics"
        assert get_res.json()["members"] == []

        # 3. Update team name via PATCH
        patch_res = await client.patch(
            f"/teams/{team_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"name": "Bravo Rapid Logistics"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["name"] == "Bravo Rapid Logistics"

        # 4. Update team name via PUT
        put_res = await client.put(
            f"/teams/{team_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"name": "Bravo Heavy Logistics"},
        )
        assert put_res.status_code == 200
        assert put_res.json()["name"] == "Bravo Heavy Logistics"

        # 5. List teams
        list_res = await client.get(
            "/teams",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert list_res.status_code == 200
        teams = list_res.json()
        team_entry = next(t for t in teams if t["team_id"] == team_id)
        assert team_entry["name"] == "Bravo Heavy Logistics"

        # 6. Delete team
        del_res = await client.delete(
            f"/teams/{team_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert del_res.status_code == 200

        # 7. Verify 404 after deletion
        get_deleted = await client.get(
            f"/teams/{team_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_membership_transitions_and_roster() -> None:
    """Assign responder to Team A -> Reassign to Team B -> Unassign from Team B."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with db_session_factory() as session:
            cmd, cmd_token = await create_user_with_token(session, role="commander", email="cmd_trans@example.com")
            team_a = await create_team(session, cmd, name="Team Alpha")
            team_b = await create_team(session, cmd, name="Team Beta")
            resp_user, _ = await create_responder(session, email="resp_trans@example.com", badge_number="TR-100")

        resp_id = str(resp_user.user_id)
        team_a_id = str(team_a.team_id)
        team_b_id = str(team_b.team_id)

        # 1. Assign to Team Alpha
        assign_a = await client.post(
            f"/teams/{team_a_id}/members",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"responder_id": resp_id},
        )
        assert assign_a.status_code == 200
        assert assign_a.json()["team_id"] == team_a_id
        assert assign_a.json()["team_name"] == "Team Alpha"

        # Check Team Alpha roster
        t_a_detail = (await client.get(f"/teams/{team_a_id}", headers={"Authorization": f"Bearer {cmd_token}"})).json()
        assert len(t_a_detail["members"]) == 1
        assert t_a_detail["members"][0]["user_id"] == resp_id

        # 2. Reassign to Team Beta
        assign_b = await client.post(
            f"/teams/{team_b_id}/members",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"responder_id": resp_id},
        )
        assert assign_b.status_code == 200
        assert assign_b.json()["team_id"] == team_b_id
        assert assign_b.json()["team_name"] == "Team Beta"

        # Verify Team Alpha has 0 members and Team Beta has 1 member
        t_a_check = (await client.get(f"/teams/{team_a_id}", headers={"Authorization": f"Bearer {cmd_token}"})).json()
        t_b_check = (await client.get(f"/teams/{team_b_id}", headers={"Authorization": f"Bearer {cmd_token}"})).json()
        assert len(t_a_check["members"]) == 0
        assert len(t_b_check["members"]) == 1

        # 3. Trying to remove from Team Alpha returns 400 (responder is on Team Beta)
        wrong_remove = await client.delete(
            f"/teams/{team_a_id}/members/{resp_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert wrong_remove.status_code == 400
        assert "not assigned to this team" in wrong_remove.json()["detail"]

        # 4. Remove from Team Beta
        remove_b = await client.delete(
            f"/teams/{team_b_id}/members/{resp_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert remove_b.status_code == 200

        # Verify responder is now unassigned
        async with db_session_factory() as session:
            profile = await session.get(ResponderProfile, resp_user.user_id)
            assert profile is not None
            assert profile.team_id is None


@pytest.mark.asyncio
async def test_negative_permission_gates() -> None:
    """Exhaustive negative role matrix: civilians and unauthorized roles rejected with 403."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with db_session_factory() as session:
            _, civ_token = await create_user_with_token(session, role="civilian", email="civ_perm@example.com")
            _, resp_token = await create_user_with_token(session, role="responder", email="resp_perm@example.com")
            _, cmd_token = await create_user_with_token(session, role="commander", email="cmd_perm@example.com")

        fake_id = str(uuid4())
        resp_payload = {
            "email": "fake_resp@example.com",
            "password": "StrongPass123!",
            "phone_number": "+15559998877",
            "full_name": "Fake Responder",
            "badge_number": "FAKE-01",
        }

        # --- Civilian Forbidden from ALL Team/Responder endpoints ---
        assert (
            await client.post(
                "/commander/responders",
                headers={"Authorization": f"Bearer {civ_token}"},
                json=resp_payload,
            )
        ).status_code == 403

        assert (
            await client.get("/commander/responders", headers={"Authorization": f"Bearer {civ_token}"})
        ).status_code == 403

        assert (
            await client.post("/teams", headers={"Authorization": f"Bearer {civ_token}"}, json={"name": "Team"})
        ).status_code == 403

        assert (await client.get("/teams", headers={"Authorization": f"Bearer {civ_token}"})).status_code == 403

        assert (
            await client.get(f"/teams/{fake_id}", headers={"Authorization": f"Bearer {civ_token}"})
        ).status_code == 403

        assert (
            await client.patch(
                f"/teams/{fake_id}", headers={"Authorization": f"Bearer {civ_token}"}, json={"name": "T"}
            )
        ).status_code == 403

        assert (
            await client.put(f"/teams/{fake_id}", headers={"Authorization": f"Bearer {civ_token}"}, json={"name": "T"})
        ).status_code == 403

        assert (
            await client.delete(f"/teams/{fake_id}", headers={"Authorization": f"Bearer {civ_token}"})
        ).status_code == 403

        assert (
            await client.post(
                f"/teams/{fake_id}/members",
                headers={"Authorization": f"Bearer {civ_token}"},
                json={"responder_id": fake_id},
            )
        ).status_code == 403

        assert (
            await client.delete(f"/teams/{fake_id}/members/{fake_id}", headers={"Authorization": f"Bearer {civ_token}"})
        ).status_code == 403

        assert (
            await client.get("/responders/me/team", headers={"Authorization": f"Bearer {civ_token}"})
        ).status_code == 403

        # --- Responder Forbidden from Commander-Only Routes ---
        assert (
            await client.post(
                "/commander/responders",
                headers={"Authorization": f"Bearer {resp_token}"},
                json=resp_payload,
            )
        ).status_code == 403

        assert (
            await client.get("/commander/responders", headers={"Authorization": f"Bearer {resp_token}"})
        ).status_code == 403

        assert (
            await client.post("/teams", headers={"Authorization": f"Bearer {resp_token}"}, json={"name": "Team"})
        ).status_code == 403

        assert (
            await client.patch(
                f"/teams/{fake_id}", headers={"Authorization": f"Bearer {resp_token}"}, json={"name": "T"}
            )
        ).status_code == 403

        assert (
            await client.put(f"/teams/{fake_id}", headers={"Authorization": f"Bearer {resp_token}"}, json={"name": "T"})
        ).status_code == 403

        assert (
            await client.delete(f"/teams/{fake_id}", headers={"Authorization": f"Bearer {resp_token}"})
        ).status_code == 403

        assert (
            await client.post(
                f"/teams/{fake_id}/members",
                headers={"Authorization": f"Bearer {resp_token}"},
                json={"responder_id": fake_id},
            )
        ).status_code == 403

        assert (
            await client.delete(
                f"/teams/{fake_id}/members/{fake_id}", headers={"Authorization": f"Bearer {resp_token}"}
            )
        ).status_code == 403

        # --- Commander Forbidden from Responder-Only Self-Service ---
        assert (
            await client.get("/responders/me/team", headers={"Authorization": f"Bearer {cmd_token}"})
        ).status_code == 403

        # --- Unauthenticated Requests Return 401 ---
        assert (await client.get("/teams")).status_code == 401
        assert (await client.post("/teams", json={"name": "T"})).status_code == 401
        assert (await client.get("/responders/me/team")).status_code == 401


@pytest.mark.asyncio
async def test_responder_self_service_assigned_and_unassigned() -> None:
    """Responder self-service team query returns team info when assigned and None when unassigned."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with db_session_factory() as session:
            cmd, _ = await create_user_with_token(session, role="commander", email="cmd_self@example.com")
            team = await create_team(session, cmd, name="Echo Team")
            _, token_unassigned = await create_user_with_token(
                session, role="responder", email="resp_unassigned@example.com"
            )
            resp_assigned, token_assigned = await create_user_with_token(
                session, role="responder", email="resp_assigned@example.com"
            )
            # Add responder profile with team
            session.add(
                ResponderProfile(
                    user_id=resp_assigned.user_id,
                    team_id=team.team_id,
                    badge_number="ECHO-01",
                )
            )
            await session.commit()

        # Unassigned responder gets 200 with null
        res_unassigned = await client.get(
            "/responders/me/team",
            headers={"Authorization": f"Bearer {token_unassigned}"},
        )
        assert res_unassigned.status_code == 200
        assert res_unassigned.json() is None

        # Assigned responder gets 200 with team details and roster
        res_assigned = await client.get(
            "/responders/me/team",
            headers={"Authorization": f"Bearer {token_assigned}"},
        )
        assert res_assigned.status_code == 200
        data = res_assigned.json()
        assert data["name"] == "Echo Team"
        assert len(data["members"]) == 1
        assert data["members"][0]["badge_number"] == "ECHO-01"


@pytest.mark.asyncio
async def test_orphan_safety_on_team_deletion() -> None:
    """Deleting a team sets member team_id to None; responder user and profile accounts remain intact."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with db_session_factory() as session:
            cmd, cmd_token = await create_user_with_token(session, role="commander", email="cmd_orphan@example.com")
            team = await create_team(session, cmd, name="Sierra Rescue")
            resp_user, _ = await create_responder(
                session, email="sierra_resp@example.com", badge_number="SIE-001", team=team
            )

        team_id = str(team.team_id)
        resp_id = resp_user.user_id

        # Delete team
        del_res = await client.delete(
            f"/teams/{team_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert del_res.status_code == 200

        # Verify DB state: team is deleted, responder exists with team_id=None
        async with db_session_factory() as session:
            saved_resp = await session.get(User, resp_id)
            assert saved_resp is not None
            assert saved_resp.is_active is True

            saved_profile = await session.get(ResponderProfile, resp_id)
            assert saved_profile is not None
            assert saved_profile.team_id is None
            assert saved_profile.badge_number == "SIE-001"


@pytest.mark.asyncio
async def test_not_found_edge_cases() -> None:
    """Non-existent IDs return 404 for all relevant operations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with db_session_factory() as session:
            cmd, cmd_token = await create_user_with_token(session, role="commander", email="cmd_nf@example.com")
            team = await create_team(session, cmd, name="Real Team")

        fake_team_id = str(uuid4())
        fake_resp_id = str(uuid4())
        real_team_id = str(team.team_id)

        # 1. Provision responder with non-existent team -> 404
        bad_prov = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={
                "email": "nf_resp@example.com",
                "password": "StrongPass123!",
                "phone_number": "+1555000099",
                "full_name": "NF Responder",
                "badge_number": "NF-001",
                "team_id": fake_team_id,
            },
        )
        assert bad_prov.status_code == 404

        # 2. Get non-existent team -> 404
        assert (
            await client.get(f"/teams/{fake_team_id}", headers={"Authorization": f"Bearer {cmd_token}"})
        ).status_code == 404

        # 3. Update non-existent team -> 404
        assert (
            await client.patch(
                f"/teams/{fake_team_id}",
                headers={"Authorization": f"Bearer {cmd_token}"},
                json={"name": "New"},
            )
        ).status_code == 404

        # 4. Delete non-existent team -> 404
        assert (
            await client.delete(f"/teams/{fake_team_id}", headers={"Authorization": f"Bearer {cmd_token}"})
        ).status_code == 404

        # 5. Add member to non-existent team -> 404
        assert (
            await client.post(
                f"/teams/{fake_team_id}/members",
                headers={"Authorization": f"Bearer {cmd_token}"},
                json={"responder_id": fake_resp_id},
            )
        ).status_code == 404

        # 6. Add non-existent responder to real team -> 404
        assert (
            await client.post(
                f"/teams/{real_team_id}/members",
                headers={"Authorization": f"Bearer {cmd_token}"},
                json={"responder_id": fake_resp_id},
            )
        ).status_code == 404

        # 7. Delete member from non-existent team -> 404
        assert (
            await client.delete(
                f"/teams/{fake_team_id}/members/{fake_resp_id}",
                headers={"Authorization": f"Bearer {cmd_token}"},
            )
        ).status_code == 404

        # 8. Delete non-existent responder from real team -> 404
        assert (
            await client.delete(
                f"/teams/{real_team_id}/members/{fake_resp_id}",
                headers={"Authorization": f"Bearer {cmd_token}"},
            )
        ).status_code == 404
