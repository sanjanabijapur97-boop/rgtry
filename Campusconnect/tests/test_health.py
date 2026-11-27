"""Tests for app factory, config, CORS, error handlers, and GET /api/health."""

import pytest
from flask import abort

from app import create_app
from app.errors import AppError


def test_health_check_success(client):
    response = client.get("/api/health")
    assert response.status_code == 200

    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "connected"
    assert body["data"]["timestamp"].endswith("Z")


def test_refuses_to_start_without_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(test_config={"TESTING": True}, load_env=False)


def test_refuses_to_start_with_blank_secret_key():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(test_config={"TESTING": True, "SECRET_KEY": "   "}, load_env=False)


def test_refuses_wildcard_cors_origin():
    with pytest.raises(RuntimeError, match="Wildcard"):
        create_app(
            test_config={
                "TESTING": True,
                "SECRET_KEY": "valid-test-secret",
                "FRONTEND_ORIGINS": "*",
            },
            load_env=False,
        )


def test_debug_mode_off_by_default(app):
    assert app.config["FLASK_DEBUG"] is False
    assert app.debug is False


def test_cors_allows_configured_origin_and_preflight(client):
    origin = "http://192.168.1.20:5173"
    preflight = client.options(
        "/api/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert preflight.status_code in (200, 204)
    assert preflight.headers.get("Access-Control-Allow-Origin") == origin
    allow_headers = preflight.headers.get("Access-Control-Allow-Headers", "")
    assert "Authorization" in allow_headers
    assert "Content-Type" in allow_headers

    get_resp = client.get("/api/health", headers={"Origin": origin})
    assert get_resp.status_code == 200
    assert get_resp.headers.get("Access-Control-Allow-Origin") == origin


def test_cors_blocks_unconfigured_origin(client):
    resp = client.get("/api/health", headers={"Origin": "http://evil.example.com"})
    assert resp.status_code == 200
    assert resp.headers.get("Access-Control-Allow-Origin") is None


def test_404_and_405_json_error_responses(client):
    resp_404 = client.get("/api/does-not-exist")
    assert resp_404.status_code == 404
    body_404 = resp_404.get_json()
    assert body_404["success"] is False
    assert body_404["error"]["code"] == "NOT_FOUND"
    assert isinstance(body_404["error"]["details"], dict)

    resp_405 = client.post("/api/health")
    assert resp_405.status_code == 405
    body_405 = resp_405.get_json()
    assert body_405["success"] is False
    assert body_405["error"]["code"] == "METHOD_NOT_ALLOWED"


@pytest.mark.parametrize(
    "status_code,expected_code",
    [
        (400, "BAD_REQUEST"),
        (401, "UNAUTHORIZED"),
        (403, "FORBIDDEN"),
        (409, "CONFLICT"),
        (422, "UNPROCESSABLE_ENTITY"),
    ],
)
def test_standard_http_error_handlers(tmp_path, status_code, expected_code):
    test_app = create_app(
        test_config={
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'err.db').as_posix()}",
        },
        load_env=False,
    )

    @test_app.get("/api/test-abort")
    def trigger_abort():
        abort(status_code)

    resp = test_app.test_client().get("/api/test-abort")
    assert resp.status_code == status_code
    body = resp.get_json()
    assert body["success"] is False
    assert body["error"]["code"] == expected_code
    assert isinstance(body["error"]["details"], dict)


def test_500_error_hides_stack_trace(tmp_path):
    test_app = create_app(
        test_config={
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'err500.db').as_posix()}",
        },
        load_env=False,
    )

    @test_app.get("/api/test-crash")
    def trigger_crash():
        raise RuntimeError("sensitive internal detail")

    resp = test_app.test_client().get("/api/test-crash")
    assert resp.status_code == 500
    raw = resp.get_data(as_text=True)
    assert "Traceback" not in raw
    assert "sensitive internal detail" not in raw

    body = resp.get_json()
    assert body == {
        "success": False,
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected internal server error occurred.",
            "details": {},
        },
    }


def test_app_error_response(tmp_path):
    test_app = create_app(
        test_config={
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'apperr.db').as_posix()}",
        },
        load_env=False,
    )

    @test_app.get("/api/test-app-error")
    def trigger_app_error():
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid input.",
            status_code=422,
            details={"field": "email"},
        )

    resp = test_app.test_client().get("/api/test-app-error")
    assert resp.status_code == 422
    assert resp.get_json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Invalid input.",
            "details": {"field": "email"},
        },
    }


def test_init_db_cli_command(tmp_path):
    db_path = tmp_path / "cli_init.db"
    test_app = create_app(
        test_config={
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_URL": f"sqlite:///{db_path.as_posix()}",
        },
        load_env=False,
    )
    runner = test_app.test_cli_runner()
    result = runner.invoke(args=["init-db"])
    assert result.exit_code == 0
    assert "Initialized the database." in result.output
    assert db_path.exists()
