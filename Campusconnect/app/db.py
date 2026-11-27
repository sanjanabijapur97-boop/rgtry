"""SQLite database connection and schema initialization helpers."""

import os
import sqlite3
from flask import Flask, current_app, g


def resolve_sqlite_path(database_url: str, instance_path: str) -> str:
    """Resolve a sqlite:/// URL into a filesystem path or :memory:."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise RuntimeError("DATABASE_URL must use the 'sqlite:///' scheme.")

    raw_path = database_url[len(prefix) :]
    if not raw_path:
        raise RuntimeError("DATABASE_URL cannot have an empty sqlite path.")

    if raw_path == ":memory:":
        return ":memory:"

    if os.path.isabs(raw_path):
        db_path = os.path.normpath(raw_path)
    else:
        db_path = os.path.normpath(os.path.join(instance_path, raw_path))

    parent_dir = os.path.dirname(db_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    return db_path


def get_db() -> sqlite3.Connection:
    """Return the per-request SQLite connection with foreign keys enabled."""
    if "_sqlite_db" not in g:
        db_path = current_app.config["SQLITE_DB_PATH"]
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g._sqlite_db = conn
    return g._sqlite_db


def close_db(_exception: BaseException | None = None) -> None:
    """Close the per-request SQLite connection if opened."""
    conn = g.pop("_sqlite_db", None)
    if conn is not None:
        conn.close()


from app.models.schema import SCHEMA_STATEMENTS


def init_db() -> None:
    """Initialize SQLite schema tables."""
    conn = get_db()
    conn.execute("PRAGMA foreign_keys = ON;")
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)
    conn.commit()


def init_app_db(app: Flask) -> None:
    """Resolve DB path on app startup and register teardown handler."""
    app.config["SQLITE_DB_PATH"] = resolve_sqlite_path(
        app.config["DATABASE_URL"], app.instance_path
    )
    app.teardown_appcontext(close_db)
