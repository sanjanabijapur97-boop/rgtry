"""Tests for eligible opportunities feed, password change, admin stats, and seed-db CLI."""


def test_eligible_opportunities_feed(app, client):
    runner = app.test_cli_runner()
    runner.invoke(args=["seed-db"])

    student_token = client.post(
        "/api/auth/login",
        json={"email": "aarav@campus.edu", "password": "Password123"},
    ).get_json()["data"]["access_token"]

    # Seeded student: CSE, year 3, cgpa 8.75, skills [Python, Flask, SQL] -> eligible for all 4
    eligible_only = client.get(
        "/api/opportunities/eligible",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert eligible_only.status_code == 200
    data = eligible_only.get_json()["data"]
    assert data["pagination"]["total"] == 4
    assert all(item["eligibility"]["eligible"] is True for item in data["items"])

    # Lower CGPA to 7.2 -> only hackathon (7.0) and workshop (None) remain eligible
    client.patch(
        "/api/profile",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"cgpa": 7.2},
    )
    filtered = client.get(
        "/api/opportunities/eligible",
        headers={"Authorization": f"Bearer {student_token}"},
    ).get_json()["data"]
    assert filtered["pagination"]["total"] == 2

    # eligible_only=false returns all 4 with eligibility breakdown
    all_evaluated = client.get(
        "/api/opportunities/eligible?eligible_only=false",
        headers={"Authorization": f"Bearer {student_token}"},
    ).get_json()["data"]
    assert all_evaluated["pagination"]["total"] == 4
    ineligible_count = sum(
        1 for item in all_evaluated["items"] if not item["eligibility"]["eligible"]
    )
    assert ineligible_count == 2


def test_change_password_success_and_failures(client):
    client.post(
        "/api/auth/register",
        json={"name": "Aarav", "email": "aarav@campus.edu", "password": "Password123"},
    )
    token = client.post(
        "/api/auth/login",
        json={"email": "aarav@campus.edu", "password": "Password123"},
    ).get_json()["data"]["access_token"]

    wrong_current = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "WrongPassword", "new_password": "NewPassword456"},
    )
    assert wrong_current.status_code == 401
    assert wrong_current.get_json()["error"]["code"] == "INVALID_CREDENTIALS"

    same_password = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "Password123", "new_password": "Password123"},
    )
    assert same_password.status_code == 422

    ok_resp = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "Password123", "new_password": "NewPassword456"},
    )
    assert ok_resp.status_code == 200
    assert ok_resp.get_json()["data"] == {"password_changed": True}

    # Old password fails, new password succeeds
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "aarav@campus.edu", "password": "Password123"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "aarav@campus.edu", "password": "NewPassword456"},
        ).status_code
        == 200
    )


def test_admin_stats_and_seed_db_idempotency(app, client):
    runner = app.test_cli_runner()
    res1 = runner.invoke(args=["seed-db"])
    assert res1.exit_code == 0
    assert "opportunities_created=4" in res1.output

    # Running seed-db a second time creates 0 duplicates
    res2 = runner.invoke(args=["seed-db"])
    assert res2.exit_code == 0
    assert "opportunities_created=0" in res2.output

    admin_token = client.post(
        "/api/auth/login",
        json={"email": "admin@campusconnect.local", "password": "AdminPass123"},
    ).get_json()["data"]["access_token"]
    student_token = client.post(
        "/api/auth/login",
        json={"email": "aarav@campus.edu", "password": "Password123"},
    ).get_json()["data"]["access_token"]

    # Create 1 application and 1 bookmark
    opps = client.get("/api/opportunities").get_json()["data"]["items"]
    opp_id = opps[0]["id"]
    client.post(
        f"/api/opportunities/{opp_id}/apply",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    client.post(
        f"/api/opportunities/{opp_id}/bookmark",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # Student cannot access admin stats
    assert (
        client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {student_token}"},
        ).status_code
        == 403
    )

    stats_resp = client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert stats_resp.status_code == 200
    stats = stats_resp.get_json()["data"]["stats"]
    assert stats["users"] == {"total": 2, "students": 1, "admins": 1}
    assert stats["opportunities"]["total"] == 4
    assert stats["opportunities"]["active"] == 4
    assert stats["applications"]["total"] == 1
    assert stats["applications"]["by_status"]["submitted"] == 1
    assert stats["bookmarks"]["total"] == 1
