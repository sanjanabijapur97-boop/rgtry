"""Tests for Feature 6: student applications, withdrawal, and admin review."""


def _setup_admin_and_students(app, client):
    runner = app.test_cli_runner()
    res = runner.invoke(
        args=["create-admin", "--email", "admin@campus.edu", "--password", "AdminPass123"]
    )
    assert res.exit_code == 0
    admin_token = client.post(
        "/api/auth/login",
        json={"email": "admin@campus.edu", "password": "AdminPass123"},
    ).get_json()["data"]["access_token"]

    tokens = []
    for idx, (name, email) in enumerate(
        [("Aarav Sharma", "aarav@campus.edu"), ("Diya Nair", "diya@campus.edu")], start=1
    ):
        client.post(
            "/api/auth/register",
            json={"name": name, "email": email, "password": "Password123"},
        )
        tok = client.post(
            "/api/auth/login",
            json={"email": email, "password": "Password123"},
        ).get_json()["data"]["access_token"]
        if idx == 1:
            client.patch(
                "/api/profile",
                headers={"Authorization": f"Bearer {tok}"},
                json={
                    "branch": "CSE",
                    "year": 3,
                    "cgpa": 8.6,
                    "skills": ["Python", "Flask"],
                },
            )
        tokens.append(tok)

    return admin_token, tokens[0], tokens[1]


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
        "deadline": "2099-12-20",
        "is_active": True,
    }
    payload.update(overrides)
    resp = client.post(
        "/api/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert resp.status_code == 201
    return resp.get_json()["data"]["opportunity"]["id"]


def test_student_apply_list_detail_withdraw_and_reapply(app, client):
    admin_token, student_token, other_token = _setup_admin_and_students(app, client)
    opp_id = _create_opp(client, admin_token)

    # Apply with note
    apply_resp = client.post(
        f"/api/opportunities/{opp_id}/apply",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"note": "Excited to build Flask APIs!"},
    )
    assert apply_resp.status_code == 201
    app_data = apply_resp.get_json()["data"]["application"]
    app_id = app_data["id"]
    assert app_data["status"] == "submitted"
    assert app_data["note"] == "Excited to build Flask APIs!"
    assert app_data["opportunity"]["id"] == opp_id

    # Duplicate active application returns 409
    dup_resp = client.post(
        f"/api/opportunities/{opp_id}/apply",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert dup_resp.status_code == 409
    assert dup_resp.get_json()["error"]["code"] == "ALREADY_APPLIED"

    # Student list & detail
    list_resp = client.get(
        "/api/applications?status=submitted",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert list_resp.status_code == 200
    assert list_resp.get_json()["data"]["pagination"]["total"] == 1

    # Other student cannot inspect or withdraw
    other_get = client.get(
        f"/api/applications/{app_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_get.status_code == 403

    other_withdraw = client.post(
        f"/api/applications/{app_id}/withdraw",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_withdraw.status_code == 403

    # Owner withdraws
    withdraw_resp = client.post(
        f"/api/applications/{app_id}/withdraw",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert withdraw_resp.status_code == 200
    assert withdraw_resp.get_json()["data"]["application"]["status"] == "withdrawn"

    # Second withdraw returns 409
    again = client.post(
        f"/api/applications/{app_id}/withdraw",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert again.status_code == 409
    assert again.get_json()["error"]["code"] == "ALREADY_WITHDRAWN"

    # Re-apply without body reactivates the application
    reapply = client.post(
        f"/api/opportunities/{opp_id}/apply",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert reapply.status_code == 201
    assert reapply.get_json()["data"]["application"]["id"] == app_id
    assert reapply.get_json()["data"]["application"]["status"] == "submitted"
    assert reapply.get_json()["data"]["application"]["note"] is None


def test_apply_blocks_ineligible_inactive_and_expired_opportunities(app, client):
    admin_token, eligible_token, incomplete_token = _setup_admin_and_students(
        app, client
    )
    open_opp = _create_opp(client, admin_token)
    inactive_opp = _create_opp(client, admin_token, title="Closed Opp", is_active=False)
    expired_opp = _create_opp(
        client, admin_token, title="Expired Opp", deadline="2020-01-01"
    )

    # Incomplete student profile fails eligibility
    ineligible = client.post(
        f"/api/opportunities/{open_opp}/apply",
        headers={"Authorization": f"Bearer {incomplete_token}"},
    )
    assert ineligible.status_code == 422
    err = ineligible.get_json()["error"]
    assert err["code"] == "NOT_ELIGIBLE"
    assert len(err["details"]["reasons"]) == 4

    inactive_resp = client.post(
        f"/api/opportunities/{inactive_opp}/apply",
        headers={"Authorization": f"Bearer {eligible_token}"},
    )
    assert inactive_resp.status_code == 422
    assert inactive_resp.get_json()["error"]["code"] == "OPPORTUNITY_INACTIVE"

    expired_resp = client.post(
        f"/api/opportunities/{expired_opp}/apply",
        headers={"Authorization": f"Bearer {eligible_token}"},
    )
    assert expired_resp.status_code == 422
    assert expired_resp.get_json()["error"]["code"] == "DEADLINE_PASSED"


def test_admin_review_applicants_and_status_updates(app, client):
    admin_token, student_token, _ = _setup_admin_and_students(app, client)
    opp_id = _create_opp(client, admin_token)

    created = client.post(
        f"/api/opportunities/{opp_id}/apply",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"note": "Ready to participate"},
    )
    app_id = created.get_json()["data"]["application"]["id"]

    # Student cannot list all applicants or update status
    assert (
        client.get(
            f"/api/opportunities/{opp_id}/applications",
            headers={"Authorization": f"Bearer {student_token}"},
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/applications/{app_id}/status",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"status": "shortlisted"},
        ).status_code
        == 403
    )

    # Admin lists applicants with profile info
    apps_resp = client.get(
        f"/api/opportunities/{opp_id}/applications",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert apps_resp.status_code == 200
    items = apps_resp.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["applicant"]["email"] == "aarav@campus.edu"
    assert items[0]["applicant"]["cgpa"] == 8.6

    # Admin shortlists then accepts
    shortlist = client.patch(
        f"/api/applications/{app_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "shortlisted", "admin_remarks": "Great skills"},
    )
    assert shortlist.status_code == 200
    assert shortlist.get_json()["data"]["application"]["status"] == "shortlisted"
    assert (
        shortlist.get_json()["data"]["application"]["admin_remarks"] == "Great skills"
    )

    accept = client.patch(
        f"/api/applications/{app_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "accepted"},
    )
    assert accept.status_code == 200
    assert accept.get_json()["data"]["application"]["status"] == "accepted"

    # Accepted application cannot be withdrawn
    withdraw_accepted = client.post(
        f"/api/applications/{app_id}/withdraw",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert withdraw_accepted.status_code == 422
    assert withdraw_accepted.get_json()["error"]["code"] == "CANNOT_WITHDRAW"
