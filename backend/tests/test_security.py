from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException

from app.config import settings
from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_hashing_verifies_password_and_rejects_bad_password() -> None:
    password_hash = hash_password("StrongPass123!")

    assert password_hash != "StrongPass123!"
    assert verify_password("StrongPass123!", password_hash)
    assert not verify_password("WrongPass123!", password_hash)


def test_jwt_creation_and_verification_round_trip() -> None:
    user_id = uuid4()
    token = create_access_token(user_id, "civilian")

    payload = decode_token(token, expected_type="access")

    assert payload.sub == str(user_id)
    assert payload.typ == "access"
    assert payload.role == "civilian"


def test_jwt_expiry_handling() -> None:
    expired_token = jwt.encode(
        {
            "sub": str(uuid4()),
            "role": "civilian",
            "typ": "access",
            "iat": int((datetime.now(UTC) - timedelta(minutes=30)).timestamp()),
            "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp()),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_token(expired_token, expected_type="access")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token expired"
