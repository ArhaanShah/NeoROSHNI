from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.api.deps import RoleChecker
from app.config import settings
from app.main import app
from app.routers import auth, users


async def _register(client: AsyncClient, email: str, phone_number: str) -> dict:
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "phone_number": phone_number,
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_register_login_and_me_flow() -> None:
    email = f"c2-user-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone = f"+1555{datetime.now(UTC).strftime('%f')}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        register_payload = await _register(client, email, phone)

        me_response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {register_payload['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email

        login_response = await client.post(
            "/auth/login",
            json={"email": email, "password": "StrongPass123!"},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()


@pytest.mark.asyncio
async def test_invalid_credentials_fail_cleanly() -> None:
    email = f"c2-bad-login-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone = f"+1666{datetime.now(UTC).strftime('%f')}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        await _register(client, email, phone)

        bad_login = await client.post(
            "/auth/login",
            json={"email": email, "password": "WrongPass123!"},
        )
        assert bad_login.status_code == 401


@pytest.mark.asyncio
async def test_expired_access_token_rejected() -> None:
    email = f"c2-expired-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone = f"+1777{datetime.now(UTC).strftime('%f')}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        register_payload = await _register(client, email, phone)
        valid_me = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {register_payload['access_token']}"},
        )
        assert valid_me.status_code == 200

        user_id = valid_me.json()["user_id"]
        expired_token = jwt.encode(
            {
                "sub": user_id,
                "role": "civilian",
                "typ": "access",
                "iat": int((datetime.now(UTC) - timedelta(minutes=30)).timestamp()),
                "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp()),
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        expired_me = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert expired_me.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotation_and_reuse_rejection() -> None:
    email = f"c2-refresh-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone = f"+1888{datetime.now(UTC).strftime('%f')}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = await _register(client, email, phone)

        refreshed = await client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refreshed.status_code == 200
        rotated = refreshed.json()
        assert rotated["refresh_token"] != tokens["refresh_token"]

        reused = await client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert reused.status_code == 401


@pytest.mark.asyncio
async def test_logout_revocation_blocks_refresh() -> None:
    email = f"c2-logout-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone = f"+1999{datetime.now(UTC).strftime('%f')}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = await _register(client, email, phone)

        logout_response = await client.post(
            "/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert logout_response.status_code == 200

        refresh_after_logout = await client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_after_logout.status_code == 401


@pytest.mark.asyncio
async def test_commander_only_endpoint_returns_403_for_civilian() -> None:
    """Civilian token must be denied a commander-only endpoint with 403."""
    email = f"c4-cmd-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone = f"+1301{datetime.now(UTC).strftime('%f')}"

    test_app = FastAPI()
    test_app.include_router(auth.router)
    test_app.include_router(users.router)

    @test_app.get("/commander-only")
    async def commander_only(_user=Depends(RoleChecker(["commander"]))) -> dict[str, str]:
        return {"status": "ok"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = await _register(client, email, phone)

        response = await client.get(
            "/commander-only",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_multi_role_endpoint_returns_403_for_civilian() -> None:
    """Civilian token is denied an endpoint requiring [responder, commander]."""
    email = f"c4-multi-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone = f"+1302{datetime.now(UTC).strftime('%f')}"

    test_app = FastAPI()
    test_app.include_router(auth.router)
    test_app.include_router(users.router)

    @test_app.get("/staff-only")
    async def staff_only(_user=Depends(RoleChecker(["responder", "commander"]))) -> dict[str, str]:
        return {"status": "ok"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = await _register(client, email, phone)

        response = await client.get(
            "/staff-only",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_role_checker_allows_correct_role() -> None:
    """Civilian token is allowed through a civilian-gated endpoint — 200."""
    email = f"c4-allow-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone = f"+1303{datetime.now(UTC).strftime('%f')}"

    test_app = FastAPI()
    test_app.include_router(auth.router)
    test_app.include_router(users.router)

    @test_app.get("/civilian-only")
    async def civilian_only(_user=Depends(RoleChecker(["civilian"]))) -> dict[str, str]:
        return {"status": "ok"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = await _register(client, email, phone)

        response = await client.get(
            "/civilian-only",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_responder_gets_403_on_commander_endpoint() -> None:
    """A responder-role token is denied a commander-only endpoint with 403."""
    from app.core.security import create_access_token, hash_password
    from app.database import db_session_factory
    from app.models.auth import User, UserMedicalProfile, UserProfile

    # Insert a responder user directly (bypassing the civilian-only register endpoint)
    async with db_session_factory() as db:
        responder = User(
            email=f"c4-resp-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com",
            hashed_password=hash_password("Test1234!"),
            phone_number=f"+1304{datetime.now(UTC).strftime('%f')}",
            role="responder",
            is_active=True,
        )
        db.add(responder)
        await db.flush()
        responder_id = responder.user_id
        db.add(UserProfile(user_id=responder_id, full_name="Test Responder"))
        db.add(
            UserMedicalProfile(
                user_id=responder_id,
                public_user_code=f"R-{responder_id}",
                consent_flags={},
            )
        )
        await db.commit()

    responder_token = create_access_token(responder_id, "responder")

    test_app = FastAPI()
    test_app.include_router(auth.router)
    test_app.include_router(users.router)

    @test_app.get("/commander-only-2")
    async def commander_only_2(_user=Depends(RoleChecker(["commander"]))) -> dict[str, str]:
        return {"status": "ok"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/commander-only-2",
            headers={"Authorization": f"Bearer {responder_token}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_role_checker_returns_403_for_wrong_role() -> None:
    email = f"c2-role-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}@example.com"
    phone = f"+1222{datetime.now(UTC).strftime('%f')}"

    test_app = FastAPI()
    test_app.include_router(auth.router)
    test_app.include_router(users.router)

    @test_app.get("/role-protected")
    async def role_protected(_user=Depends(RoleChecker(["responder"]))) -> dict[str, str]:
        return {"status": "ok"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = await _register(client, email, phone)

        response = await client.get(
            "/role-protected",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 403
