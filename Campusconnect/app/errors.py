"""Centralized JSON error classes and Flask error handlers."""

from typing import Any
from flask import Flask, Response
from werkzeug.exceptions import HTTPException

from app.utils.response import error_response

_HTTP_CODE_MAP: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "The request is invalid or malformed."),
    401: ("UNAUTHORIZED", "Authentication is required or invalid."),
    403: ("FORBIDDEN", "You do not have permission to perform this action."),
    404: ("NOT_FOUND", "The requested resource was not found."),
    405: ("METHOD_NOT_ALLOWED", "The HTTP method is not allowed for this endpoint."),
    409: ("CONFLICT", "The request conflicts with existing data."),
    422: ("UNPROCESSABLE_ENTITY", "The request failed validation or business rules."),
    500: ("INTERNAL_SERVER_ERROR", "An unexpected internal server error occurred."),
}


class AppError(Exception):
    """Structured application error mapped directly to the JSON error envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def register_error_handlers(app: Flask) -> None:
    """Register JSON-only error handlers for 400, 401, 403, 404, 405, 409, 422, 500."""

    @app.errorhandler(AppError)
    def handle_app_error(err: AppError) -> tuple[Response, int]:
        return error_response(err.code, err.message, err.status_code, err.details)

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException) -> tuple[Response, int]:
        status = err.code or 500
        default_code, default_msg = _HTTP_CODE_MAP.get(
            status, ("HTTP_ERROR", "An HTTP error occurred.")
        )
        # Never expose internal details on 500 responses.
        message = default_msg if status >= 500 else (err.description or default_msg)
        return error_response(default_code, message, status)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(err: Exception) -> tuple[Response, int]:
        app.logger.exception("Unhandled server exception: %s", err)
        code, message = _HTTP_CODE_MAP[500]
        return error_response(code, message, 500)
