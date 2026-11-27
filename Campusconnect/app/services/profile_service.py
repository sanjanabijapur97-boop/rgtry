"""Student profile business logic."""

from typing import Any

from app.errors import AppError
from app.models.profile import StudentProfileModel


def get_student_profile(user_id: int) -> dict[str, Any]:
    """Fetch and serialize the authenticated student's profile."""
    profile_row = StudentProfileModel.find_by_user_id(user_id)
    if profile_row is None:
        raise AppError(
            code="PROFILE_NOT_FOUND",
            message="Student profile not found.",
            status_code=404,
        )
    return {"profile": StudentProfileModel.serialize(profile_row)}


def update_student_profile(user_id: int, updates: dict[str, Any]) -> dict[str, Any]:
    """Update and return the authenticated student's profile."""
    existing = StudentProfileModel.find_by_user_id(user_id)
    if existing is None:
        raise AppError(
            code="PROFILE_NOT_FOUND",
            message="Student profile not found.",
            status_code=404,
        )

    updated_row = StudentProfileModel.update(user_id, updates)
    assert updated_row is not None
    return {"profile": StudentProfileModel.serialize(updated_row)}
