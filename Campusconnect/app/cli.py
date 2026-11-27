"""Flask CLI commands."""

import click
from flask import Flask

from app.db import init_db
from app.errors import AppError
from app.services.auth_service import create_admin_user
from app.services.seed_service import seed_sample_data
from app.validators.auth import validate_admin_cli_input


def register_cli(app: Flask) -> None:
    """Register custom management CLI commands."""

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Initialize the SQLite database tables."""
        init_db()
        click.echo("Initialized the database.")

    @app.cli.command("seed-db")
    def seed_db_command() -> None:
        """Initialize tables and seed sample admin, student, and opportunities."""
        init_db()
        summary = seed_sample_data()
        click.echo(
            "Seed complete: "
            f"admin_created={summary['admin_created']} ({summary['admin_email']}), "
            f"student_created={summary['student_created']} ({summary['student_email']}), "
            f"opportunities_created={summary['opportunities_created']}"
        )

    @app.cli.command("create-admin")
    @click.option("--email", required=True, help="Admin email address.")
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Admin password (min 8 characters).",
    )
    def create_admin_command(email: str, password: str) -> None:
        """Create an admin user (the only supported way to create admins)."""
        init_db()
        try:
            normalized_email, valid_password = validate_admin_cli_input(email, password)
            admin = create_admin_user(normalized_email, valid_password)
        except AppError as exc:
            raise click.ClickException(exc.message) from exc

        click.echo(f"Admin user created: {admin['email']} (id={admin['id']})")
