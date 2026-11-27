"""Bookmark database operations."""

import sqlite3
from typing import Any

from app.db import get_db
from app.models.opportunity import OpportunityModel
from app.utils.datetime_utils import utc_now_iso


class BookmarkModel:
    """Data access layer for student saved/bookmarked opportunities."""

    @staticmethod
    def find_by_user_and_opportunity(
        user_id: int, opportunity_id: int
    ) -> sqlite3.Row | None:
        return get_db().execute(
            """
            SELECT * FROM bookmarks
            WHERE user_id = ? AND opportunity_id = ?
            """,
            (user_id, opportunity_id),
        ).fetchone()

    @staticmethod
    def create(user_id: int, opportunity_id: int) -> tuple[sqlite3.Row, bool]:
        """Save an opportunity for a student; returns (bookmark_row, created)."""
        existing = BookmarkModel.find_by_user_and_opportunity(user_id, opportunity_id)
        if existing is not None:
            return existing, False

        db = get_db()
        now = utc_now_iso()
        cursor = db.execute(
            """
            INSERT INTO bookmarks (opportunity_id, user_id, created_at)
            VALUES (?, ?, ?)
            """,
            (opportunity_id, user_id, now),
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM bookmarks WHERE id = ?",
            (int(cursor.lastrowid),),
        ).fetchone()
        assert row is not None
        return row, True

    @staticmethod
    def delete(user_id: int, opportunity_id: int) -> bool:
        db = get_db()
        cursor = db.execute(
            "DELETE FROM bookmarks WHERE user_id = ? AND opportunity_id = ?",
            (user_id, opportunity_id),
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def list_for_student(
        user_id: int,
        page: int,
        per_page: int,
        *,
        is_active: bool | None = None,
    ) -> tuple[list[sqlite3.Row], int]:
        db = get_db()
        where_clauses = ["b.user_id = ?"]
        params: list[Any] = [user_id]
        if is_active is not None:
            where_clauses.append("o.is_active = ?")
            params.append(1 if is_active else 0)

        where_sql = f"WHERE {' AND '.join(where_clauses)}"
        total = db.execute(
            f"""
            SELECT COUNT(*)
            FROM bookmarks b
            JOIN opportunities o ON o.id = b.opportunity_id
            {where_sql}
            """,
            tuple(params),
        ).fetchone()[0]

        offset = (page - 1) * per_page
        rows = db.execute(
            f"""
            SELECT o.*,
                   b.id AS bookmark_id,
                   b.created_at AS bookmarked_at
            FROM bookmarks b
            JOIN opportunities o ON o.id = b.opportunity_id
            {where_sql}
            ORDER BY b.created_at DESC, b.id DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params + [per_page, offset]),
        ).fetchall()
        return rows, int(total)

    @staticmethod
    def serialize_bookmark(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "opportunity_id": row["opportunity_id"],
            "user_id": row["user_id"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def serialize_saved_item(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "bookmark_id": row["bookmark_id"],
            "bookmarked_at": row["bookmarked_at"],
            "opportunity": OpportunityModel.serialize(row),
        }
