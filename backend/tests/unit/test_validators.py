from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.schemas.validators import (
    sanitize_string,
    validate_badge_number,
    validate_latitude,
    validate_longitude,
    validate_phone_number,
)


def test_phone_validator_valid_and_invalid() -> None:
    # Valid E.164 formats
    assert validate_phone_number("+15551234567") == "+15551234567"
    assert validate_phone_number("  +919876543210  ") == "+919876543210"

    # Invalid formats
    with pytest.raises(ValueError, match="Phone number"):
        validate_phone_number("555-1234")
    with pytest.raises(ValueError, match="Phone number"):
        validate_phone_number("123")
    with pytest.raises(ValueError, match="Phone number"):
        validate_phone_number("invalid_phone")
    with pytest.raises(ValueError, match="Phone number"):
        validate_phone_number("+0123456789")  # Leading zero after plus

    # Via RegisterRequest schema
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
        validate_latitude(-90.1)
    with pytest.raises(ValueError, match="Latitude"):
        validate_latitude("nan")
    with pytest.raises(ValueError, match="Latitude"):
        validate_latitude("inf")

    assert validate_latitude(-90) == -90
    assert validate_latitude(0) == 0
    assert validate_latitude(90) == 90
    assert validate_latitude("45.5") == 45.5


def test_longitude_validator_rejects_bad_values_independently() -> None:
    with pytest.raises(ValueError, match="Longitude"):
        validate_longitude(-180.1)
    with pytest.raises(ValueError, match="Longitude"):
        validate_longitude(180.1)
    with pytest.raises(ValueError, match="Longitude"):
        validate_longitude("nan")
    with pytest.raises(ValueError, match="Longitude"):
        validate_longitude("inf")

    assert validate_longitude(-180) == -180
    assert validate_longitude(0) == 0
    assert validate_longitude(180) == 180
    assert validate_longitude("-122.4194") == -122.4194


def test_badge_number_validator() -> None:
    # Valid formats
    assert validate_badge_number("B-101") == "B-101"
    assert validate_badge_number("BADGE_99") == "BADGE_99"
    assert validate_badge_number("  RESP-01  ") == "RESP-01"
    assert validate_badge_number("AB") == "AB"
    assert validate_badge_number("R" * 50) == "R" * 50

    # Invalid formats
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("A")  # too short (< 2)
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("BADGE#123")  # special character
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("BADGE 123")  # space in between
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("BADGE.123")  # dot
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("X" * 51)  # too long (> 50)
    with pytest.raises(ValueError, match="Badge number"):
        validate_badge_number("   ")  # empty whitespace


def test_sanitize_string_validator() -> None:
    assert sanitize_string("  Alpha Team  ") == "Alpha Team"
    assert sanitize_string("Clean String", min_length=1, max_length=50) == "Clean String"

    with pytest.raises(ValueError, match="non-whitespace"):
        sanitize_string("   ")
    with pytest.raises(ValueError, match="least"):
        sanitize_string("ab", min_length=3)
    with pytest.raises(ValueError, match="exceed"):
        sanitize_string("A" * 256, max_length=255)
