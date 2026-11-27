"""Bookmark query parameter validators."""

from typing import Any

from app.errors import AppError
from app.validators.common import parse_bool_query_param, parse_pagination_params


def validate_bookmark_list_params() -> dict[str, Any]:
    """Validate query parameters for GET /api/bookmarks."""
    page, per_page = parse_pagination_params()
    field_errors: dict[str, str] = {}
    is_active = parse_bool_query_param("active", field_errors)

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid query parameters.",
            status_code=422,
            details={"fields": field_errors},
        )

    return {"page": page, "per_page": per_page, "is_active": is_active}
