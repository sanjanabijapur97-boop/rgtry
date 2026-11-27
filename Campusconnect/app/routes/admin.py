"""Admin dashboard and analytics blueprint."""

from flask import Blueprint, Response

from app.services.admin_service import get_admin_stats
from app.utils.auth import require_role
from app.utils.response import success_response

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/stats")
@require_role("admin")
def admin_stats_route() -> tuple[Response, int]:
    """Return platform-wide aggregate statistics (admin only)."""
    return success_response(get_admin_stats(), status_code=200)
