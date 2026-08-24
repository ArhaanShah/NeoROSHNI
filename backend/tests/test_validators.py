from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.schemas.validators import (
    sanitize_string,
    validate_badge_number,
    validate_latitude,
    validate_longitude,
)


def test_phone_validator_rejects_bad_phone_numbers() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="bad-phone@example.com",
            password="StrongPass123!",
            phone_number="555-1234",
            full_name="Bad Phone",
        )


def test_latitude_validator_rejects_bad_values_independently() -> None:
    with pytest.raises(ValueError, match="Latitude"):
        validate_latitude(90.1)
    with pytest.raises(ValueError, match="Latitude"):
        validate_latitude("nan")

    assert validate_latitude(-90) == -90
    assert validate_latitude(90) == 90


def test_longitude_validator_rejects_bad_values_independently() -> None:
    with pytest.raises(ValueError, match="Longitude"):
        validate_longitude(-180.1)
    with pytest.raises(ValueError, match="Longitude"):
        validate_longitude("inf")

    assert validate_longitude(-180) == -180
    assert validate_longitude(180) == 180


def test_badge_number_validator() -> None:
    # Valid formats
    assert validate_badge_number("B-101") == "B-101"
    assert validate_badge_number("BADGE_99") == "BADGE_99"
    assert validate_badge_number("  RESP-01  ") == "RESP-01"

    # Invalid formats
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("A")  # too short
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("BADGE#123")  # special character
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("BADGE 123")  # space in between
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("X" * 51)  # too long


def test_sanitize_string_validator() -> None:
    assert sanitize_string("  Alpha Team  ") == "Alpha Team"
    with pytest.raises(ValueError, match="non-whitespace"):
        sanitize_string("   ")
    with pytest.raises(ValueError, match="exceed"):
        sanitize_string("A" * 256, max_length=255)

