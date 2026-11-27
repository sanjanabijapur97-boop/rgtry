"""Standardized JSON response helpers."""

import math
from typing import Any
from flask import Response, jsonify


def success_response(
    data: Any = None, status_code: int = 200
) -> tuple[Response, int]:
    """Return a standard success JSON envelope."""
    return jsonify({"success": True, "data": data}), status_code


def error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> tuple[Response, int]:
    """Return a standard error JSON envelope."""
    return (
        jsonify(
            {
                "success": False,
                "error": {
                    "code": code,
                    "message": message,
                    "details": details if details is not None else {},
                },
            }
        ),
        status_code,
    )


def paginated_payload(
    items: list[Any], page: int, per_page: int, total: int
) -> dict[str, Any]:
    """Wrap paginated items with pagination metadata."""
    pages = math.ceil(total / per_page) if per_page > 0 and total > 0 else 0
    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1 and pages > 0,
        },
    }
