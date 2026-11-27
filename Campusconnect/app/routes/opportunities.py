"""Opportunities blueprint."""

from flask import Blueprint, Response, g

from app.services.eligibility_service import check_student_eligibility
from app.services.opportunity_service import (
    create_opportunity,
    delete_opportunity,
    get_opportunity,
    list_eligible_opportunities_for_student,
    list_opportunities,
    update_opportunity,
)
from app.utils.auth import require_role
from app.utils.response import success_response
from app.validators.common import require_json_body
from app.validators.opportunity import (
    validate_eligible_opportunities_params,
    validate_opportunity_list_params,
    validate_opportunity_payload,
)

opportunities_bp = Blueprint(
    "opportunities", __name__, url_prefix="/api/opportunities"
)


@opportunities_bp.get("")
def list_opportunities_route() -> tuple[Response, int]:
    """List opportunities with keyword search, category filter, sorting, and pagination."""
    params = validate_opportunity_list_params()
    result = list_opportunities(**params)
    return success_response(result, status_code=200)


@opportunities_bp.get("/eligible")
@require_role("student")
def list_eligible_opportunities_route() -> tuple[Response, int]:
    """List opportunities evaluated against the authenticated student's profile."""
    params = validate_eligible_opportunities_params()
    result = list_eligible_opportunities_for_student(g.current_user["id"], **params)
    return success_response(result, status_code=200)


@opportunities_bp.get("/<int:opportunity_id>")
def get_opportunity_route(opportunity_id: int) -> tuple[Response, int]:
    """Get details for a single opportunity."""
    result = get_opportunity(opportunity_id)
    return success_response(result, status_code=200)


@opportunities_bp.post("")
@require_role("admin")
def create_opportunity_route() -> tuple[Response, int]:
    """Create a new opportunity (admin only)."""
    body = require_json_body()
    validated = validate_opportunity_payload(body, partial=False)
    result = create_opportunity(validated, admin_user_id=g.current_user["id"])
    return success_response(result, status_code=201)


@opportunities_bp.put("/<int:opportunity_id>")
@require_role("admin")
def replace_opportunity_route(opportunity_id: int) -> tuple[Response, int]:
    """Full update of an opportunity (admin only)."""
    body = require_json_body()
    validated = validate_opportunity_payload(body, partial=False)
    result = update_opportunity(opportunity_id, validated)
    return success_response(result, status_code=200)


@opportunities_bp.patch("/<int:opportunity_id>")
@require_role("admin")
def patch_opportunity_route(opportunity_id: int) -> tuple[Response, int]:
    """Partial update of an opportunity (admin only)."""
    body = require_json_body()
    validated = validate_opportunity_payload(body, partial=True)
    result = update_opportunity(opportunity_id, validated)
    return success_response(result, status_code=200)


@opportunities_bp.delete("/<int:opportunity_id>")
@require_role("admin")
def delete_opportunity_route(opportunity_id: int) -> tuple[Response, int]:
    """Delete an opportunity (admin only)."""
    result = delete_opportunity(opportunity_id)
    return success_response(result, status_code=200)


@opportunities_bp.get("/<int:opportunity_id>/eligibility")
@require_role("student")
def check_eligibility_route(opportunity_id: int) -> tuple[Response, int]:
    """Check whether the authenticated student is eligible for an opportunity."""
    result = check_student_eligibility(
        user_id=g.current_user["id"], opportunity_id=opportunity_id
    )
    return success_response(result, status_code=200)
