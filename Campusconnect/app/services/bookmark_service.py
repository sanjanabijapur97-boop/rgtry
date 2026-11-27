"""Bookmark business logic."""

from typing import Any

from app.errors import AppError
from app.models.bookmark import BookmarkModel
from app.models.opportunity import OpportunityModel
from app.utils.response import paginated_payload


def add_bookmark(user_id: int, opportunity_id: int) -> tuple[dict[str, Any], int]:
    """Bookmark an opportunity for a student."""
    if OpportunityModel.find_by_id(opportunity_id) is None:
        raise AppError(
            code="OPPORTUNITY_NOT_FOUND",
            message="Opportunity not found.",
            status_code=404,
        )

    row, created = BookmarkModel.create(user_id, opportunity_id)
    status_code = 201 if created else 200
    return {
        "bookmark": BookmarkModel.serialize_bookmark(row),
        "already_bookmarked": not created,
    }, status_code


def remove_bookmark(user_id: int, opportunity_id: int) -> dict[str, Any]:
    """Remove a student's bookmark for an opportunity."""
    deleted = BookmarkModel.delete(user_id, opportunity_id)
    if not deleted:
        raise AppError(
            code="BOOKMARK_NOT_FOUND",
            message="Bookmark not found for this opportunity.",
            status_code=404,
        )
    return {"deleted": True, "opportunity_id": opportunity_id}


def list_student_bookmarks(
    user_id: int,
    page: int,
    per_page: int,
    *,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """List paginated bookmarked opportunities for the authenticated student."""
    rows, total = BookmarkModel.list_for_student(
        user_id, page, per_page, is_active=is_active
    )
    items = [BookmarkModel.serialize_saved_item(row) for row in rows]
    return paginated_payload(items=items, page=page, per_page=per_page, total=total)
