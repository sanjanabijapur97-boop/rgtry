"""Student profile database operations."""

import json
import sqlite3
from typing import Any

from app.db import get_db
from app.utils.datetime_utils import utc_now_iso


class StudentProfileModel:
    """Data access layer for student_profiles."""

    @staticmethod
    def find_by_user_id(user_id: int) -> sqlite3.Row | None:
        return get_db().execute(
            """
            SELECT sp.id, sp.user_id, u.email, sp.name, sp.branch, sp.year,
                   sp.cgpa, sp.skills, sp.phone, sp.created_at, sp.updated_at
            FROM student_profiles sp
            JOIN users u ON u.id = sp.user_id
            WHERE sp.user_id = ?
            """,
            (user_id,),
        ).fetchone()

    @staticmethod
    def update(user_id: int, updates: dict[str, Any]) -> sqlite3.Row | None:
        db = get_db()
        allowed = ("name", "branch", "year", "cgpa", "skills", "phone")
        assignments: list[str] = []
        values: list[Any] = []

        for field in allowed:
            if field in updates:
                assignments.append(f"{field} = ?")
                val = updates[field]
                if field == "skills":
                    val = json.dumps(val)
                values.append(val)

        if not assignments:
            return StudentProfileModel.find_by_user_id(user_id)

        assignments.append("updated_at = ?")
        values.append(utc_now_iso())
        values.append(user_id)

        db.execute(
            f"UPDATE student_profiles SET {', '.join(assignments)} WHERE user_id = ?",
            tuple(values),
        )
        db.commit()
        return StudentProfileModel.find_by_user_id(user_id)

    @staticmethod
    def serialize(row: sqlite3.Row) -> dict[str, Any]:
        try:
            skills = json.loads(row["skills"]) if row["skills"] else []
        except (TypeError, ValueError):
            skills = []

        return {
            "user_id": row["user_id"],
            "email": row["email"],
            "name": row["name"],
            "branch": row["branch"],
            "year": row["year"],
            "cgpa": row["cgpa"],
            "skills": skills,
            "phone": row["phone"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
