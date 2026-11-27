"""Common request parsing and validation helpers."""

from typing import Any
from flask import request
from werkzeug.exceptions import BadRequest

from app.errors import AppError


def require_json_body() -> dict[str, Any]:
    """Parse and validate that the request body is a JSON object."""
    try:
        data = request.get_json(force=False, silent=False)
    except BadRequest as exc:
        raise AppError(
            code="INVALID_JSON",
            message="Request body must be valid JSON.",
            status_code=400,
        ) from exc

    if not isinstance(data, dict):
        raise AppError(
            code="BAD_REQUEST",
            message="Request body must be a JSON object.",
            status_code=400,
        )
    return data


def optional_json_body() -> dict[str, Any]:
    """Parse an optional JSON object body, returning {} when the body is empty."""
    if not request.get_data(cache=True):
        return {}
    return require_json_body()


def parse_bool_query_param(
    param_name: str,
    field_errors: dict[str, str],
    *,
    default: bool | None = None,
) -> bool | None:
    """Parse a boolean query parameter ('true'/'1'/'false'/'0')."""
    raw_val = request.args.get(param_name)
    if raw_val is None or raw_val.strip() == "":
        return default
    normalized = raw_val.strip().lower()
    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False
    field_errors[param_name] = f"{param_name} must be 'true' or 'false'."
    return default


def parse_pagination_params(
    default_page: int = 1, default_per_page: int = 10, max_per_page: int = 100
) -> tuple[int, int]:
    """Parse and validate page & per_page query parameters."""
    field_errors: dict[str, str] = {}

    raw_page = request.args.get("page")
    if raw_page is None or raw_page == "":
        page = default_page
    else:
        try:
            page = int(raw_page)
            if page < 1:
                raise ValueError
        except ValueError:
            field_errors["page"] = "page must be an integer >= 1."
            page = default_page

    raw_per_page = request.args.get("per_page")
    if raw_per_page is None or raw_per_page == "":
        per_page = default_per_page
    else:
        try:
            per_page = int(raw_per_page)
            if per_page < 1 or per_page > max_per_page:
                raise ValueError
        except ValueError:
            field_errors["per_page"] = f"per_page must be an integer between 1 and {max_per_page}."
            per_page = default_per_page

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid pagination parameters.",
            status_code=422,
            details={"fields": field_errors},
        )

    return page, per_page
