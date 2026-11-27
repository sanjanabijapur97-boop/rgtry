"""Application input validators."""

from typing import Any

from flask import request

from app.errors import AppError
from app.validators.common import parse_pagination_params

ALLOWED_ADMIN_STATUSES = {"submitted", "shortlisted", "accepted", "rejected"}
ALLOWED_APPLICATION_STATUSES = ALLOWED_ADMIN_STATUSES | {"withdrawn"}


def _validate_optional_text(
    val: Any, field_name: str, max_len: int = 1000
) -> tuple[str | None, str | None]:
    if val is None:
        return None, None
    if not isinstance(val, str):
        return None, f"{field_name} must be a string or null."
    cleaned = val.strip()
    if not cleaned:
        return None, None
    if len(cleaned) > max_len:
        return None, f"{field_name} must not exceed {max_len} characters."
    return cleaned, None


def validate_apply_payload(data: dict[str, Any]) -> str | None:
    """Validate optional note on POST /api/opportunities/<id>/apply."""
    note, err = _validate_optional_text(data.get("note"), "note")
    if err:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid application data.",
            status_code=422,
            details={"fields": {"note": err}},
        )
    return note


def validate_application_status_payload(
    data: dict[str, Any],
) -> tuple[str, str | None, bool]:
    """Validate admin status update payload for PATCH /api/applications/<id>/status."""
    field_errors: dict[str, str] = {}

    raw_status = data.get("status")
    status = ""
    if not isinstance(raw_status, str) or not raw_status.strip():
        field_errors["status"] = "status is required."
    else:
        status = raw_status.strip().lower()
        if status not in ALLOWED_ADMIN_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_ADMIN_STATUSES))
            field_errors["status"] = f"status must be one of: {allowed}."

    update_remarks = "admin_remarks" in data
    remarks: str | None = None
    if update_remarks:
        remarks, err = _validate_optional_text(data.get("admin_remarks"), "admin_remarks")
        if err:
            field_errors["admin_remarks"] = err

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid application status update.",
            status_code=422,
            details={"fields": field_errors},
        )

    return status, remarks, update_remarks


def validate_application_list_params() -> dict[str, Any]:
    """Validate query parameters for listing applications."""
    page, per_page = parse_pagination_params()
    field_errors: dict[str, str] = {}

    raw_status = request.args.get("status")
    status: str | None = None
    if raw_status is not None and raw_status.strip() != "":
        status = raw_status.strip().lower()
        if status not in ALLOWED_APPLICATION_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_APPLICATION_STATUSES))
            field_errors["status"] = f"status must be one of: {allowed}."

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid query parameters.",
            status_code=422,
            details={"fields": field_errors},
        )

    return {"page": page, "per_page": per_page, "status": status}
