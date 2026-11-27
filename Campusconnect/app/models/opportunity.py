"""Opportunity database operations."""

import json
import sqlite3
from typing import Any

from app.db import get_db
from app.utils.datetime_utils import utc_now_iso


class OpportunityModel:
    """Data access layer for opportunities."""

    @staticmethod
    def create(data: dict[str, Any], created_by: int) -> sqlite3.Row:
        db = get_db()
        now = utc_now_iso()
        cursor = db.execute(
            """
            INSERT INTO opportunities (
                title, organization, description, category,
                eligible_branches, eligible_years, min_cgpa, required_skills,
                deadline, link, is_active, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["title"],
                data["organization"],
                data["description"],
                data["category"],
                json.dumps(data["eligible_branches"]),
                json.dumps(data["eligible_years"]),
                data["min_cgpa"],
                json.dumps(data["required_skills"]),
                data["deadline"],
                data["link"],
                1 if data["is_active"] else 0,
                created_by,
                now,
                now,
            ),
        )
        db.commit()
        created = OpportunityModel.find_by_id(int(cursor.lastrowid))
        assert created is not None
        return created

    @staticmethod
    def find_by_id(opportunity_id: int) -> sqlite3.Row | None:
        return get_db().execute(
            "SELECT * FROM opportunities WHERE id = ?",
            (opportunity_id,),
        ).fetchone()

    @staticmethod
    def _escape_like(term: str) -> str:
        return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @staticmethod
    def _build_filter_and_order(
        *,
        q: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[str, list[Any], str]:
        where_clauses: list[str] = []
        params: list[Any] = []

        if q is not None:
            like_pattern = f"%{OpportunityModel._escape_like(q.lower())}%"
            where_clauses.append(
                """
                (
                    LOWER(title) LIKE ? ESCAPE '\\'
                    OR LOWER(organization) LIKE ? ESCAPE '\\'
                    OR LOWER(description) LIKE ? ESCAPE '\\'
                    OR LOWER(category) LIKE ? ESCAPE '\\'
                    OR LOWER(required_skills) LIKE ? ESCAPE '\\'
                )
                """
            )
            params.extend([like_pattern] * 5)

        if category is not None:
            where_clauses.append("LOWER(category) = ?")
            params.append(category.lower())

        if is_active is not None:
            where_clauses.append("is_active = ?")
            params.append(1 if is_active else 0)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        direction = "ASC" if order == "asc" else "DESC"
        sort_expressions = {
            "created_at": f"created_at {direction}, id {direction}",
            "deadline": f"deadline {direction}, id DESC",
            "title": f"LOWER(title) {direction}, id DESC",
            "min_cgpa": f"min_cgpa IS NULL, min_cgpa {direction}, id DESC",
        }
        order_by_sql = sort_expressions.get(sort, "created_at DESC, id DESC")
        return where_sql, params, order_by_sql

    @staticmethod
    def list_matching(
        *,
        q: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> list[sqlite3.Row]:
        db = get_db()
        where_sql, params, order_by_sql = OpportunityModel._build_filter_and_order(
            q=q,
            category=category,
            is_active=is_active,
            sort=sort,
            order=order,
        )
        return db.execute(
            f"""
            SELECT * FROM opportunities
            {where_sql}
            ORDER BY {order_by_sql}
            """,
            tuple(params),
        ).fetchall()

    @staticmethod
    def list_paginated(
        page: int,
        per_page: int,
        *,
        q: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[sqlite3.Row], int]:
        db = get_db()
        where_sql, params, order_by_sql = OpportunityModel._build_filter_and_order(
            q=q,
            category=category,
            is_active=is_active,
            sort=sort,
            order=order,
        )

        total = db.execute(
            f"SELECT COUNT(*) FROM opportunities {where_sql}",
            tuple(params),
        ).fetchone()[0]

        offset = (page - 1) * per_page
        rows = db.execute(
            f"""
            SELECT * FROM opportunities
            {where_sql}
            ORDER BY {order_by_sql}
            LIMIT ? OFFSET ?
            """,
            tuple(params + [per_page, offset]),
        ).fetchall()
        return rows, int(total)

    @staticmethod
    def update(opportunity_id: int, updates: dict[str, Any]) -> sqlite3.Row | None:
        db = get_db()
        allowed = (
            "title",
            "organization",
            "description",
            "category",
            "eligible_branches",
            "eligible_years",
            "min_cgpa",
            "required_skills",
            "deadline",
            "link",
            "is_active",
        )
        assignments: list[str] = []
        values: list[Any] = []

        for field in allowed:
            if field in updates:
                assignments.append(f"{field} = ?")
                val = updates[field]
                if field in ("eligible_branches", "eligible_years", "required_skills"):
                    val = json.dumps(val)
                elif field == "is_active":
                    val = 1 if val else 0
                values.append(val)

        if not assignments:
            return OpportunityModel.find_by_id(opportunity_id)

        assignments.append("updated_at = ?")
        values.append(utc_now_iso())
        values.append(opportunity_id)

        db.execute(
            f"UPDATE opportunities SET {', '.join(assignments)} WHERE id = ?",
            tuple(values),
        )
        db.commit()
        return OpportunityModel.find_by_id(opportunity_id)

    @staticmethod
    def delete(opportunity_id: int) -> bool:
        db = get_db()
        cursor = db.execute("DELETE FROM opportunities WHERE id = ?", (opportunity_id,))
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def serialize(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "organization": row["organization"],
            "description": row["description"],
            "category": row["category"],
            "eligible_branches": json.loads(row["eligible_branches"] or "[]"),
            "eligible_years": json.loads(row["eligible_years"] or "[]"),
            "min_cgpa": row["min_cgpa"],
            "required_skills": json.loads(row["required_skills"] or "[]"),
            "deadline": row["deadline"],
            "link": row["link"],
            "is_active": bool(row["is_active"]),
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
