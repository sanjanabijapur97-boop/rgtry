"""Applications blueprint for student submissions and admin review."""

from flask import Blueprint, Response, g

from app.services.application_service import (
    apply_to_opportunity,
    get_application_for_user,
    list_opportunity_applications,
    list_student_applications,
    update_application_status,
    withdraw_student_application,
)
from app.utils.auth import require_auth, require_role
from app.utils.response import success_response
from app.validators.application import (
    validate_application_list_params,
    validate_application_status_payload,
    validate_apply_payload,
)
from app.validators.common import optional_json_body, require_json_body

applications_bp = Blueprint("applications", __name__, url_prefix="/api")


@applications_bp.post("/opportunities/<int:opportunity_id>/apply")
@require_role("student")
def apply_route(opportunity_id: int) -> tuple[Response, int]:
    """Submit an application for an opportunity (student only)."""
    body = optional_json_body()
    note = validate_apply_payload(body)
    result = apply_to_opportunity(
        user_id=g.current_user["id"],
        opportunity_id=opportunity_id,
        note=note,
    )
    return success_response(result, status_code=201)


@applications_bp.get("/applications")
@require_role("student")
def list_my_applications_route() -> tuple[Response, int]:
    """List the authenticated student's applications."""
    params = validate_application_list_params()
    result = list_student_applications(g.current_user["id"], **params)
    return success_response(result, status_code=200)


@applications_bp.get("/applications/<int:application_id>")
@require_auth
def get_application_route(application_id: int) -> tuple[Response, int]:
    """View a single application (owner student or admin)."""
    result = get_application_for_user(
        application_id=application_id,
        user_id=g.current_user["id"],
        role=g.current_user["role"],
    )
    return success_response(result, status_code=200)


@applications_bp.post("/applications/<int:application_id>/withdraw")
@require_role("student")
def withdraw_application_route(application_id: int) -> tuple[Response, int]:
    """Withdraw the authenticated student's application."""
    result = withdraw_student_application(
        application_id=application_id,
        user_id=g.current_user["id"],
    )
    return success_response(result, status_code=200)


@applications_bp.get("/opportunities/<int:opportunity_id>/applications")
@require_role("admin")
def list_opportunity_applications_route(opportunity_id: int) -> tuple[Response, int]:
    """List applicants for an opportunity (admin only)."""
    params = validate_application_list_params()
    result = list_opportunity_applications(opportunity_id, **params)
    return success_response(result, status_code=200)


@applications_bp.patch("/applications/<int:application_id>/status")
@require_role("admin")
def update_application_status_route(application_id: int) -> tuple[Response, int]:
    """Update an application's review status (admin only)."""
    body = require_json_body()
    status, admin_remarks, update_remarks = validate_application_status_payload(body)
    result = update_application_status(
        application_id=application_id,
        status=status,
        admin_remarks=admin_remarks,
        update_remarks=update_remarks,
    )
    return success_response(result, status_code=200)
