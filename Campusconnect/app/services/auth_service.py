"""Authentication business logic."""

import sqlite3
from typing import Any

from app.errors import AppError
from app.models.user import UserModel
from app.utils.auth import create_access_token


def register_student(name: str, email: str, password: str) -> dict[str, Any]:
    """Register a new student account (public registration is always student role)."""
    if UserModel.find_by_email(email) is not None:
        raise AppError(
            code="EMAIL_ALREADY_EXISTS",
            message="An account with this email already exists.",
            status_code=409,
        )

    try:
        user_row = UserModel.create_student(name=name, email=email, password=password)
    except sqlite3.IntegrityError as exc:
        raise AppError(
            code="EMAIL_ALREADY_EXISTS",
            message="An account with this email already exists.",
            status_code=409,
        ) from exc

    return {"user": UserModel.serialize(user_row)}


def login_user(email: str, password: str) -> dict[str, Any]:
    """Authenticate credentials and issue a Bearer JWT."""
    user_row = UserModel.find_by_email(email)
    if user_row is None or not UserModel.verify_password(user_row, password):
        raise AppError(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
            status_code=401,
        )

    token, expires_in, expires_at = create_access_token(
        user_id=user_row["id"], role=user_row["role"]
    )
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "expires_at": expires_at,
        "user": UserModel.serialize(user_row),
    }


def get_current_user_data(user_row: sqlite3.Row) -> dict[str, Any]:
    """Return serialized current user payload."""
    return {"user": UserModel.serialize(user_row)}


def change_user_password(
    user_row: sqlite3.Row, current_password: str, new_password: str
) -> dict[str, Any]:
    """Verify current password and update to a new password."""
    if not UserModel.verify_password(user_row, current_password):
        raise AppError(
            code="INVALID_CREDENTIALS",
            message="Current password is incorrect.",
            status_code=401,
        )

    UserModel.update_password(int(user_row["id"]), new_password)
    return {"password_changed": True}


def create_admin_user(email: str, password: str) -> dict[str, Any]:
    """Create an admin account via CLI."""
    if UserModel.find_by_email(email) is not None:
        raise AppError(
            code="EMAIL_ALREADY_EXISTS",
            message="An account with this email already exists.",
            status_code=409,
        )

    try:
        user_row = UserModel.create_admin(email=email, password=password)
    except sqlite3.IntegrityError as exc:
        raise AppError(
            code="EMAIL_ALREADY_EXISTS",
            message="An account with this email already exists.",
            status_code=409,
        ) from exc

    return UserModel.serialize(user_row)
