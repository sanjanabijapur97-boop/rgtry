"""Student profile input validators."""

import re
from typing import Any

from app.errors import AppError

PHONE_REGEX = re.compile(r"^[+]?[0-9\s\-()]{7,20}$")


def _validate_name(val: Any) -> tuple[str | None, str | None]:
    if not isinstance(val, str):
        return None, "Name must be a string between 2 and 120 characters."
    cleaned = val.strip()
    if len(cleaned) < 2 or len(cleaned) > 120:
        return None, "Name must be between 2 and 120 characters."
    return cleaned, None


def _validate_branch(val: Any) -> tuple[str | None, str | None]:
    if val is None:
        return None, None
    if not isinstance(val, str):
        return None, "Branch must be a string or null."
    cleaned = val.strip()
    if not cleaned or len(cleaned) > 50:
        return None, "Branch must be between 1 and 50 characters."
    return cleaned, None


def _validate_year(val: Any) -> tuple[int | None, str | None]:
    if val is None:
        return None, None
    if isinstance(val, bool) or not isinstance(val, int):
        return None, "Year must be an integer between 1 and 5."
    if val < 1 or val > 5:
        return None, "Year must be between 1 and 5."
    return val, None


def _validate_cgpa(val: Any) -> tuple[float | None, str | None]:
    if val is None:
        return None, None
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return None, "CGPA must be a number between 0.0 and 10.0."
    numeric = float(val)
    if numeric < 0.0 or numeric > 10.0:
        return None, "CGPA must be between 0.0 and 10.0."
    return round(numeric, 2), None


def _validate_skills(val: Any) -> tuple[list[str] | None, str | None]:
    if not isinstance(val, list):
        return None, "Skills must be an array of strings."
    if len(val) > 50:
        return None, "Skills cannot contain more than 50 items."

    cleaned_skills: list[str] = []
    seen_lower: set[str] = set()
    for item in val:
        if not isinstance(item, str):
            return None, "Each skill must be a non-empty string."
        cleaned = item.strip()
        if not cleaned or len(cleaned) > 50:
            return None, "Each skill must be between 1 and 50 characters."
        lowered = cleaned.lower()
        if lowered not in seen_lower:
            seen_lower.add(lowered)
            cleaned_skills.append(cleaned)
    return cleaned_skills, None


def _validate_phone(val: Any) -> tuple[str | None, str | None]:
    if val is None:
        return None, None
    if not isinstance(val, str):
        return None, "Phone must be a string or null."
    cleaned = val.strip()
    digits = re.sub(r"\D", "", cleaned)
    if not PHONE_REGEX.match(cleaned) or len(digits) < 7 or len(digits) > 15:
        return None, "Phone must be a valid phone number (7 to 15 digits)."
    return cleaned, None


def validate_profile_update(data: dict[str, Any], *, partial: bool) -> dict[str, Any]:
    """Validate PUT (full) or PATCH (partial) student profile update payload."""
    field_errors: dict[str, str] = {}
    updates: dict[str, Any] = {}

    if not partial:
        if "name" not in data:
            field_errors["name"] = "Name is required for full profile update."
        else:
            parsed_name, err = _validate_name(data["name"])
            if err:
                field_errors["name"] = err
            else:
                updates["name"] = parsed_name

        for key, validator, default in (
            ("branch", _validate_branch, None),
            ("year", _validate_year, None),
            ("cgpa", _validate_cgpa, None),
            ("skills", _validate_skills, []),
            ("phone", _validate_phone, None),
        ):
            raw = data.get(key, default)
            parsed, err = validator(raw)
            if err:
                field_errors[key] = err
            else:
                updates[key] = parsed
    else:
        validators = {
            "name": _validate_name,
            "branch": _validate_branch,
            "year": _validate_year,
            "cgpa": _validate_cgpa,
            "skills": _validate_skills,
            "phone": _validate_phone,
        }
        for key, validator in validators.items():
            if key in data:
                parsed, err = validator(data[key])
                if err:
                    field_errors[key] = err
                else:
                    updates[key] = parsed

        if not field_errors and not updates:
            raise AppError(
                code="VALIDATION_ERROR",
                message="At least one profile field must be provided to update.",
                status_code=422,
                details={"fields": {}},
            )

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid profile data.",
            status_code=422,
            details={"fields": field_errors},
        )

    return updates
