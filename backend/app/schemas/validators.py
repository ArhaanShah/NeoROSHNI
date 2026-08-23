from __future__ import annotations

import math
import re
from typing import Any

PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")


def validate_phone_number(value: str) -> str:
    if not PHONE_RE.fullmatch(value):
        raise ValueError("Phone number must be in E.164 format, for example +15551234567")
    return value


def validate_optional_phone_number(value: str | None) -> str | None:
    if value is None:
        return value
    return validate_phone_number(value)


def validate_latitude(value: Any) -> float:
    latitude = float(value)
    if not math.isfinite(latitude) or latitude < -90 or latitude > 90:
        raise ValueError("Latitude must be between -90 and 90")
    return latitude


def validate_longitude(value: Any) -> float:
    longitude = float(value)
    if not math.isfinite(longitude) or longitude < -180 or longitude > 180:
        raise ValueError("Longitude must be between -180 and 180")
    return longitude
