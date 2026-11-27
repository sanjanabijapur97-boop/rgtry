"""Flask application factory."""

import os
from typing import Any
from flask import Flask

from app.cli import register_cli
from app.config import load_app_config
from app.errors import register_error_handlers
from app.extensions import init_extensions
from app.routes import register_blueprints


def create_app(
    test_config: dict[str, Any] | None = None,
    *,
    load_env: bool = True,
) -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    config = load_app_config(test_config=test_config, load_env=load_env)
    app.config.update(config)

    init_extensions(app)
    register_error_handlers(app)
    register_blueprints(app)
    register_cli(app)

    return app
