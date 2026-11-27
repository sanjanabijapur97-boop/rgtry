"""Tests for Feature 7: student opportunity bookmarks."""


def _setup_users(app, client):
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
        json={"name": "Aarav Sharma", "email": "aarav@campus.edu", "password": "Password123"},
    )
    student_token = client.post(
        "/api/auth/login",
        json={"email": "aarav@campus.edu", "password": "Password123"},
    ).get_json()["data"]["access_token"]

    return admin_token, student_token


def _create_opp(client, admin_token, title="Campus Hackathon", is_active=True):
    resp = client.post(
        "/api/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": title,
            "organization": "Tech Club",
            "description": "Build innovative campus projects together.",
            "category": "hackathon",
            "deadline": "2099-12-20",
            "is_active": is_active,
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["data"]["opportunity"]["id"]


def test_bookmark_add_list_filter_and_delete(app, client):
    admin_token, student_token = _setup_users(app, client)
    opp1 = _create_opp(client, admin_token, title="Active Opp", is_active=True)
    opp2 = _create_opp(client, admin_token, title="Inactive Opp", is_active=False)

    # Create bookmark -> 201
    add1 = client.post(
        f"/api/opportunities/{opp1}/bookmark",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert add1.status_code == 201
    assert add1.get_json()["data"]["already_bookmarked"] is False

    # Re-bookmarking is idempotent -> 200
    add1_again = client.post(
        f"/api/opportunities/{opp1}/bookmark",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert add1_again.status_code == 200
    assert add1_again.get_json()["data"]["already_bookmarked"] is True

    add2 = client.post(
        f"/api/opportunities/{opp2}/bookmark",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert add2.status_code == 201

    # List all bookmarks
    all_bm = client.get(
        "/api/bookmarks", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert all_bm.status_code == 200
    assert all_bm.get_json()["data"]["pagination"]["total"] == 2

    # Filter active only
    active_bm = client.get(
        "/api/bookmarks?active=true",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert active_bm.status_code == 200
    assert active_bm.get_json()["data"]["pagination"]["total"] == 1
    assert active_bm.get_json()["data"]["items"][0]["opportunity"]["id"] == opp1

    # Delete bookmark
    del_resp = client.delete(
        f"/api/opportunities/{opp1}/bookmark",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert del_resp.status_code == 200
    assert del_resp.get_json()["data"] == {"deleted": True, "opportunity_id": opp1}

    # Deleting missing bookmark returns 404
    del_missing = client.delete(
        f"/api/opportunities/{opp1}/bookmark",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert del_missing.status_code == 404
    assert del_missing.get_json()["error"]["code"] == "BOOKMARK_NOT_FOUND"


def test_bookmark_permissions_and_missing_opportunity(app, client):
    admin_token, _ = _setup_users(app, client)
    opp_id = _create_opp(client, admin_token)

    assert client.get("/api/bookmarks").status_code == 401
    assert (
        client.post(
            f"/api/opportunities/{opp_id}/bookmark",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).status_code
        == 403
    )

    # Register student to check 404 on non-existent opportunity
    client.post(
        "/api/auth/register",
        json={"name": "Student", "email": "s@campus.edu", "password": "Password123"},
    )
    tok = client.post(
        "/api/auth/login",
        json={"email": "s@campus.edu", "password": "Password123"},
    ).get_json()["data"]["access_token"]

    missing = client.post(
        "/api/opportunities/999/bookmark",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert missing.status_code == 404
    assert missing.get_json()["error"]["code"] == "OPPORTUNITY_NOT_FOUND"
