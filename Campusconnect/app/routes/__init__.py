"""Blueprint registration."""

from flask import Flask

from app.routes.admin import admin_bp
from app.routes.applications import applications_bp
from app.routes.auth import auth_bp
from app.routes.bookmarks import bookmarks_bp
from app.routes.health import health_bp
from app.routes.opportunities import opportunities_bp
from app.routes.profile import profile_bp


def register_blueprints(app: Flask) -> None:
    """Register all feature blueprints on the Flask application."""
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(opportunities_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(bookmarks_bp)
    app.register_blueprint(admin_bp)
