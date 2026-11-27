"""Shared pytest fixtures."""

import pytest

from app import create_app
from app.db import init_db


@pytest.fixture()
def app(tmp_path):
    """Create a fresh Flask application and SQLite database per test."""
    db_file = tmp_path / "test_campusconnect.db"
    application = create_app(
        test_config={
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-not-for-production",
            "DATABASE_URL": f"sqlite:///{db_file.as_posix()}",
            "FRONTEND_ORIGINS": "http://localhost:5173,http://192.168.1.20:5173",
        },
        load_env=False,
    )

    with application.app_context():
        init_db()
        yield application


@pytest.fixture()
def client(app):
    """Return a Flask test client."""
    return app.test_client()
