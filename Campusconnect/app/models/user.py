"""User and student profile database operations."""

import sqlite3
from typing import Any
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db
from app.utils.datetime_utils import utc_now_iso


class UserModel:
    """Data access layer for users and student profile initialization."""

    @staticmethod
    def find_by_email(email: str) -> sqlite3.Row | None:
        db = get_db()
        return db.execute(
            """
            SELECT u.id, u.email, u.password_hash, u.role, u.created_at, u.updated_at,
                   sp.name AS student_name
            FROM users u
            LEFT JOIN student_profiles sp ON sp.user_id = u.id
            WHERE u.email = ?
            """,
            (email,),
        ).fetchone()

    @staticmethod
    def find_by_id(user_id: int) -> sqlite3.Row | None:
        db = get_db()
        return db.execute(
            """
            SELECT u.id, u.email, u.password_hash, u.role, u.created_at, u.updated_at,
                   sp.name AS student_name
            FROM users u
            LEFT JOIN student_profiles sp ON sp.user_id = u.id
            WHERE u.id = ?
            """,
            (user_id,),
        ).fetchone()

    @staticmethod
    def create_student(name: str, email: str, password: str) -> sqlite3.Row:
        """Create a student user and matching student_profiles row atomically."""
        db = get_db()
        now = utc_now_iso()
        password_hash = generate_password_hash(password)

        try:
            cursor = db.execute(
                """
                INSERT INTO users (email, password_hash, role, created_at, updated_at)
                VALUES (?, ?, 'student', ?, ?)
                """,
                (email, password_hash, now, now),
            )
            user_id = cursor.lastrowid
            db.execute(
                """
                INSERT INTO student_profiles (user_id, name, skills, created_at, updated_at)
                VALUES (?, ?, '[]', ?, ?)
                """,
                (user_id, name, now, now),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        created = UserModel.find_by_id(int(user_id))
        assert created is not None
        return created

    @staticmethod
    def create_admin(email: str, password: str) -> sqlite3.Row:
        """Create an admin user (CLI-only operation)."""
        db = get_db()
        now = utc_now_iso()
        password_hash = generate_password_hash(password)

        try:
            cursor = db.execute(
                """
                INSERT INTO users (email, password_hash, role, created_at, updated_at)
                VALUES (?, ?, 'admin', ?, ?)
                """,
                (email, password_hash, now, now),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        created = UserModel.find_by_id(int(cursor.lastrowid))
        assert created is not None
        return created

    @staticmethod
    def verify_password(user_row: sqlite3.Row, password: str) -> bool:
        return check_password_hash(user_row["password_hash"], password)

    @staticmethod
    def update_password(user_id: int, new_password: str) -> None:
        """Update a user's password hash and updated_at timestamp."""
        db = get_db()
        db.execute(
            """
            UPDATE users
            SET password_hash = ?, updated_at = ?
            WHERE id = ?
            """,
            (generate_password_hash(new_password), utc_now_iso(), user_id),
        )
        db.commit()

    @staticmethod
    def serialize(user_row: sqlite3.Row) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": user_row["id"],
            "email": user_row["email"],
            "role": user_row["role"],
            "created_at": user_row["created_at"],
        }
        if user_row["role"] == "student":
            payload["name"] = user_row["student_name"]
        return payload
