"""Application configuration and environment validation."""

import os
from typing import Any
from dotenv import load_dotenv


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_origins(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        origins = [str(item).strip() for item in value if str(item).strip()]
    else:
        origins = [item.strip() for item in str(value).split(",") if item.strip()]

    if "*" in origins:
        raise RuntimeError("Wildcard '*' is not allowed in FRONTEND_ORIGINS.")
    return origins


def _parse_int(value: Any, default: int, name: str) -> int:
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} must be a valid integer.") from exc


def load_app_config(
    test_config: dict[str, Any] | None = None,
    *,
    load_env: bool = True,
) -> dict[str, Any]:
    """Load and validate application configuration from environment or test overrides."""
    if load_env and test_config is None:
        load_dotenv(override=False)

    overrides = dict(test_config or {})

    secret_key = overrides.get("SECRET_KEY", os.environ.get("SECRET_KEY", ""))
    if not isinstance(secret_key, str) or not secret_key.strip():
        raise RuntimeError(
            "SECRET_KEY environment variable is required and cannot be empty."
        )

    database_url = str(
        overrides.get(
            "DATABASE_URL",
            os.environ.get("DATABASE_URL") or "sqlite:///campusconnect.db",
        )
    ).strip()

    frontend_origins = _parse_origins(
        overrides.get("FRONTEND_ORIGINS", os.environ.get("FRONTEND_ORIGINS", ""))
    )

    host = str(overrides.get("HOST", os.environ.get("HOST") or "0.0.0.0")).strip()
    port = _parse_int(
        overrides.get("PORT", os.environ.get("PORT")), default=5000, name="PORT"
    )
    flask_debug = _parse_bool(
        overrides.get("FLASK_DEBUG", os.environ.get("FLASK_DEBUG")), default=False
    )
    jwt_expiry_hours = _parse_int(
        overrides.get("JWT_EXPIRY_HOURS", os.environ.get("JWT_EXPIRY_HOURS")),
        default=24,
        name="JWT_EXPIRY_HOURS",
    )
    if jwt_expiry_hours <= 0:
        raise RuntimeError("JWT_EXPIRY_HOURS must be a positive integer.")

    config: dict[str, Any] = {
        "SECRET_KEY": secret_key.strip(),
        "DATABASE_URL": database_url,
        "FRONTEND_ORIGINS": frontend_origins,
        "HOST": host,
        "PORT": port,
        "FLASK_DEBUG": flask_debug,
        "DEBUG": flask_debug,
        "JWT_EXPIRY_HOURS": jwt_expiry_hours,
        "PROPAGATE_EXCEPTIONS": False,
    }

    handled_keys = {
        "SECRET_KEY",
        "DATABASE_URL",
        "FRONTEND_ORIGINS",
        "HOST",
        "PORT",
        "FLASK_DEBUG",
        "JWT_EXPIRY_HOURS",
    }
    for key, val in overrides.items():
        if key not in handled_keys:
            config[key] = val

    return config
