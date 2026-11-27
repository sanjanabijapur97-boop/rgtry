"""JWT token utilities and authentication/authorization decorators."""

from datetime import timedelta
from functools import wraps
from typing import Callable, TypeVar
import jwt
from flask import current_app, g, request

from app.errors import AppError
from app.models.user import UserModel
from app.utils.datetime_utils import to_utc_iso, utc_now

F = TypeVar("F", bound=Callable[..., object])


def create_access_token(user_id: int, role: str) -> tuple[str, int, str]:
    """Generate a signed HS256 JWT and return (token, expires_in_seconds, expires_at_iso)."""
    now = utc_now()
    expiry_hours = int(current_app.config["JWT_EXPIRY_HOURS"])
    expires_delta = timedelta(hours=expiry_hours)
    expires_at = now + expires_delta

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
    return token, int(expires_delta.total_seconds()), to_utc_iso(expires_at)


def decode_access_token(token: str) -> dict:
    """Decode and validate a Bearer JWT."""
    try:
        return jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError(
            code="TOKEN_EXPIRED",
            message="Authentication token has expired.",
            status_code=401,
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise AppError(
            code="INVALID_TOKEN",
            message="Authentication token is invalid.",
            status_code=401,
        ) from exc


def _extract_bearer_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise AppError(
            code="UNAUTHORIZED",
            message="Missing or invalid Authorization Bearer token.",
            status_code=401,
        )
    return parts[1]


def require_auth(fn: F) -> F:
    """Require a valid Bearer JWT and attach the authenticated user to flask.g."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        claims = decode_access_token(token)
        raw_sub = claims.get("sub")
        try:
            user_id = int(raw_sub)
        except (TypeError, ValueError) as exc:
            raise AppError(
                code="INVALID_TOKEN",
                message="Authentication token subject is invalid.",
                status_code=401,
            ) from exc

        user = UserModel.find_by_id(user_id)
        if user is None:
            raise AppError(
                code="UNAUTHORIZED",
                message="Authenticated user no longer exists.",
                status_code=401,
            )

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def require_role(*allowed_roles: str) -> Callable[[F], F]:
    """Require authentication and verify the user holds one of the allowed roles."""

    def decorator(fn: F) -> F:
        @wraps(fn)
        @require_auth
        def wrapper(*args, **kwargs):
            user = g.current_user
            if user["role"] not in allowed_roles:
                raise AppError(
                    code="FORBIDDEN",
                    message="You do not have permission to perform this action.",
                    status_code=403,
                )
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
