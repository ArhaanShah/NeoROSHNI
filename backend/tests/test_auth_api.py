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
from app.core.security import create_access_token
from app.database import db_session_factory
from app.main import app
from app.models.auth import User


async def _register(client: AsyncClient, email: str, phone: str) -> dict:
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "phone_number": phone,
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_register_login_and_me_flow() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = await _register(client, "user1@example.com", "+1555000101")

        me = await client.get("/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert me.status_code == 200
        assert me.json()["email"] == "user1@example.com"

        login = await client.post("/auth/login", json={"email": "user1@example.com", "password": "StrongPass123!"})
        assert login.status_code == 200
        assert "access_token" in login.json()


@pytest.mark.asyncio
async def test_invalid_credentials_fail_cleanly() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        await _register(client, "user2@example.com", "+1555000102")
        bad_login = await client.post("/auth/login", json={"email": "user2@example.com", "password": "WrongPassword"})
        assert bad_login.status_code == 401


@pytest.mark.asyncio
async def test_expired_access_token_rejected() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = await _register(client, "user3@example.com", "+1555000103")
        me = await client.get("/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        user_id = me.json()["user_id"]

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
        expired_res = await client.get("/users/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert expired_res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_revocation() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = await _register(client, "user4@example.com", "+1555000104")

        # Refresh rotates token
        refreshed = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert refreshed.status_code == 200
        new_token = refreshed.json()["refresh_token"]
        assert new_token != tokens["refresh_token"]

        # Reusing old token is rejected
        reused = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert reused.status_code == 401

        # Logout revokes active token
        logout = await client.post("/auth/logout", json={"refresh_token": new_token})
        assert logout.status_code == 200
        after_logout = await client.post("/auth/refresh", json={"refresh_token": new_token})
        assert after_logout.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("allowed_roles", "user_role", "expected_status", "idx"),
    [
        (["civilian"], "civilian", 200, 1),
        (["commander"], "civilian", 403, 2),
        (["responder", "commander"], "civilian", 403, 3),
        (["commander"], "responder", 403, 4),
    ],
)
async def test_role_checker_enforcement(allowed_roles: list[str], user_role: str, expected_status: int, idx: int) -> None:
    test_app = FastAPI()

    @test_app.get("/role-check")
    async def role_check(_user=Depends(RoleChecker(allowed_roles))) -> dict[str, str]:
        return {"status": "ok"}

    async with db_session_factory() as session:
        user = User(
            email=f"rc-user{idx}@example.com",
            hashed_password="h",
            phone_number=f"+15559990{idx}",
            role=user_role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        token = create_access_token(user_id=user.user_id, role=user_role)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.get("/role-check", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == expected_status
