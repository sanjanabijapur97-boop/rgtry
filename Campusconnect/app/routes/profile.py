"""Student profile blueprint."""

from flask import Blueprint, Response, g

from app.services.profile_service import get_student_profile, update_student_profile
from app.utils.auth import require_role
from app.utils.response import success_response
from app.validators.common import require_json_body
from app.validators.profile import validate_profile_update

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


@profile_bp.get("")
@require_role("student")
def get_own_profile() -> tuple[Response, int]:
    """View the authenticated student's own profile."""
    result = get_student_profile(g.current_user["id"])
    return success_response(result, status_code=200)


@profile_bp.put("")
@require_role("student")
def replace_own_profile() -> tuple[Response, int]:
    """Full update of the authenticated student's profile."""
    body = require_json_body()
    updates = validate_profile_update(body, partial=False)
    result = update_student_profile(g.current_user["id"], updates)
    return success_response(result, status_code=200)


@profile_bp.patch("")
@require_role("student")
def patch_own_profile() -> tuple[Response, int]:
    """Partial update of the authenticated student's profile."""
    body = require_json_body()
    updates = validate_profile_update(body, partial=True)
    result = update_student_profile(g.current_user["id"], updates)
    return success_response(result, status_code=200)
