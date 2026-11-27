"""Application business logic."""

from typing import Any

from app.errors import AppError
from app.models.application import ApplicationModel
from app.models.opportunity import OpportunityModel
from app.models.profile import StudentProfileModel
from app.services.eligibility_service import evaluate_eligibility
from app.utils.datetime_utils import utc_now_iso
from app.utils.response import paginated_payload


def apply_to_opportunity(
    user_id: int, opportunity_id: int, *, note: str | None = None
) -> dict[str, Any]:
    """Submit a student application to an active, open, eligible opportunity."""
    opp_row = OpportunityModel.find_by_id(opportunity_id)
    if opp_row is None:
        raise AppError(
            code="OPPORTUNITY_NOT_FOUND",
            message="Opportunity not found.",
            status_code=404,
        )

    opp = OpportunityModel.serialize(opp_row)
    if not opp["is_active"]:
        raise AppError(
            code="OPPORTUNITY_INACTIVE",
            message="This opportunity is no longer accepting applications.",
            status_code=422,
        )

    if opp["deadline"] < utc_now_iso():
        raise AppError(
            code="DEADLINE_PASSED",
            message="The application deadline for this opportunity has passed.",
            status_code=422,
        )

    profile_row = StudentProfileModel.find_by_user_id(user_id)
    if profile_row is None:
        raise AppError(
            code="PROFILE_NOT_FOUND",
            message="Student profile not found.",
            status_code=404,
        )

    eligibility = evaluate_eligibility(
        StudentProfileModel.serialize(profile_row), opp
    )
    if not eligibility["eligible"]:
        raise AppError(
            code="NOT_ELIGIBLE",
            message="You do not meet the eligibility criteria for this opportunity.",
            status_code=422,
            details={
                "reasons": eligibility["reasons"],
                "missing_fields": eligibility["missing_fields"],
            },
        )

    existing = ApplicationModel.find_by_user_and_opportunity(user_id, opportunity_id)
    if existing is not None and existing["status"] != "withdrawn":
        raise AppError(
            code="ALREADY_APPLIED",
            message="You have already applied to this opportunity.",
            status_code=409,
        )

    app_row = ApplicationModel.create_or_reapply(user_id, opportunity_id, note=note)
    return {"application": ApplicationModel.serialize(app_row)}


def list_student_applications(
    user_id: int,
    page: int,
    per_page: int,
    *,
    status: str | None = None,
) -> dict[str, Any]:
    """List paginated applications submitted by the authenticated student."""
    rows, total = ApplicationModel.list_for_student(
        user_id, page, per_page, status=status
    )
    items = [ApplicationModel.serialize(row) for row in rows]
    return paginated_payload(items=items, page=page, per_page=per_page, total=total)


def get_application_for_user(
    application_id: int, user_id: int, role: str
) -> dict[str, Any]:
    """Retrieve a single application (owner student or admin)."""
    row = ApplicationModel.find_by_id(application_id)
    if row is None:
        raise AppError(
            code="APPLICATION_NOT_FOUND",
            message="Application not found.",
            status_code=404,
        )

    if role != "admin" and int(row["user_id"]) != user_id:
        raise AppError(
            code="FORBIDDEN",
            message="You do not have permission to view this application.",
            status_code=403,
        )

    return {
        "application": ApplicationModel.serialize(
            row, include_applicant=(role == "admin")
        )
    }


def withdraw_student_application(application_id: int, user_id: int) -> dict[str, Any]:
    """Allow a student to withdraw their own pending/shortlisted application."""
    row = ApplicationModel.find_by_id(application_id)
    if row is None:
        raise AppError(
            code="APPLICATION_NOT_FOUND",
            message="Application not found.",
            status_code=404,
        )

    if int(row["user_id"]) != user_id:
        raise AppError(
            code="FORBIDDEN",
            message="You do not have permission to modify this application.",
            status_code=403,
        )

    if row["status"] == "withdrawn":
        raise AppError(
            code="ALREADY_WITHDRAWN",
            message="Application has already been withdrawn.",
            status_code=409,
        )

    if row["status"] in ("accepted", "rejected"):
        raise AppError(
            code="CANNOT_WITHDRAW",
            message=f"Cannot withdraw an application that has already been {row['status']}.",
            status_code=422,
        )

    updated = ApplicationModel.update_status(application_id, "withdrawn")
    assert updated is not None
    return {"application": ApplicationModel.serialize(updated)}


def list_opportunity_applications(
    opportunity_id: int,
    page: int,
    per_page: int,
    *,
    status: str | None = None,
) -> dict[str, Any]:
    """List paginated applications for an opportunity (admin only)."""
    if OpportunityModel.find_by_id(opportunity_id) is None:
        raise AppError(
            code="OPPORTUNITY_NOT_FOUND",
            message="Opportunity not found.",
            status_code=404,
        )

    rows, total = ApplicationModel.list_for_opportunity(
        opportunity_id, page, per_page, status=status
    )
    items = [ApplicationModel.serialize(row, include_applicant=True) for row in rows]
    return paginated_payload(items=items, page=page, per_page=per_page, total=total)


def update_application_status(
    application_id: int,
    status: str,
    *,
    admin_remarks: str | None = None,
    update_remarks: bool = False,
) -> dict[str, Any]:
    """Update an application's review status (admin only)."""
    row = ApplicationModel.find_by_id(application_id)
    if row is None:
        raise AppError(
            code="APPLICATION_NOT_FOUND",
            message="Application not found.",
            status_code=404,
        )

    if row["status"] == "withdrawn":
        raise AppError(
            code="APPLICATION_WITHDRAWN",
            message="Cannot update the status of a withdrawn application.",
            status_code=422,
        )

    updated = ApplicationModel.update_status(
        application_id,
        status,
        admin_remarks=admin_remarks,
        update_remarks=update_remarks,
    )
    assert updated is not None
    return {"application": ApplicationModel.serialize(updated, include_applicant=True)}
