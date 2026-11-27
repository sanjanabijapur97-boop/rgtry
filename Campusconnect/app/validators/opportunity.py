"""Opportunity input validators."""

from typing import Any
from urllib.parse import urlparse

from flask import request

from app.errors import AppError
from app.utils.datetime_utils import parse_deadline_to_utc_iso
from app.validators.common import parse_bool_query_param, parse_pagination_params

ALLOWED_SORT_FIELDS = {"deadline", "created_at", "title", "min_cgpa"}
ALLOWED_SORT_ORDERS = {"asc", "desc"}


def _validate_non_empty_str(
    val: Any, field_label: str, min_len: int, max_len: int
) -> tuple[str | None, str | None]:
    if not isinstance(val, str):
        return None, f"{field_label} must be a string."
    cleaned = val.strip()
    if len(cleaned) < min_len or len(cleaned) > max_len:
        return None, f"{field_label} must be between {min_len} and {max_len} characters."
    return cleaned, None


def _validate_string_list(
    val: Any, field_label: str, max_items: int = 50, max_item_len: int = 60
) -> tuple[list[str] | None, str | None]:
    if not isinstance(val, list):
        return None, f"{field_label} must be an array of strings."
    if len(val) > max_items:
        return None, f"{field_label} cannot exceed {max_items} items."

    cleaned_items: list[str] = []
    seen_lower: set[str] = set()
    for item in val:
        if not isinstance(item, str):
            return None, f"Each entry in {field_label} must be a string."
        cleaned = item.strip()
        if not cleaned or len(cleaned) > max_item_len:
            return (
                None,
                f"Each entry in {field_label} must be 1 to {max_item_len} characters.",
            )
        lowered = cleaned.lower()
        if lowered not in seen_lower:
            seen_lower.add(lowered)
            cleaned_items.append(cleaned)
    return cleaned_items, None


def _validate_eligible_years(val: Any) -> tuple[list[int] | None, str | None]:
    if not isinstance(val, list):
        return None, "eligible_years must be an array of integers."
    cleaned: list[int] = []
    seen: set[int] = set()
    for item in val:
        if isinstance(item, bool) or not isinstance(item, int) or item < 1 or item > 5:
            return None, "Each year in eligible_years must be an integer between 1 and 5."
        if item not in seen:
            seen.add(item)
            cleaned.append(item)
    return sorted(cleaned), None


def _validate_min_cgpa(val: Any) -> tuple[float | None, str | None]:
    if val is None:
        return None, None
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return None, "min_cgpa must be a number between 0.0 and 10.0, or null."
    numeric = float(val)
    if numeric < 0.0 or numeric > 10.0:
        return None, "min_cgpa must be between 0.0 and 10.0."
    return round(numeric, 2), None


def _validate_deadline(val: Any) -> tuple[str | None, str | None]:
    if not isinstance(val, str) or not val.strip():
        return None, "deadline must be an ISO 8601 date (YYYY-MM-DD) or datetime string."
    try:
        return parse_deadline_to_utc_iso(val), None
    except ValueError:
        return None, "deadline must be a valid ISO 8601 date or datetime string."


def _validate_link(val: Any) -> tuple[str | None, str | None]:
    if val is None:
        return None, None
    if not isinstance(val, str):
        return None, "link must be a URL string or null."
    cleaned = val.strip()
    if not cleaned:
        return None, None
    if len(cleaned) > 500:
        return None, "link must not exceed 500 characters."
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None, "link must be a valid http:// or https:// URL."
    return cleaned, None


def _validate_is_active(val: Any) -> tuple[bool | None, str | None]:
    if not isinstance(val, bool):
        return None, "is_active must be a boolean."
    return val, None


