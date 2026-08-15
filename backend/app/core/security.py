from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status

from app.config import settings

password_hasher = PasswordHasher()


@dataclass
class TokenPayload:
    sub: str
    typ: str
    exp: int
    iat: int
    role: str | None = None


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now_utc() -> datetime:
    return datetime.now(UTC)


def create_access_token(user_id: UUID, role: str) -> str:
    now = _now_utc()
    payload = {
        "sub": str(user_id),
        "role": role,
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID) -> tuple[str, datetime]:
    now = _now_utc()
    expires_at = now + timedelta(days=settings.refresh_token_ttl_days)
    payload = {
        "sub": str(user_id),
        "typ": "refresh",
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_token(token: str, expected_type: str) -> TokenPayload:
    try:
        decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    token_type = decoded.get("typ")
    if token_type != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    subject = decoded.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    return TokenPayload(
        sub=subject,
        typ=token_type,
        exp=int(decoded.get("exp", 0)),
        iat=int(decoded.get("iat", 0)),
        role=decoded.get("role"),
    )
