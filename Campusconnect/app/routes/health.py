"""Health check blueprint."""

from datetime import datetime, timezone
from flask import Blueprint, Response

from app.db import get_db
from app.errors import AppError
from app.utils.response import success_response

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health_check() -> tuple[Response, int]:
    """Verify service availability and SQLite database connectivity."""
    try:
        get_db().execute("SELECT 1").fetchone()
    except Exception as exc:
        raise AppError(
            code="DATABASE_UNAVAILABLE",
            message="Database connectivity check failed.",
            status_code=500,
        ) from exc

    return success_response(
        {
            "status": "ok",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        status_code=200,
    )
