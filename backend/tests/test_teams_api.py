from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.security import create_access_token, hash_password
from app.database import db_session_factory
from app.main import app
from app.models.auth import User


async def _create_user(email: str, phone: str, role: str) -> tuple[User, str]:
    async with db_session_factory() as session:
        user = User(
            email=email,
            hashed_password=hash_password("StrongPass123!"),
            phone_number=phone,
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = create_access_token(user_id=user.user_id, role=user.role)
        return user, token


@pytest.mark.asyncio
async def test_commander_provision_responder_and_login() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        _, cmd_token = await _create_user("commander1@example.com", "+1555100001", "commander")

        # 1. Commander creates team
        team_res = await client.post(
            "/teams",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"name": "Bravo Search"},
        )
        assert team_res.status_code == 201
        team_data = team_res.json()
        team_id = team_data["team_id"]

        # 2. Commander creates responder with team assignment
        resp_payload = {
            "email": "resp1@example.com",
            "password": "StrongPass123!",
            "phone_number": "+1555100002",
            "full_name": "John Responder",
            "badge_number": "B-001",
            "specialization": "Paramedic",
            "team_id": team_id,
        }
        create_res = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json=resp_payload,
        )
        assert create_res.status_code == 201
        created = create_res.json()
        assert created["email"] == "resp1@example.com"
        assert created["badge_number"] == "B-001"
        assert created["team_id"] == team_id
        assert created["team_name"] == "Bravo Search"

        # 3. Newly created responder can log in
        login_res = await client.post(
            "/auth/login",
            json={"email": "resp1@example.com", "password": "StrongPass123!"},
        )
        assert login_res.status_code == 200
        resp_token = login_res.json()["access_token"]

        # 4. Responder checks /responders/me/team
        me_team = await client.get(
            "/responders/me/team",
            headers={"Authorization": f"Bearer {resp_token}"},
        )
        assert me_team.status_code == 200
        team_detail = me_team.json()
        assert team_detail is not None
        assert team_detail["team_id"] == team_id
        assert len(team_detail["members"]) == 1
        assert team_detail["members"][0]["badge_number"] == "B-001"


@pytest.mark.asyncio
async def test_duplicate_responder_provision_fails_with_409() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        _, cmd_token = await _create_user("commander2@example.com", "+1555100003", "commander")

        resp_payload = {
            "email": "resp2@example.com",
            "password": "StrongPass123!",
            "phone_number": "+1555100004",
            "full_name": "Jane Responder",
            "badge_number": "B-002",
        }
        res1 = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json=resp_payload,
        )
        assert res1.status_code == 201

        # Duplicate email
        res2 = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={**resp_payload, "phone_number": "+1555100005", "badge_number": "B-003"},
        )
        assert res2.status_code == 409

        # Duplicate phone
        res3 = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={**resp_payload, "email": "other@example.com", "badge_number": "B-004"},
        )
        assert res3.status_code == 409

        # Duplicate badge number
        res4 = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={**resp_payload, "email": "other2@example.com", "phone_number": "+1555100006"},
        )
        assert res4.status_code == 409


