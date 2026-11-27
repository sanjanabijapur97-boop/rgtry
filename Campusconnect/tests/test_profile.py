"""Tests for Feature 2: student profile view and update."""


def _register_and_login(client, name="Aarav Sharma", email="aarav@campus.edu", password="Password123"):
    reg = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert reg.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return login.get_json()["data"]["access_token"]


def test_get_initial_profile_success(client):
    token = _register_and_login(client)
    resp = client.get("/api/profile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    profile = resp.get_json()["data"]["profile"]
    assert profile["email"] == "aarav@campus.edu"
    assert profile["name"] == "Aarav Sharma"
    assert profile["branch"] is None
    assert profile["year"] is None
    assert profile["cgpa"] is None
    assert profile["skills"] == []
    assert profile["phone"] is None


def test_put_and_patch_profile_success(client):
    token = _register_and_login(client)

    put_resp = client.put(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Aarav S.",
            "branch": "CSE",
            "year": 3,
            "cgpa": 8.75,
            "skills": ["Python", "Flask", "python", "SQLite"],
            "phone": "+91-9876543210",
        },
    )
    assert put_resp.status_code == 200
    profile = put_resp.get_json()["data"]["profile"]
    assert profile["name"] == "Aarav S."
    assert profile["branch"] == "CSE"
    assert profile["year"] == 3
    assert profile["cgpa"] == 8.75
    assert profile["skills"] == ["Python", "Flask", "SQLite"]
    assert profile["phone"] == "+91-9876543210"

    # Partial PATCH preserves unspecified fields
    patch_resp = client.patch(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"cgpa": 9.1, "skills": ["Python", "React"]},
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.get_json()["data"]["profile"]
    assert patched["name"] == "Aarav S."
    assert patched["branch"] == "CSE"
    assert patched["year"] == 3
    assert patched["cgpa"] == 9.1
    assert patched["skills"] == ["Python", "React"]
    assert patched["phone"] == "+91-9876543210"

    # Subsequent GET confirms persistence
    get_resp = client.get("/api/profile", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 200
    assert get_resp.get_json()["data"]["profile"]["cgpa"] == 9.1


def test_profile_isolated_per_student(client):
    token_a = _register_and_login(client, name="Student A", email="a@campus.edu")
    token_b = _register_and_login(client, name="Student B", email="b@campus.edu")

    client.patch(
        "/api/profile",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"branch": "ECE", "year": 2, "cgpa": 7.5},
    )

    resp_a = client.get("/api/profile", headers={"Authorization": f"Bearer {token_a}"})
    profile_a = resp_a.get_json()["data"]["profile"]
    assert profile_a["name"] == "Student A"
    assert profile_a["branch"] is None
    assert profile_a["cgpa"] is None


def test_profile_auth_and_role_restrictions(app, client):
    unauth = client.get("/api/profile")
    assert unauth.status_code == 401

    runner = app.test_cli_runner()
    runner.invoke(
        args=["create-admin", "--email", "admin@campus.edu", "--password", "AdminPass123"]
    )
    admin_login = client.post(
        "/api/auth/login",
        json={"email": "admin@campus.edu", "password": "AdminPass123"},
    )
    admin_token = admin_login.get_json()["data"]["access_token"]

    admin_get = client.get(
        "/api/profile", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_get.status_code == 403
    assert admin_get.get_json()["error"]["code"] == "FORBIDDEN"

    admin_patch = client.patch(
        "/api/profile",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Nope"},
    )
    assert admin_patch.status_code == 403


def test_profile_validation_errors(client):
    token = _register_and_login(client)

    bad_json = client.patch(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"},
        data="{invalid",
        content_type="application/json",
    )
    assert bad_json.status_code == 400

    empty_patch = client.patch(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert empty_patch.status_code == 422

    invalid = client.put(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "X",
            "branch": "",
            "year": True,
            "cgpa": 11.5,
            "skills": ["", 123],
            "phone": "abc",
        },
    )
    assert invalid.status_code == 422
    fields = invalid.get_json()["error"]["details"]["fields"]
    assert set(fields.keys()) == {"name", "branch", "year", "cgpa", "skills", "phone"}
