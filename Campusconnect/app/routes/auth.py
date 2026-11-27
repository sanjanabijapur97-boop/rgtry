"""Authentication blueprint."""

from flask import Blueprint, Response, g

from app.services.auth_service import (
    change_user_password,
    get_current_user_data,
    login_user,
    register_student,
)
from app.utils.auth import require_auth
from app.utils.response import success_response
from app.validators.auth import (
    validate_change_password_payload,
    validate_login_payload,
    validate_register_payload,
)
from app.validators.common import require_json_body

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register() -> tuple[Response, int]:
    """Register a new student account."""
    body = require_json_body()
    name, email, password = validate_register_payload(body)
    result = register_student(name=name, email=email, password=password)
    return success_response(result, status_code=201)


@auth_bp.post("/login")
def login() -> tuple[Response, int]:
    """Authenticate user credentials and return a Bearer JWT."""
    body = require_json_body()
    email, password = validate_login_payload(body)
    result = login_user(email=email, password=password)
    return success_response(result, status_code=200)


@auth_bp.get("/me")
@require_auth
def me() -> tuple[Response, int]:
    """Return the currently authenticated user."""
    return success_response(get_current_user_data(g.current_user), status_code=200)


@auth_bp.post("/change-password")
@require_auth
def change_password() -> tuple[Response, int]:
    """Update the authenticated user's password."""
    body = require_json_body()
    current_password, new_password = validate_change_password_payload(body)
    result = change_user_password(g.current_user, current_password, new_password)
    return success_response(result, status_code=200)
