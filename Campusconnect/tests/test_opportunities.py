"""Tests for Feature 3: opportunities CRUD, pagination, deadlines, and permissions."""


def _create_admin_and_login(app, client, email="admin@campus.edu", password="AdminPass123"):
    runner = app.test_cli_runner()
    res = runner.invoke(
        args=["create-admin", "--email", email, "--password", password]
    )
    assert res.exit_code == 0
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    return login.get_json()["data"]["access_token"]


def _create_student_and_login(client, email="student@campus.edu", password="Password123"):
    client.post(
        "/api/auth/register",
        json={"name": "Student One", "email": email, "password": password},
    )
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    return login.get_json()["data"]["access_token"]


def _sample_opportunity(**overrides):
    payload = {
        "title": "Smart Campus Hackathon 2026",
        "organization": "Tech Club",
        "description": "Build innovative solutions for campus life in 36 hours.",
        "category": "Hackathon",
        "eligible_branches": ["CSE", "IT", "ECE"],
        "eligible_years": [2, 3, 4],
        "min_cgpa": 7.5,
        "required_skills": ["Python", "Flask"],
        "deadline": "2026-12-20",
        "link": "https://campusconnect.example.com/hackathon",
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def test_admin_create_and_public_list_detail(app, client):
    admin_token = _create_admin_and_login(app, client)

    # Create with date-only deadline -> 2026-12-20 23:59 Asia/Kolkata == 2026-12-20T18:29:00Z
    create_resp = client.post(
        "/api/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_sample_opportunity(),
    )
    assert create_resp.status_code == 201
    opp = create_resp.get_json()["data"]["opportunity"]
    assert opp["title"] == "Smart Campus Hackathon 2026"
    assert opp["category"] == "hackathon"
    assert opp["deadline"] == "2026-12-20T18:29:00Z"
    assert opp["is_active"] is True

    # Public list (no auth required)
    list_resp = client.get("/api/opportunities")
    assert list_resp.status_code == 200
    data = list_resp.get_json()["data"]
    assert len(data["items"]) == 1
    assert data["pagination"]["total"] == 1

    # Public detail
    detail_resp = client.get(f"/api/opportunities/{opp['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.get_json()["data"]["opportunity"]["id"] == opp["id"]


def test_deadline_with_explicit_offset_converted_to_utc(app, client):
    admin_token = _create_admin_and_login(app, client)
    resp = client.post(
        "/api/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_sample_opportunity(deadline="2026-12-20T18:00:00+05:30"),
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["opportunity"]["deadline"] == "2026-12-20T12:30:00Z"


def test_opportunities_pagination(app, client):
    admin_token = _create_admin_and_login(app, client)
    for idx in range(1, 6):
        resp = client.post(
            "/api/opportunities",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=_sample_opportunity(title=f"Opportunity {idx}"),
        )
        assert resp.status_code == 201

    page_1 = client.get("/api/opportunities?page=1&per_page=2").get_json()["data"]
    assert len(page_1["items"]) == 2
    assert page_1["pagination"] == {
        "page": 1,
        "per_page": 2,
        "total": 5,
        "pages": 3,
        "has_next": True,
        "has_prev": False,
    }

    page_3 = client.get("/api/opportunities?page=3&per_page=2").get_json()["data"]
    assert len(page_3["items"]) == 1
    assert page_3["pagination"]["has_next"] is False
    assert page_3["pagination"]["has_prev"] is True

    bad_page = client.get("/api/opportunities?page=0")
    assert bad_page.status_code == 422


def test_admin_update_and_delete_opportunity(app, client):
    admin_token = _create_admin_and_login(app, client)
    created = client.post(
        "/api/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_sample_opportunity(),
    ).get_json()["data"]["opportunity"]
    opp_id = created["id"]

    # Partial PATCH
    patch_resp = client.patch(
        f"/api/opportunities/{opp_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"min_cgpa": 8.0, "is_active": False},
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.get_json()["data"]["opportunity"]
    assert patched["min_cgpa"] == 8.0
    assert patched["is_active"] is False
    assert patched["title"] == "Smart Campus Hackathon 2026"

    # Full PUT
    put_resp = client.put(
        f"/api/opportunities/{opp_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_sample_opportunity(title="Updated Hackathon", min_cgpa=None, link=None),
    )
    assert put_resp.status_code == 200
    replaced = put_resp.get_json()["data"]["opportunity"]
    assert replaced["title"] == "Updated Hackathon"
    assert replaced["min_cgpa"] is None
    assert replaced["link"] is None

    # DELETE
    del_resp = client.delete(
        f"/api/opportunities/{opp_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_resp.status_code == 200
    assert del_resp.get_json()["data"] == {"deleted": True, "id": opp_id}

    # Detail after delete returns 404
    missing = client.get(f"/api/opportunities/{opp_id}")
    assert missing.status_code == 404
    assert missing.get_json()["error"]["code"] == "OPPORTUNITY_NOT_FOUND"


def test_opportunity_write_permissions_and_not_found(app, client):
    admin_token = _create_admin_and_login(app, client)
    student_token = _create_student_and_login(client)

    unauth = client.post("/api/opportunities", json=_sample_opportunity())
    assert unauth.status_code == 401

    forbidden_create = client.post(
        "/api/opportunities",
        headers={"Authorization": f"Bearer {student_token}"},
        json=_sample_opportunity(),
    )
    assert forbidden_create.status_code == 403

    forbidden_delete = client.delete(
        "/api/opportunities/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert forbidden_delete.status_code == 403

    missing_patch = client.patch(
        "/api/opportunities/999",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Missing Opp"},
    )
    assert missing_patch.status_code == 404

    missing_delete = client.delete(
        "/api/opportunities/999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert missing_delete.status_code == 404


def test_opportunity_validation_errors(app, client):
    admin_token = _create_admin_and_login(app, client)

    bad_json = client.post(
        "/api/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        data="{broken",
        content_type="application/json",
    )
    assert bad_json.status_code == 400

    invalid = client.post(
        "/api/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "A",
            "organization": "",
            "description": "Short",
            "category": "",
            "eligible_years": [0, 7],
            "min_cgpa": 12,
            "deadline": "not-a-date",
            "link": "ftp://invalid.example.com",
            "is_active": "yes",
        },
    )
    assert invalid.status_code == 422
    fields = invalid.get_json()["error"]["details"]["fields"]
    assert {
        "title",
        "organization",
        "description",
        "category",
        "eligible_years",
        "min_cgpa",
        "deadline",
        "link",
        "is_active",
    }.issubset(fields.keys())
