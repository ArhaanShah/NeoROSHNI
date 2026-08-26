from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.database import db_session_factory
from app.main import app
from tests.factories import create_user_with_token


@pytest.mark.asyncio
async def test_user_profile_and_medical_endpoints() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with db_session_factory() as session:
            _, token = await create_user_with_token(session, email="profile_user@example.com")

        headers = {"Authorization": f"Bearer {token}"}

        # 1. Get Me
        me_res = await client.get("/users/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "profile_user@example.com"

        # 2. Get Profile
        prof_res = await client.get("/users/me/profile", headers=headers)
        assert prof_res.status_code == 200
        assert prof_res.json()["full_name"] == "Test User"

        # 3. Update Profile
        update_prof = await client.put(
            "/users/me/profile",
            headers=headers,
            json={
                "full_name": "Updated Name",
                "address": "123 Main St",
                "emergency_contact_name": "Jane Doe",
                "emergency_contact_phone": "+15559876543",
            },
        )
        assert update_prof.status_code == 200
        assert update_prof.json()["full_name"] == "Updated Name"
        assert update_prof.json()["address"] == "123 Main St"

        # 4. Get Medical Profile
        med_res = await client.get("/users/me/medical", headers=headers)
        assert med_res.status_code == 200
        assert "public_user_code" in med_res.json()

        # 5. Update Medical Profile
        update_med = await client.put(
            "/users/me/medical",
            headers=headers,
            json={
                "blood_group": "O+",
                "known_allergies": "Penicillin",
                "chronic_conditions": "Asthma",
                "current_medications": "Albuterol",
                "other_medical_notes": "None",
            },
        )
        assert update_med.status_code == 200
        assert update_med.json()["blood_group"] == "O+"
        assert update_med.json()["known_allergies"] == "Penicillin"
