"""Tests for Feature 4: search, category filter, sorting, and pagination on GET /api/opportunities."""


def _seed_opportunities(app, client):
    runner = app.test_cli_runner()
    runner.invoke(
        args=["create-admin", "--email", "admin@campus.edu", "--password", "AdminPass123"]
    )
    token = client.post(
        "/api/auth/login",
        json={"email": "admin@campus.edu", "password": "AdminPass123"},
    ).get_json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    items = [
        {
            "title": "AI Innovation Hackathon",
            "organization": "Google DSC",
            "description": "Build generative AI tools using Python and TensorFlow.",
            "category": "hackathon",
            "min_cgpa": 7.0,
            "required_skills": ["Python", "ML"],
            "deadline": "2026-12-10",
            "is_active": True,
        },
        {
            "title": "Backend Engineering Internship",
            "organization": "Acme Cloud",
            "description": "Summer internship building REST APIs with Flask and SQLite.",
            "category": "internship",
            "min_cgpa": 8.5,
            "required_skills": ["Flask", "SQL"],
            "deadline": "2026-12-05",
            "is_active": True,
        },
        {
            "title": "Merit Scholarship 100% Grant",
            "organization": "Campus Foundation",
            "description": "Financial support for high-achieving undergraduate students.",
            "category": "scholarship",
            "min_cgpa": 9.0,
            "required_skills": [],
            "deadline": "2026-12-25",
            "is_active": False,
        },
        {
            "title": "Cloud Native Workshop",
            "organization": "DevOps Society",
            "description": "Hands-on Kubernetes and Docker workshop for beginners.",
            "category": "workshop",
            "min_cgpa": None,
            "required_skills": ["Docker"],
            "deadline": "2026-12-01",
            "is_active": True,
        },
    ]

    for payload in items:
        resp = client.post("/api/opportunities", headers=headers, json=payload)
        assert resp.status_code == 201


def test_keyword_search_matches_fields_and_escapes_wildcards(app, client):
    _seed_opportunities(app, client)

    # Matches organization/description/skills case-insensitively
    by_skill = client.get("/api/opportunities?q=docker").get_json()["data"]
    assert [item["title"] for item in by_skill["items"]] == ["Cloud Native Workshop"]

    by_org = client.get("/api/opportunities?q=acme").get_json()["data"]
    assert [item["title"] for item in by_org["items"]] == [
        "Backend Engineering Internship"
    ]

    # Literal '%' must only match the item containing '100%'
    by_percent = client.get("/api/opportunities?q=100%25").get_json()["data"]
    assert [item["title"] for item in by_percent["items"]] == [
        "Merit Scholarship 100% Grant"
    ]


def test_filter_by_category_and_active(app, client):
    _seed_opportunities(app, client)

    hackathons = client.get("/api/opportunities?category=Hackathon").get_json()["data"]
    assert hackathons["pagination"]["total"] == 1
    assert hackathons["items"][0]["category"] == "hackathon"

    active_only = client.get("/api/opportunities?active=true").get_json()["data"]
    assert active_only["pagination"]["total"] == 3

    inactive_only = client.get("/api/opportunities?active=false").get_json()["data"]
    assert inactive_only["pagination"]["total"] == 1
    assert inactive_only["items"][0]["title"] == "Merit Scholarship 100% Grant"


def test_sort_and_paginate_opportunities(app, client):
    _seed_opportunities(app, client)

    by_deadline_asc = client.get(
        "/api/opportunities?active=true&sort=deadline&order=asc&page=1&per_page=2"
    ).get_json()["data"]
    assert [item["title"] for item in by_deadline_asc["items"]] == [
        "Cloud Native Workshop",
        "Backend Engineering Internship",
    ]
    assert by_deadline_asc["pagination"]["total"] == 3
    assert by_deadline_asc["pagination"]["has_next"] is True

    by_title_desc = client.get(
        "/api/opportunities?sort=title&order=desc"
    ).get_json()["data"]
    titles = [item["title"] for item in by_title_desc["items"]]
    assert titles == sorted(titles, key=str.lower, reverse=True)

    # min_cgpa ASC puts NULLs last
    by_cgpa_asc = client.get(
        "/api/opportunities?sort=min_cgpa&order=asc"
    ).get_json()["data"]
    cgpas = [item["min_cgpa"] for item in by_cgpa_asc["items"]]
    assert cgpas == [7.0, 8.5, 9.0, None]


def test_invalid_search_filter_sort_params_return_422(client):
    resp = client.get("/api/opportunities?sort=invalid&order=sideways&active=maybe")
    assert resp.status_code == 422
    fields = resp.get_json()["error"]["details"]["fields"]
    assert set(fields.keys()) == {"sort", "order", "active"}
