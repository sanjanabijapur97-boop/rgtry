"""Tests for Feature 5: opportunity eligibility checks."""


def _setup_admin_and_student(app, client):
    runner = app.test_cli_runner()
    runner.invoke(
        args=["create-admin", "--email", "admin@campus.edu", "--password", "AdminPass123"]
    )
    admin_token = client.post(
        "/api/auth/login",
        json={"email": "admin@campus.edu", "password": "AdminPass123"},
    ).get_json()["data"]["access_token"]

    client.post(
        "/api/auth/register",
        json={
            "name": "Aarav Sharma",
            "email": "aarav@campus.edu",
            "password": "Password123",
        },
    )
    student_token = client.post(
        "/api/auth/login",
        json={"email": "aarav@campus.edu", "password": "Password123"},
    ).get_json()["data"]["access_token"]

    return admin_token, student_token


def _create_opp(client, admin_token, **overrides):
    payload = {
        "title": "Backend Hackathon",
        "organization": "Tech Club",
        "description": "Build scalable REST APIs in 24 hours.",
        "category": "hackathon",
        "eligible_branches": ["CSE", "IT"],
        "eligible_years": [2, 3, 4],
        "min_cgpa": 7.5,
        "required_skills": ["Python", "Flask"],
        "deadline": "2026-12-20",
    }
    payload.update(overrides)
    resp = client.post(
        "/api/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert resp.status_code == 201
    return resp.get_json()["data"]["opportunity"]["id"]


def test_eligible_student_passes_case_insensitively(app, client):
    admin_token, student_token = _setup_admin_and_student(app, client)
    opp_id = _create_opp(client, admin_token)

    client.patch(
        "/api/profile",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "branch": "cse",
            "year": 3,
            "cgpa": 8.4,
            "skills": ["python", "flask", "SQLite"],
        },
    )

    resp = client.get(
        f"/api/opportunities/{opp_id}/eligibility",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data == {
        "opportunity_id": opp_id,
        "eligible": True,
        "reasons": [],
        "missing_fields": [],
    }


def test_ineligible_student_receives_all_failed_rule_reasons(app, client):
    admin_token, student_token = _setup_admin_and_student(app, client)
    opp_id = _create_opp(client, admin_token)

    client.patch(
        "/api/profile",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "branch": "MECH",
            "year": 1,
            "cgpa": 6.8,
            "skills": ["Python"],
        },
    )

    resp = client.get(
        f"/api/opportunities/{opp_id}/eligibility",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["eligible"] is False
    assert data["missing_fields"] == []
    assert len(data["reasons"]) == 4
    joined = " | ".join(data["reasons"])
    assert "MECH" in joined
    assert "year 1" in joined.lower()
    assert "6.8" in joined
    assert "Flask" in joined


def test_missing_profile_fields_reported_and_fail_required_rules(app, client):
    admin_token, student_token = _setup_admin_and_student(app, client)
    restricted_id = _create_opp(client, admin_token)
    open_id = _create_opp(
        client,
        admin_token,
        title="Open Campus Workshop",
        eligible_branches=[],
        eligible_years=[],
        min_cgpa=None,
        required_skills=[],
    )

    # Fresh profile has branch, year, cgpa, skills all missing
    resp_restricted = client.get(
        f"/api/opportunities/{restricted_id}/eligibility",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp_restricted.status_code == 200
    data = resp_restricted.get_json()["data"]
    assert data["eligible"] is False
    assert data["missing_fields"] == ["branch", "year", "cgpa", "skills"]
    assert len(data["reasons"]) == 4

    # Open opportunity is eligible, yet still reports missing profile fields
    resp_open = client.get(
        f"/api/opportunities/{open_id}/eligibility",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp_open.status_code == 200
    open_data = resp_open.get_json()["data"]
    assert open_data["eligible"] is True
    assert open_data["reasons"] == []
    assert open_data["missing_fields"] == ["branch", "year", "cgpa", "skills"]


def test_eligibility_auth_and_not_found(app, client):
    admin_token, student_token = _setup_admin_and_student(app, client)
    opp_id = _create_opp(client, admin_token)

    unauth = client.get(f"/api/opportunities/{opp_id}/eligibility")
    assert unauth.status_code == 401

    admin_forbidden = client.get(
        f"/api/opportunities/{opp_id}/eligibility",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_forbidden.status_code == 403

    missing_opp = client.get(
        "/api/opportunities/999/eligibility",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert missing_opp.status_code == 404
    assert missing_opp.get_json()["error"]["code"] == "OPPORTUNITY_NOT_FOUND"
