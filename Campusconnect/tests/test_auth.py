"""Tests for Feature 1: registration, login, current user, and create-admin CLI."""

from datetime import datetime, timedelta, timezone
import jwt

from app.db import get_db


def _register_student(client, name="Aarav Sharma", email="aarav@campus.edu", password="Password123"):
    return client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )


def test_register_student_success_and_creates_profile(client, app):
    resp = _register_student(client, email="  Aarav@Campus.EDU ")
    assert resp.status_code == 201

    body = resp.get_json()
    assert body["success"] is True
    user = body["data"]["user"]
    assert user["email"] == "aarav@campus.edu"
    assert user["name"] == "Aarav Sharma"
    assert user["role"] == "student"
    assert user["created_at"].endswith("Z")
    assert "password_hash" not in user

    with app.app_context():
        profile = get_db().execute(
            "SELECT user_id, name FROM student_profiles WHERE user_id = ?",
            (user["id"],),
        ).fetchone()
        assert profile is not None
        assert profile["name"] == "Aarav Sharma"


def test_public_registration_always_creates_student_even_if_role_admin_sent(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "name": "Sneaky User",
            "email": "sneaky@campus.edu",
            "password": "Password123",
            "role": "admin",
        },
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["user"]["role"] == "student"


def test_register_duplicate_email_returns_409(client):
    first = _register_student(client, email="dup@campus.edu")
    assert first.status_code == 201

    second = _register_student(client, email="DUP@campus.edu")
    assert second.status_code == 409
    body = second.get_json()
    assert body["success"] is False
    assert body["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_register_validation_and_malformed_json(client):
    bad_json = client.post(
        "/api/auth/register",
        data="{not valid json",
        content_type="application/json",
    )
    assert bad_json.status_code == 400
    assert bad_json.get_json()["error"]["code"] == "INVALID_JSON"

    invalid = client.post(
        "/api/auth/register",
        json={"name": "A", "email": "not-an-email", "password": "short"},
    )
    assert invalid.status_code == 422
    err = invalid.get_json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert set(err["details"]["fields"].keys()) == {"name", "email", "password"}


def test_login_and_me_success(client):
    reg = _register_student(client)
    assert reg.status_code == 201

    login_resp = client.post(
        "/api/auth/login",
        json={"email": "AARAV@CAMPUS.EDU", "password": "Password123"},
    )
    assert login_resp.status_code == 200
    data = login_resp.get_json()["data"]
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 86400
    assert data["expires_at"].endswith("Z")
    assert data["user"]["role"] == "student"

    token = data["access_token"]
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_user = me_resp.get_json()["data"]["user"]
    assert me_user["email"] == "aarav@campus.edu"
    assert me_user["name"] == "Aarav Sharma"
    assert me_user["role"] == "student"


def test_login_failures(client):
    _register_student(client)

    wrong_pw = client.post(
        "/api/auth/login",
        json={"email": "aarav@campus.edu", "password": "WrongPassword"},
    )
    assert wrong_pw.status_code == 401
    assert wrong_pw.get_json()["error"]["code"] == "INVALID_CREDENTIALS"

    unknown = client.post(
        "/api/auth/login",
        json={"email": "nobody@campus.edu", "password": "Password123"},
    )
    assert unknown.status_code == 401
    assert unknown.get_json()["error"]["code"] == "INVALID_CREDENTIALS"

    bad_fields = client.post("/api/auth/login", json={"email": "bad", "password": ""})
    assert bad_fields.status_code == 422
    assert bad_fields.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_me_auth_errors(client, app):
    missing = client.get("/api/auth/me")
    assert missing.status_code == 401
    assert missing.get_json()["error"]["code"] == "UNAUTHORIZED"

    bad_scheme = client.get("/api/auth/me", headers={"Authorization": "Basic abc"})
    assert bad_scheme.status_code == 401
    assert bad_scheme.get_json()["error"]["code"] == "UNAUTHORIZED"

    invalid_token = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert invalid_token.status_code == 401
    assert invalid_token.get_json()["error"]["code"] == "INVALID_TOKEN"

    reg = _register_student(client).get_json()["data"]["user"]
    expired_payload = {
        "sub": str(reg["id"]),
        "role": "student",
        "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
        "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
    }
    expired_jwt = jwt.encode(
        expired_payload, app.config["SECRET_KEY"], algorithm="HS256"
    )
    expired_resp = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {expired_jwt}"}
    )
    assert expired_resp.status_code == 401
    assert expired_resp.get_json()["error"]["code"] == "TOKEN_EXPIRED"


def test_create_admin_cli_and_login(app, client):
    runner = app.test_cli_runner()
    res = runner.invoke(
        args=["create-admin", "--email", "admin@campus.edu", "--password", "AdminPass123"]
    )
    assert res.exit_code == 0
    assert "Admin user created: admin@campus.edu" in res.output

    # Duplicate admin email should fail cleanly
    dup = runner.invoke(
        args=["create-admin", "--email", "admin@campus.edu", "--password", "AdminPass123"]
    )
    assert dup.exit_code != 0
    assert "already exists" in dup.output

    # Admin can log in and inspect /api/auth/me
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "admin@campus.edu", "password": "AdminPass123"},
    )
    assert login_resp.status_code == 200
    data = login_resp.get_json()["data"]
    assert data["user"]["role"] == "admin"

    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.get_json()["data"]["user"]["role"] == "admin"
    assert me_resp.get_json()["data"]["user"]["email"] == "admin@campus.edu"
