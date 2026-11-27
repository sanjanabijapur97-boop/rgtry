"""Authentication input validators."""

import re
from typing import Any

from app.errors import AppError

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def normalize_email(raw_email: Any) -> str | None:
    if not isinstance(raw_email, str):
        return None
    cleaned = raw_email.strip().lower()
    if not cleaned or len(cleaned) > 254 or not EMAIL_REGEX.match(cleaned):
        return None
    return cleaned


def validate_register_payload(data: dict[str, Any]) -> tuple[str, str, str]:
    """Validate student registration fields and return (name, email, password)."""
    field_errors: dict[str, str] = {}

    raw_name = data.get("name")
    name = raw_name.strip() if isinstance(raw_name, str) else ""
    if not isinstance(raw_name, str) or len(name) < 2 or len(name) > 120:
        field_errors["name"] = "Name must be a string between 2 and 120 characters."

    email = normalize_email(data.get("email"))
    if email is None:
        field_errors["email"] = "A valid email address is required."

    password = data.get("password")
    if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
        field_errors["password"] = "Password must be between 8 and 128 characters."

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid registration data.",
            status_code=422,
            details={"fields": field_errors},
        )

    assert email is not None
    assert isinstance(password, str)
    return name, email, password


def validate_login_payload(data: dict[str, Any]) -> tuple[str, str]:
    """Validate login credentials format and return (email, password)."""
    field_errors: dict[str, str] = {}

    email = normalize_email(data.get("email"))
    if email is None:
        field_errors["email"] = "A valid email address is required."

    password = data.get("password")
    if not isinstance(password, str) or not password:
        field_errors["password"] = "Password is required."

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid login data.",
            status_code=422,
            details={"fields": field_errors},
        )

    assert email is not None
    assert isinstance(password, str)
    return email, password


def validate_admin_cli_input(email_raw: str, password: str) -> tuple[str, str]:
    """Validate admin creation CLI inputs."""
    email = normalize_email(email_raw)
    if email is None:
        raise AppError(
            code="VALIDATION_ERROR",
            message="A valid email address is required.",
            status_code=422,
            details={"fields": {"email": "A valid email address is required."}},
        )
    if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Password must be between 8 and 128 characters.",
            status_code=422,
            details={"fields": {"password": "Password must be between 8 and 128 characters."}},
        )
    return email, password


def validate_change_password_payload(data: dict[str, Any]) -> tuple[str, str]:
    """Validate current_password and new_password for password change."""
    field_errors: dict[str, str] = {}

    current_password = data.get("current_password")
    if not isinstance(current_password, str) or not current_password:
        field_errors["current_password"] = "Current password is required."

    new_password = data.get("new_password")
    if (
        not isinstance(new_password, str)
        or len(new_password) < 8
        or len(new_password) > 128
    ):
        field_errors["new_password"] = (
            "New password must be between 8 and 128 characters."
        )
    elif (
        isinstance(current_password, str)
        and current_password
        and new_password == current_password
    ):
        field_errors["new_password"] = (
            "New password must be different from current password."
        )

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid password change data.",
            status_code=422,
            details={"fields": field_errors},
        )

    assert isinstance(current_password, str)
    assert isinstance(new_password, str)
    return current_password, new_password