def validate_opportunity_payload(
    data: dict[str, Any], *, partial: bool = False
) -> dict[str, Any]:
    """Validate opportunity creation/full update (partial=False) or PATCH (partial=True)."""
    field_errors: dict[str, str] = {}
    parsed: dict[str, Any] = {}

    required_specs = {
        "title": lambda v: _validate_non_empty_str(v, "title", 2, 200),
        "organization": lambda v: _validate_non_empty_str(v, "organization", 2, 150),
        "description": lambda v: _validate_non_empty_str(v, "description", 10, 5000),
        "category": lambda v: _validate_non_empty_str(v, "category", 2, 50),
        "deadline": _validate_deadline,
    }
    optional_specs = {
        "eligible_branches": (lambda v: _validate_string_list(v, "eligible_branches"), []),
        "eligible_years": (_validate_eligible_years, []),
        "min_cgpa": (_validate_min_cgpa, None),
        "required_skills": (lambda v: _validate_string_list(v, "required_skills"), []),
        "link": (_validate_link, None),
        "is_active": (_validate_is_active, True),
    }

    if not partial:
        for field, validator in required_specs.items():
            if field not in data:
                field_errors[field] = f"{field} is required."
            else:
                val, err = validator(data[field])
                if err:
                    field_errors[field] = err
                else:
                    parsed[field] = val.lower() if field == "category" and isinstance(val, str) else val

        for field, (validator, default) in optional_specs.items():
            raw = data.get(field, default)
            val, err = validator(raw)
            if err:
                field_errors[field] = err
            else:
                parsed[field] = val
    else:
        for field, validator in required_specs.items():
            if field in data:
                val, err = validator(data[field])
                if err:
                    field_errors[field] = err
                else:
                    parsed[field] = val.lower() if field == "category" and isinstance(val, str) else val

        for field, (validator, _) in optional_specs.items():
            if field in data:
                val, err = validator(data[field])
                if err:
                    field_errors[field] = err
                else:
                    parsed[field] = val

        if not field_errors and not parsed:
            raise AppError(
                code="VALIDATION_ERROR",
                message="At least one opportunity field must be provided to update.",
                status_code=422,
                details={"fields": {}},
            )

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid opportunity data.",
            status_code=422,
            details={"fields": field_errors},
        )

    return parsed


def _parse_list_query_params(
    *, default_active: bool | None = None, include_eligible_only: bool = False
) -> dict[str, Any]:
    """Parse shared search, filter, sort, and pagination query parameters."""
    page, per_page = parse_pagination_params()
    field_errors: dict[str, str] = {}

    raw_q = request.args.get("q")
    q = raw_q.strip() if isinstance(raw_q, str) and raw_q.strip() else None

    raw_category = request.args.get("category")
    category = (
        raw_category.strip().lower()
        if isinstance(raw_category, str) and raw_category.strip()
        else None
    )

    is_active = parse_bool_query_param("active", field_errors, default=default_active)

    eligible_only = True
    if include_eligible_only:
        parsed_elig = parse_bool_query_param("eligible_only", field_errors, default=True)
        eligible_only = True if parsed_elig is None else parsed_elig

    raw_sort = request.args.get("sort")
    if raw_sort is None or raw_sort.strip() == "":
        sort = "created_at"
    else:
        sort = raw_sort.strip().lower()
        if sort not in ALLOWED_SORT_FIELDS:
            field_errors["sort"] = (
                f"sort must be one of: {', '.join(sorted(ALLOWED_SORT_FIELDS))}."
            )

    raw_order = request.args.get("order")
    if raw_order is None or raw_order.strip() == "":
        order = "desc" if sort == "created_at" else "asc"
    else:
        order = raw_order.strip().lower()
        if order not in ALLOWED_SORT_ORDERS:
            field_errors["order"] = "order must be 'asc' or 'desc'."

    if field_errors:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid query parameters.",
            status_code=422,
            details={"fields": field_errors},
        )

    result: dict[str, Any] = {
        "page": page,
        "per_page": per_page,
        "q": q,
        "category": category,
        "is_active": is_active,
        "sort": sort,
        "order": order,
    }
    if include_eligible_only:
        result["eligible_only"] = eligible_only
    return result


def validate_opportunity_list_params() -> dict[str, Any]:
    """Validate search, filter, sort, and pagination query parameters for GET /api/opportunities."""
    return _parse_list_query_params(default_active=None, include_eligible_only=False)


def validate_eligible_opportunities_params() -> dict[str, Any]:
    """Validate query parameters for GET /api/opportunities/eligible."""
    return _parse_list_query_params(default_active=True, include_eligible_only=True)
