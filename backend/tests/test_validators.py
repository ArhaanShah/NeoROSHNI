from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.schemas.validators import validate_latitude, validate_longitude


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