@pytest.mark.asyncio
async def test_team_lifecycle_and_membership_transitions() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        _, cmd_token = await _create_user("commander3@example.com", "+1555100010", "commander")

        # Create two teams
        team_a = (
            await client.post(
                "/teams",
                headers={"Authorization": f"Bearer {cmd_token}"},
                json={"name": "Team Alpha"},
            )
        ).json()
        team_b = (
            await client.post(
                "/teams",
                headers={"Authorization": f"Bearer {cmd_token}"},
                json={"name": "Team Bravo"},
            )
        ).json()

        # Create responder unassigned
        resp = (
            await client.post(
                "/commander/responders",
                headers={"Authorization": f"Bearer {cmd_token}"},
                json={
                    "email": "resp3@example.com",
                    "password": "StrongPass123!",
                    "phone_number": "+1555100011",
                    "full_name": "Bob Medic",
                    "badge_number": "B-003",
                    "specialization": "K9 Handler",
                },
            )
        ).json()
        resp_id = resp["user_id"]

        # List responders
        responders_list = await client.get(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert responders_list.status_code == 200
        assert any(r["badge_number"] == "B-003" for r in responders_list.json())

        # Assign responder to Team Alpha
        add_res = await client.post(
            f"/teams/{team_a['team_id']}/members",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"responder_id": resp_id},
        )
        assert add_res.status_code == 200
        assert add_res.json()["team_id"] == team_a["team_id"]

        # Check team list member count
        teams_res = await client.get(
            "/teams",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert teams_res.status_code == 200
        t_a = next(t for t in teams_res.json() if t["team_id"] == team_a["team_id"])
        assert t_a["member_count"] == 1

        # Reassign responder to Team Bravo
        reassign_res = await client.post(
            f"/teams/{team_b['team_id']}/members",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"responder_id": resp_id},
        )
        assert reassign_res.status_code == 200
        assert reassign_res.json()["team_id"] == team_b["team_id"]

        # Removing from wrong team returns 400
        bad_remove = await client.delete(
            f"/teams/{team_a['team_id']}/members/{resp_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert bad_remove.status_code == 400

        # Remove from Team Bravo
        remove_res = await client.delete(
            f"/teams/{team_b['team_id']}/members/{resp_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert remove_res.status_code == 200

        # Delete Team Alpha
        del_res = await client.delete(
            f"/teams/{team_a['team_id']}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert del_res.status_code == 200

        # Team Alpha is gone
        get_deleted = await client.get(
            f"/teams/{team_a['team_id']}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_role_rejection_matrix() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        _, civilian_token = await _create_user("civ@example.com", "+1555100020", "civilian")
        _, resp_token = await _create_user("resp_role@example.com", "+1555100021", "responder")
        _, cmd_token = await _create_user("cmd_role@example.com", "+1555100022", "commander")

        fake_id = str(uuid4())

        # Civilian forbidden from everything
        assert (
            await client.post(
                "/commander/responders",
                headers={"Authorization": f"Bearer {civilian_token}"},
                json={
                    "email": "a@a.com",
                    "password": "pass",
                    "phone_number": "+1",
                    "full_name": "a",
                    "badge_number": "1",
                },
            )
        ).status_code == 403

        assert (
            await client.get("/commander/responders", headers={"Authorization": f"Bearer {civilian_token}"})
        ).status_code == 403

        assert (
            await client.post("/teams", headers={"Authorization": f"Bearer {civilian_token}"}, json={"name": "T"})
        ).status_code == 403

        assert (await client.get("/teams", headers={"Authorization": f"Bearer {civilian_token}"})).status_code == 403

        assert (
            await client.get(f"/teams/{fake_id}", headers={"Authorization": f"Bearer {civilian_token}"})
        ).status_code == 403

        assert (
            await client.delete(f"/teams/{fake_id}", headers={"Authorization": f"Bearer {civilian_token}"})
        ).status_code == 403

        assert (
            await client.get("/responders/me/team", headers={"Authorization": f"Bearer {civilian_token}"})
        ).status_code == 403

        # Responder forbidden from commander routes
        assert (
            await client.post(
                "/commander/responders",
                headers={"Authorization": f"Bearer {resp_token}"},
                json={
                    "email": "a@a.com",
                    "password": "pass",
                    "phone_number": "+1",
                    "full_name": "a",
                    "badge_number": "1",
                },
            )
        ).status_code == 403

        assert (
            await client.get("/commander/responders", headers={"Authorization": f"Bearer {resp_token}"})
        ).status_code == 403

        assert (
            await client.post("/teams", headers={"Authorization": f"Bearer {resp_token}"}, json={"name": "T"})
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

        # Commander forbidden from responder-only route
        assert (
            await client.get("/responders/me/team", headers={"Authorization": f"Bearer {cmd_token}"})
        ).status_code == 403


@pytest.mark.asyncio
async def test_responder_unassigned_me_team_returns_null() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        _, cmd_token = await _create_user("commander4@example.com", "+1555100030", "commander")

        # Provision responder with no team
        await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={
                "email": "unassigned@example.com",
                "password": "StrongPass123!",
                "phone_number": "+1555100031",
                "full_name": "Solo Responder",
                "badge_number": "B-SOLO",
            },
        )

        login = await client.post(
            "/auth/login",
            json={"email": "unassigned@example.com", "password": "StrongPass123!"},
        )
        token = login.json()["access_token"]

        res = await client.get("/responders/me/team", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json() is None


@pytest.mark.asyncio
async def test_not_found_scenarios() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        _, cmd_token = await _create_user("commander5@example.com", "+1555100040", "commander")
        fake_team_id = str(uuid4())
        fake_resp_id = str(uuid4())

        # Create responder with fake team_id -> 404
        bad_prov = await client.post(
            "/commander/responders",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={
                "email": "badteam@example.com",
                "password": "StrongPass123!",
                "phone_number": "+1555100041",
                "full_name": "Test User",
                "badge_number": "B-BADTEAM",
                "team_id": fake_team_id,
            },
        )
        assert bad_prov.status_code == 404

        # Add member to fake team -> 404
        add_fake_team = await client.post(
            f"/teams/{fake_team_id}/members",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"responder_id": fake_resp_id},
        )
        assert add_fake_team.status_code == 404

        # Create real team
        real_team = (
            await client.post(
                "/teams",
                headers={"Authorization": f"Bearer {cmd_token}"},
                json={"name": "Delta Search"},
            )
        ).json()
        real_team_id = real_team["team_id"]

        # Add fake responder to real team -> 404
        add_fake_resp = await client.post(
            f"/teams/{real_team_id}/members",
            headers={"Authorization": f"Bearer {cmd_token}"},
            json={"responder_id": fake_resp_id},
        )
        assert add_fake_resp.status_code == 404

        # Delete member with fake team -> 404
        del_fake_team = await client.delete(
            f"/teams/{fake_team_id}/members/{fake_resp_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert del_fake_team.status_code == 404

        # Delete fake responder from real team -> 404
        del_fake_resp = await client.delete(
            f"/teams/{real_team_id}/members/{fake_resp_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert del_fake_resp.status_code == 404

        # Delete fake team -> 404
        del_fake = await client.delete(
            f"/teams/{fake_team_id}",
            headers={"Authorization": f"Bearer {cmd_token}"},
        )
        assert del_fake.status_code == 404
