from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.team import (
    ResponderCreate,
    TeamCreate,
    TeamMemberAddRequest,
    TeamUpdate,
)


def test_team_create_schema() -> None:
    # Valid
    t = TeamCreate(name="  Bravo Team  ")
    assert t.name == "Bravo Team"

    # Whitespace only -> error
    with pytest.raises(ValidationError):
        TeamCreate(name="    ")

    # Empty string -> error
    with pytest.raises(ValidationError):
        TeamCreate(name="")

    # Max length boundary
    t_max = TeamCreate(name="A" * 255)
    assert t_max.name == "A" * 255

    # Exceeding max length
    with pytest.raises(ValidationError):
        TeamCreate(name="A" * 256)


def test_team_update_schema() -> None:
    # Valid with name
    u1 = TeamUpdate(name="  Updated Name  ")
    assert u1.name == "Updated Name"

    # Valid with None
    u2 = TeamUpdate(name=None)
    assert u2.name is None

    # Empty model default
    u3 = TeamUpdate()
    assert u3.name is None

    # Invalid empty whitespace string
    with pytest.raises(ValidationError):
        TeamUpdate(name="   ")

    # Exceeding max length
    with pytest.raises(ValidationError):
        TeamUpdate(name="A" * 256)


def test_responder_create_schema() -> None:
    valid_team_id = uuid4()
    # Valid payload
    r = ResponderCreate(
        email="responder@example.com",
        password="StrongPass123!",
        phone_number="+15551234567",
        full_name="  Jane Doe  ",
        badge_number="  B-101  ",
        specialization="  EMT Specialist  ",
        team_id=valid_team_id,
    )
    assert r.email == "responder@example.com"
    assert r.full_name == "Jane Doe"
    assert r.badge_number == "B-101"
    assert r.specialization == "EMT Specialist"
    assert r.team_id == valid_team_id

    # Specialization whitespace becomes None
    r_empty_spec = ResponderCreate(
        email="responder2@example.com",
        password="StrongPass123!",
        phone_number="+15551234567",
        full_name="Jane Doe",
        badge_number="B-102",
        specialization="   ",
    )
    assert r_empty_spec.specialization is None

    # Invalid email
    with pytest.raises(ValidationError):
        ResponderCreate(
            email="invalid-email",
            password="StrongPass123!",
            phone_number="+15551234567",
            full_name="Jane",
            badge_number="B-103",
        )

    # Short password
    with pytest.raises(ValidationError):
        ResponderCreate(
            email="responder@example.com",
            password="short",
            phone_number="+15551234567",
            full_name="Jane",
            badge_number="B-103",
        )

    # Invalid phone
    with pytest.raises(ValidationError):
        ResponderCreate(
            email="responder@example.com",
            password="StrongPass123!",
            phone_number="bad-phone",
            full_name="Jane",
            badge_number="B-103",
        )

    # Invalid badge
    with pytest.raises(ValidationError):
        ResponderCreate(
            email="responder@example.com",
            password="StrongPass123!",
            phone_number="+15551234567",
            full_name="Jane",
            badge_number="BAD BADGE",
        )


def test_team_member_add_request_schema() -> None:
    req_id = uuid4()
    req = TeamMemberAddRequest(responder_id=req_id)
    assert req.responder_id == req_id

    # Invalid UUID string
    with pytest.raises(ValidationError):
        TeamMemberAddRequest(responder_id="not-a-uuid")  # type: ignore[arg-type]
