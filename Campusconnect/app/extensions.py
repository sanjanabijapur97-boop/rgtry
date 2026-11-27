"""Shared Flask extensions."""

from flask import Flask
from flask_cors import CORS

from app.db import init_app_db

cors = CORS()


def init_extensions(app: Flask) -> None:
    """Initialize SQLite database hooks and strict CORS policy."""
    init_app_db(app)

    origins = app.config.get("FRONTEND_ORIGINS", [])
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": origins,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Authorization", "Content-Type"],
            }
        },
        supports_credentials=False,
    )
