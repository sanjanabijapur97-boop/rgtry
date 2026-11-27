"""Opportunity business logic."""

from typing import Any

from app.errors import AppError
from app.models.opportunity import OpportunityModel
from app.models.profile import StudentProfileModel
from app.services.eligibility_service import evaluate_eligibility
from app.utils.response import paginated_payload


def list_opportunities(
    page: int,
    per_page: int,
    *,
    q: str | None = None,
    category: str | None = None,
    is_active: bool | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> dict[str, Any]:
    """List opportunities with search, category/active filter, sorting, and pagination."""
    rows, total = OpportunityModel.list_paginated(
        page=page,
        per_page=per_page,
        q=q,
        category=category,
        is_active=is_active,
        sort=sort,
        order=order,
    )
    items = [OpportunityModel.serialize(row) for row in rows]
    return paginated_payload(items=items, page=page, per_page=per_page, total=total)


def list_eligible_opportunities_for_student(
    user_id: int,
    page: int,
    per_page: int,
    *,
    q: str | None = None,
    category: str | None = None,
    is_active: bool | None = True,
    eligible_only: bool = True,
    sort: str = "created_at",
    order: str = "desc",
) -> dict[str, Any]:
    """List opportunities evaluated against the authenticated student's profile."""
    profile_row = StudentProfileModel.find_by_user_id(user_id)
    if profile_row is None:
        raise AppError(
            code="PROFILE_NOT_FOUND",
            message="Student profile not found.",
            status_code=404,
        )
    profile = StudentProfileModel.serialize(profile_row)

    rows = OpportunityModel.list_matching(
        q=q,
        category=category,
        is_active=is_active,
        sort=sort,
        order=order,
    )
    matched: list[dict[str, Any]] = []
    for row in rows:
        serialized = OpportunityModel.serialize(row)
        eligibility = evaluate_eligibility(profile, serialized)
        if eligible_only and not eligibility["eligible"]:
            continue
        serialized["eligibility"] = {
            "eligible": eligibility["eligible"],
            "reasons": eligibility["reasons"],
            "missing_fields": eligibility["missing_fields"],
        }
        matched.append(serialized)

    total = len(matched)
    start = (page - 1) * per_page
    page_items = matched[start : start + per_page]
    return paginated_payload(items=page_items, page=page, per_page=per_page, total=total)


def get_opportunity(opportunity_id: int) -> dict[str, Any]:
    """Retrieve a single opportunity by ID."""
    row = OpportunityModel.find_by_id(opportunity_id)
    if row is None:
        raise AppError(
            code="OPPORTUNITY_NOT_FOUND",
            message="Opportunity not found.",
            status_code=404,
        )
    return {"opportunity": OpportunityModel.serialize(row)}


def create_opportunity(data: dict[str, Any], admin_user_id: int) -> dict[str, Any]:
    """Create a new opportunity."""
    row = OpportunityModel.create(data, created_by=admin_user_id)
    return {"opportunity": OpportunityModel.serialize(row)}


def update_opportunity(opportunity_id: int, updates: dict[str, Any]) -> dict[str, Any]:
    """Update an existing opportunity."""
    existing = OpportunityModel.find_by_id(opportunity_id)
    if existing is None:
        raise AppError(
            code="OPPORTUNITY_NOT_FOUND",
            message="Opportunity not found.",
            status_code=404,
        )
    updated = OpportunityModel.update(opportunity_id, updates)
    assert updated is not None
    return {"opportunity": OpportunityModel.serialize(updated)}


def delete_opportunity(opportunity_id: int) -> dict[str, Any]:
    """Delete an existing opportunity."""
    deleted = OpportunityModel.delete(opportunity_id)
    if not deleted:
        raise AppError(
            code="OPPORTUNITY_NOT_FOUND",
            message="Opportunity not found.",
            status_code=404,
        )
    return {"deleted": True, "id": opportunity_id}
