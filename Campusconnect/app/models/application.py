"""Application database operations."""

import json
import sqlite3
from typing import Any

from app.db import get_db
from app.utils.datetime_utils import utc_now_iso


class ApplicationModel:
    """Data access layer for student applications to opportunities."""

    @staticmethod
    def find_by_id(application_id: int) -> sqlite3.Row | None:
        return get_db().execute(
            """
            SELECT a.*,
                   o.title AS opportunity_title,
                   o.organization AS opportunity_organization,
                   o.category AS opportunity_category,
                   o.deadline AS opportunity_deadline,
                   o.is_active AS opportunity_is_active,
                   u.email AS student_email,
                   sp.name AS student_name,
                   sp.branch AS student_branch,
                   sp.year AS student_year,
                   sp.cgpa AS student_cgpa,
                   sp.skills AS student_skills,
                   sp.phone AS student_phone
            FROM applications a
            JOIN opportunities o ON o.id = a.opportunity_id
            JOIN users u ON u.id = a.user_id
            LEFT JOIN student_profiles sp ON sp.user_id = a.user_id
            WHERE a.id = ?
            """,
            (application_id,),
        ).fetchone()

    @staticmethod
    def find_by_user_and_opportunity(
        user_id: int, opportunity_id: int
    ) -> sqlite3.Row | None:
        return get_db().execute(
            """
            SELECT a.*,
                   o.title AS opportunity_title,
                   o.organization AS opportunity_organization,
                   o.category AS opportunity_category,
                   o.deadline AS opportunity_deadline,
                   o.is_active AS opportunity_is_active,
                   u.email AS student_email,
                   sp.name AS student_name,
                   sp.branch AS student_branch,
                   sp.year AS student_year,
                   sp.cgpa AS student_cgpa,
                   sp.skills AS student_skills,
                   sp.phone AS student_phone
            FROM applications a
            JOIN opportunities o ON o.id = a.opportunity_id
            JOIN users u ON u.id = a.user_id
            LEFT JOIN student_profiles sp ON sp.user_id = a.user_id
            WHERE a.user_id = ? AND a.opportunity_id = ?
            """,
            (user_id, opportunity_id),
        ).fetchone()

    @staticmethod
    def create_or_reapply(
        user_id: int, opportunity_id: int, note: str | None = None
    ) -> sqlite3.Row:
        """Create a new application or reactivate a previously withdrawn one."""
        db = get_db()
        now = utc_now_iso()
        existing = db.execute(
            "SELECT id, status FROM applications WHERE user_id = ? AND opportunity_id = ?",
            (user_id, opportunity_id),
        ).fetchone()

        if existing is not None:
            db.execute(
                """
                UPDATE applications
                SET status = 'submitted', note = ?, admin_remarks = NULL, updated_at = ?
                WHERE id = ?
                """,
                (note, now, existing["id"]),
            )
            db.commit()
            row = ApplicationModel.find_by_id(int(existing["id"]))
        else:
            cursor = db.execute(
                """
                INSERT INTO applications (
                    opportunity_id, user_id, status, note, admin_remarks, created_at, updated_at
                ) VALUES (?, ?, 'submitted', ?, NULL, ?, ?)
                """,
                (opportunity_id, user_id, note, now, now),
            )
            db.commit()
            row = ApplicationModel.find_by_id(int(cursor.lastrowid))

        assert row is not None
        return row

    @staticmethod
    def list_for_student(
        user_id: int,
        page: int,
        per_page: int,
        *,
        status: str | None = None,
    ) -> tuple[list[sqlite3.Row], int]:
        db = get_db()
        where_clauses = ["a.user_id = ?"]
        params: list[Any] = [user_id]
        if status is not None:
            where_clauses.append("a.status = ?")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(where_clauses)}"
        total = db.execute(
            f"SELECT COUNT(*) FROM applications a {where_sql}",
            tuple(params),
        ).fetchone()[0]

        offset = (page - 1) * per_page
        rows = db.execute(
            f"""
            SELECT a.*,
                   o.title AS opportunity_title,
                   o.organization AS opportunity_organization,
                   o.category AS opportunity_category,
                   o.deadline AS opportunity_deadline,
                   o.is_active AS opportunity_is_active,
                   u.email AS student_email,
                   sp.name AS student_name,
                   sp.branch AS student_branch,
                   sp.year AS student_year,
                   sp.cgpa AS student_cgpa,
                   sp.skills AS student_skills,
                   sp.phone AS student_phone
            FROM applications a
            JOIN opportunities o ON o.id = a.opportunity_id
            JOIN users u ON u.id = a.user_id
            LEFT JOIN student_profiles sp ON sp.user_id = a.user_id
            {where_sql}
            ORDER BY a.updated_at DESC, a.id DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params + [per_page, offset]),
        ).fetchall()
        return rows, int(total)

    @staticmethod
    def list_for_opportunity(
        opportunity_id: int,
        page: int,
        per_page: int,
        *,
        status: str | None = None,
    ) -> tuple[list[sqlite3.Row], int]:
        db = get_db()
        where_clauses = ["a.opportunity_id = ?"]
        params: list[Any] = [opportunity_id]
        if status is not None:
            where_clauses.append("a.status = ?")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(where_clauses)}"
        total = db.execute(
            f"SELECT COUNT(*) FROM applications a {where_sql}",
            tuple(params),
        ).fetchone()[0]

        offset = (page - 1) * per_page
        rows = db.execute(
            f"""
            SELECT a.*,
                   o.title AS opportunity_title,
                   o.organization AS opportunity_organization,
                   o.category AS opportunity_category,
                   o.deadline AS opportunity_deadline,
                   o.is_active AS opportunity_is_active,
                   u.email AS student_email,
                   sp.name AS student_name,
                   sp.branch AS student_branch,
                   sp.year AS student_year,
                   sp.cgpa AS student_cgpa,
                   sp.skills AS student_skills,
                   sp.phone AS student_phone
            FROM applications a
            JOIN opportunities o ON o.id = a.opportunity_id
            JOIN users u ON u.id = a.user_id
            LEFT JOIN student_profiles sp ON sp.user_id = a.user_id
            {where_sql}
            ORDER BY a.created_at DESC, a.id DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params + [per_page, offset]),
        ).fetchall()
        return rows, int(total)

    @staticmethod
    def update_status(
        application_id: int,
        status: str,
        *,
        admin_remarks: str | None = None,
        update_remarks: bool = False,
    ) -> sqlite3.Row | None:
        db = get_db()
        now = utc_now_iso()
        if update_remarks:
            db.execute(
                """
                UPDATE applications
                SET status = ?, admin_remarks = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, admin_remarks, now, application_id),
            )
        else:
            db.execute(
                """
                UPDATE applications
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, now, application_id),
            )
        db.commit()
        return ApplicationModel.find_by_id(application_id)

    @staticmethod
    def serialize(
        row: sqlite3.Row, *, include_applicant: bool = False
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": row["id"],
            "opportunity_id": row["opportunity_id"],
            "user_id": row["user_id"],
            "status": row["status"],
            "note": row["note"],
            "admin_remarks": row["admin_remarks"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "opportunity": {
                "id": row["opportunity_id"],
                "title": row["opportunity_title"],
                "organization": row["opportunity_organization"],
                "category": row["opportunity_category"],
                "deadline": row["opportunity_deadline"],
                "is_active": bool(row["opportunity_is_active"]),
            },
        }
        if include_applicant:
            try:
                skills = json.loads(row["student_skills"] or "[]")
            except (TypeError, ValueError):
                skills = []
            payload["applicant"] = {
                "user_id": row["user_id"],
                "email": row["student_email"],
                "name": row["student_name"],
                "branch": row["student_branch"],
                "year": row["student_year"],
                "cgpa": row["student_cgpa"],
                "skills": skills,
                "phone": row["student_phone"],
            }
        return payload
