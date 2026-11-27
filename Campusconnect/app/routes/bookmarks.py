"""Bookmarks blueprint for student saved opportunities."""

from flask import Blueprint, Response, g

from app.services.bookmark_service import (
    add_bookmark,
    list_student_bookmarks,
    remove_bookmark,
)
from app.utils.auth import require_role
from app.utils.response import success_response
from app.validators.bookmark import validate_bookmark_list_params

bookmarks_bp = Blueprint("bookmarks", __name__, url_prefix="/api")


@bookmarks_bp.get("/bookmarks")
@require_role("student")
def list_bookmarks_route() -> tuple[Response, int]:
    """List the authenticated student's bookmarked opportunities."""
    params = validate_bookmark_list_params()
    result = list_student_bookmarks(g.current_user["id"], **params)
    return success_response(result, status_code=200)


@bookmarks_bp.post("/opportunities/<int:opportunity_id>/bookmark")
@require_role("student")
def add_bookmark_route(opportunity_id: int) -> tuple[Response, int]:
    """Bookmark an opportunity (student only)."""
    result, status_code = add_bookmark(
        user_id=g.current_user["id"], opportunity_id=opportunity_id
    )
    return success_response(result, status_code=status_code)


@bookmarks_bp.delete("/opportunities/<int:opportunity_id>/bookmark")
@require_role("student")
def remove_bookmark_route(opportunity_id: int) -> tuple[Response, int]:
    """Remove a bookmark for an opportunity (student only)."""
    result = remove_bookmark(
        user_id=g.current_user["id"], opportunity_id=opportunity_id
    )
    return success_response(result, status_code=200)
