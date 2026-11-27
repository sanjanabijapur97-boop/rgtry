# CampusConnect API Documentation

Base URL: `http://<HOST>:<PORT>/api` (default local: `http://localhost:5000/api`)

All responses use JSON:

- **Success**: `{"success": true, "data": ...}`
- **Error**: `{"success": false, "error": {"code": "...", "message": "...", "details": {}}}`

---

## Feature 0 — Health

### `GET /api/health`

Verify that the API server is running and SQLite database connectivity is healthy.

- **Auth**: None (Public)
- **Parameters**: None
- **Sample Request JSON**: None

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "database": "connected",
    "timestamp": "2026-11-26T13:40:00Z"
  }
}
```

#### Sample Error Response (`500 Internal Server Error`)

```json
{
  "success": false,
  "error": {
    "code": "DATABASE_UNAVAILABLE",
    "message": "Database connectivity check failed.",
    "details": {}
  }
}
```

- **Status Codes**: `200`, `405`, `500`

---

## Feature 1 — Authentication

### `POST /api/auth/register`

Register a new student account. Public registration always creates a `student` user and initializes their student profile. Admin accounts can only be created via `flask create-admin`.

- **Auth**: None (Public)
- **Parameters**: None (JSON request body)
- **Sample Request JSON**:

```json
{
  "name": "Aarav Sharma",
  "email": "aarav@campus.edu",
  "password": "Password123"
}
```

#### Sample Success Response (`201 Created`)

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "name": "Aarav Sharma",
      "email": "aarav@campus.edu",
      "role": "student",
      "created_at": "2026-11-26T13:55:00Z"
    }
  }
}
```

#### Sample Error Responses

`409 Conflict` (duplicate email):

```json
{
  "success": false,
  "error": {
    "code": "EMAIL_ALREADY_EXISTS",
    "message": "An account with this email already exists.",
    "details": {}
  }
}
```

`422 Unprocessable Entity` (validation failure):

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid registration data.",
    "details": {
      "fields": {
        "password": "Password must be between 8 and 128 characters."
      }
    }
  }
}
```

- **Status Codes**: `201`, `400`, `405`, `409`, `422`, `500`

---

### `POST /api/auth/login`

Authenticate a student or admin with email and password and receive a Bearer JWT.

- **Auth**: None (Public)
- **Parameters**: None (JSON request body)
- **Sample Request JSON**:

```json
{
  "email": "aarav@campus.edu",
  "password": "Password123"
}
```

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "access_token": "<jwt-token>",
    "token_type": "Bearer",
    "expires_in": 86400,
    "expires_at": "2026-11-27T13:55:00Z",
    "user": {
      "id": 1,
      "name": "Aarav Sharma",
      "email": "aarav@campus.edu",
      "role": "student",
      "created_at": "2026-11-26T13:55:00Z"
    }
  }
}
```

#### Sample Error Response (`401 Unauthorized`)

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password.",
    "details": {}
  }
}
```

- **Status Codes**: `200`, `400`, `401`, `405`, `422`, `500`

---

### `GET /api/auth/me`

Return the currently authenticated user's account summary.

- **Auth**: Bearer JWT (`Authorization: Bearer <access_token>`) — `student` or `admin`
- **Parameters**: None
- **Sample Request JSON**: None

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "name": "Aarav Sharma",
      "email": "aarav@campus.edu",
      "role": "student",
      "created_at": "2026-11-26T13:55:00Z"
    }
  }
}
```

#### Sample Error Response (`401 Unauthorized`)

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Missing or invalid Authorization Bearer token.",
    "details": {}
  }
}
```

- **Status Codes**: `200`, `401`, `405`, `500`

---

### `POST /api/auth/change-password`

Change the currently authenticated user's password.

- **Auth**: Bearer JWT (`student` or `admin`)
- **Sample Request JSON**:

```json
{
  "current_password": "Password123",
  "new_password": "NewPassword456"
}
```

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "password_changed": true
  }
}
```

- **Status Codes**: `200`, `400`, `401`, `405`, `422`, `500`


---

## Feature 2 — Student Profile

### `GET /api/profile`

View the currently authenticated student's profile.

- **Auth**: Bearer JWT (`student` role only)
- **Parameters**: None
- **Sample Request JSON**: None

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "profile": {
      "user_id": 1,
      "email": "aarav@campus.edu",
      "name": "Aarav Sharma",
      "branch": "CSE",
      "year": 3,
      "cgpa": 8.75,
      "skills": ["Python", "Flask"],
      "phone": "+91-9876543210",
      "created_at": "2026-11-26T13:55:00Z",
      "updated_at": "2026-11-26T14:05:00Z"
    }
  }
}
```

#### Sample Error Response (`403 Forbidden`)

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to perform this action.",
    "details": {}
  }
}
```

- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `500`

---

### `GET /api/opportunities/eligible`

List opportunities evaluated against the authenticated student's profile. Supports the same search, category, sorting, and pagination parameters as `GET /api/opportunities` (`active` defaults to `true`), plus `eligible_only` (boolean string `true`/`false`, default `true`).

- **Auth**: Bearer JWT (`student` role only)
- **Query Parameters**: `q`, `category`, `active` (default `true`), `eligible_only` (default `true`), `sort`, `order`, `page`, `per_page`

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "Smart Campus Hackathon 2026",
        "organization": "Tech Club",
        "category": "hackathon",
        "eligibility": {
          "eligible": true,
          "reasons": [],
          "missing_fields": []
        }
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 1,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `422`, `500`

---

## Feature 6 — Applications

### `POST /api/opportunities/<id>/apply`

Submit an application for an active, non-expired opportunity that the authenticated student is eligible for. Re-applying after a `withdrawn` status reactivates the application as `submitted`.

- **Auth**: Bearer JWT (`student` role only)
- **Parameters**: Path parameter `id` (integer)
- **Sample Request JSON** *(optional)*:

```json
{
  "note": "Built 3 Flask APIs and won campus coding sprint."
}
```

#### Sample Success Response (`201 Created`)

```json
{
  "success": true,
  "data": {
    "application": {
      "id": 1,
      "opportunity_id": 1,
      "user_id": 2,
      "status": "submitted",
      "note": "Built 3 Flask APIs and won campus coding sprint.",
      "admin_remarks": null,
      "created_at": "2026-11-26T15:00:00Z",
      "updated_at": "2026-11-26T15:00:00Z",
      "opportunity": {
        "id": 1,
        "title": "Smart Campus Hackathon 2026",
        "organization": "Tech Club",
        "category": "hackathon",
        "deadline": "2026-12-20T18:29:00Z",
        "is_active": true
      }
    }
  }
}
```

- **Status Codes**: `201`, `400`, `401`, `403`, `404`, `405`, `409`, `422`, `500`

---

### `GET /api/applications`

List the authenticated student's submitted applications with optional `status` filter (`submitted`, `shortlisted`, `accepted`, `rejected`, `withdrawn`) and pagination (`page`, `per_page`).

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `401`, `403`, `405`, `422`, `500`

---

### `GET /api/applications/<id>`

View a single application (`student` owner or `admin`). Admin responses include an `applicant` profile summary.

- **Auth**: Bearer JWT (`student` owner or `admin`)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `500`

---

### `POST /api/applications/<id>/withdraw`

Withdraw a student's own application (allowed when status is `submitted` or `shortlisted`).

- **Auth**: Bearer JWT (`student` role only, owner)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `409`, `422`, `500`

---

### `GET /api/opportunities/<id>/applications`

List all applicants for a specific opportunity (includes student `applicant` profile details). Supports `status`, `page`, and `per_page`.

- **Auth**: Bearer JWT (`admin` role only)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `422`, `500`

---

### `PATCH /api/applications/<id>/status`

Update an application's status (`submitted`, `shortlisted`, `accepted`, `rejected`) and optional `admin_remarks`.

- **Auth**: Bearer JWT (`admin` role only)
- **Sample Request JSON**:

```json
{
  "status": "shortlisted",
  "admin_remarks": "Strong Flask backend portfolio."
}
```

- **Status Codes**: `200`, `400`, `401`, `403`, `404`, `405`, `422`, `500`

---

## Feature 7 — Bookmarks (Saved Opportunities)

### `GET /api/bookmarks`

List the authenticated student's bookmarked opportunities (`active`, `page`, `per_page`).

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `401`, `403`, `405`, `422`, `500`

---

### `POST /api/opportunities/<id>/bookmark`

Save an opportunity to the authenticated student's bookmarks (returns `201` when created, `200` with `"already_bookmarked": true` if already saved).

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `201`, `401`, `403`, `404`, `405`, `500`

---

### `DELETE /api/opportunities/<id>/bookmark`

Remove an opportunity from the authenticated student's bookmarks.

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `500`

---

## Feature 8 — Admin Analytics

### `GET /api/admin/stats`

Return aggregate counts of users, opportunities (active/inactive/by category), applications (by status), and bookmarks.

- **Auth**: Bearer JWT (`admin` role only)
- **Status Codes**: `200`, `401`, `403`, `405`, `500`

---

### `PUT /api/profile` & `PATCH /api/profile`

Update the authenticated student's profile (`name`, `branch`, `year`, `cgpa`, `skills`, `phone`).

- `PUT /api/profile`: Full update (`name` required; omitted optional fields reset to `null`/`[]`).
- `PATCH /api/profile`: Partial update (updates only provided fields; at least one field required).

- **Auth**: Bearer JWT (`student` role only)
- **Parameters**: None (JSON request body)
- **Sample Request JSON**:

```json
{
  "name": "Aarav Sharma",
  "branch": "CSE",
  "year": 3,
  "cgpa": 8.75,
  "skills": ["Python", "Flask", "SQLite"],
  "phone": "+91-9876543210"
}
```

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "profile": {
      "user_id": 1,
      "email": "aarav@campus.edu",
      "name": "Aarav Sharma",
      "branch": "CSE",
      "year": 3,
      "cgpa": 8.75,
      "skills": ["Python", "Flask", "SQLite"],
      "phone": "+91-9876543210",
      "created_at": "2026-11-26T13:55:00Z",
      "updated_at": "2026-11-26T14:05:00Z"
    }
  }
}
```

#### Sample Error Response (`422 Unprocessable Entity`)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid profile data.",
    "details": {
      "fields": {
        "cgpa": "CGPA must be between 0.0 and 10.0."
      }
    }
  }
}
```

- **Status Codes**: `200`, `400`, `401`, `403`, `404`, `405`, `422`, `500`


---

## Feature 3 — Opportunities

> **Note on Deadlines**: All timestamps are stored and returned in UTC ISO 8601 (`...Z`). Date-only `deadline` values (`YYYY-MM-DD`) close at `23:59:00 Asia/Kolkata` (`+05:30`) and are stored as UTC (e.g., `2026-12-20` → `2026-12-20T18:29:00Z`).

### `GET /api/opportunities`

List opportunities with keyword search, category/active filtering, sorting, and pagination.

- **Auth**: None (Public)
- **Query Parameters**:
  - `q` (string, optional): Case-insensitive keyword search across `title`, `organization`, `description`, `category`, and `required_skills`
  - `category` (string, optional): Case-insensitive exact category filter (e.g., `hackathon`, `internship`)
  - `active` (boolean string `true`/`false`, optional): Filter by `is_active`
  - `sort` (string, optional): `created_at` (default), `deadline`, `title`, or `min_cgpa`
  - `order` (string, optional): `asc` or `desc` (defaults to `desc` for `created_at`, `asc` for other sort fields)
  - `page` (integer `>= 1`, default `1`)
  - `per_page` (integer `1..100`, default `10`)
- **Sample Request**: `GET /api/opportunities?q=python&category=hackathon&active=true&sort=deadline&order=asc&page=1&per_page=10`

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "Smart Campus Hackathon 2026",
        "organization": "Tech Club",
        "description": "Build innovative solutions for campus life in 36 hours.",
        "category": "hackathon",
        "eligible_branches": ["CSE", "IT", "ECE"],
        "eligible_years": [2, 3, 4],
        "min_cgpa": 7.5,
        "required_skills": ["Python", "Flask"],
        "deadline": "2026-12-20T18:29:00Z",
        "link": "https://campusconnect.example.com/hackathon",
        "is_active": true,
        "created_by": 1,
        "created_at": "2026-11-26T14:15:00Z",
        "updated_at": "2026-11-26T14:15:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 1,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

#### Sample Error Response (`422 Unprocessable Entity`)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid pagination parameters.",
    "details": {
      "fields": {
        "page": "page must be an integer >= 1."
      }
    }
  }
}
```

- **Status Codes**: `200`, `405`, `422`, `500`

---

### `GET /api/opportunities/<id>`

Retrieve full details for a single opportunity.

- **Auth**: None (Public)
- **Parameters**: Path parameter `id` (integer)
- **Sample Request JSON**: None

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "opportunity": {
      "id": 1,
      "title": "Smart Campus Hackathon 2026",
      "organization": "Tech Club",
      "description": "Build innovative solutions for campus life in 36 hours.",
      "category": "hackathon",
      "eligible_branches": ["CSE", "IT", "ECE"],
      "eligible_years": [2, 3, 4],
      "min_cgpa": 7.5,
      "required_skills": ["Python", "Flask"],
      "deadline": "2026-12-20T18:29:00Z",
      "link": "https://campusconnect.example.com/hackathon",
      "is_active": true,
      "created_by": 1,
      "created_at": "2026-11-26T14:15:00Z",
      "updated_at": "2026-11-26T14:15:00Z"
    }
  }
}
```

#### Sample Error Response (`404 Not Found`)

```json
{
  "success": false,
  "error": {
    "code": "OPPORTUNITY_NOT_FOUND",
    "message": "Opportunity not found.",
    "details": {}
  }
}
```

- **Status Codes**: `200`, `404`, `405`, `500`

---

### `POST /api/opportunities`

Create a new opportunity.

- **Auth**: Bearer JWT (`admin` role only)
- **Parameters**: None (JSON request body)
- **Sample Request JSON**:

```json
{
  "title": "Smart Campus Hackathon 2026",
  "organization": "Tech Club",
  "description": "Build innovative solutions for campus life in 36 hours.",
  "category": "hackathon",
  "eligible_branches": ["CSE", "IT", "ECE"],
  "eligible_years": [2, 3, 4],
  "min_cgpa": 7.5,
  "required_skills": ["Python", "Flask"],
  "deadline": "2026-12-20",
  "link": "https://campusconnect.example.com/hackathon",
  "is_active": true
}
```

#### Sample Success Response (`201 Created`)

```json
{
  "success": true,
  "data": {
    "opportunity": {
      "id": 1,
      "title": "Smart Campus Hackathon 2026",
      "organization": "Tech Club",
      "description": "Build innovative solutions for campus life in 36 hours.",
      "category": "hackathon",
      "eligible_branches": ["CSE", "IT", "ECE"],
      "eligible_years": [2, 3, 4],
      "min_cgpa": 7.5,
      "required_skills": ["Python", "Flask"],
      "deadline": "2026-12-20T18:29:00Z",
      "link": "https://campusconnect.example.com/hackathon",
      "is_active": true,
      "created_by": 1,
      "created_at": "2026-11-26T14:15:00Z",
      "updated_at": "2026-11-26T14:15:00Z"
    }
  }
}
```

#### Sample Error Response (`403 Forbidden`)

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to perform this action.",
    "details": {}
  }
}
```

- **Status Codes**: `201`, `400`, `401`, `403`, `405`, `422`, `500`

---

### `PUT /api/opportunities/<id>` & `PATCH /api/opportunities/<id>`

Update an existing opportunity (`PUT` performs a full replacement; `PATCH` performs a partial update).

- **Auth**: Bearer JWT (`admin` role only)
- **Parameters**: Path parameter `id` (integer)
- **Sample Request JSON (`PATCH`)**:

```json
{
  "min_cgpa": 8.0,
  "is_active": false
}
```

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "opportunity": {
      "id": 1,
      "title": "Smart Campus Hackathon 2026",
      "organization": "Tech Club",
      "description": "Build innovative solutions for campus life in 36 hours.",
      "category": "hackathon",
      "eligible_branches": ["CSE", "IT", "ECE"],
      "eligible_years": [2, 3, 4],
      "min_cgpa": 8.0,
      "required_skills": ["Python", "Flask"],
      "deadline": "2026-12-20T18:29:00Z",
      "link": "https://campusconnect.example.com/hackathon",
      "is_active": false,
      "created_by": 1,
      "created_at": "2026-11-26T14:15:00Z",
      "updated_at": "2026-11-26T14:20:00Z"
    }
  }
}
```

- **Status Codes**: `200`, `400`, `401`, `403`, `404`, `405`, `422`, `500`

---

### `DELETE /api/opportunities/<id>`

Delete an opportunity.

- **Auth**: Bearer JWT (`admin` role only)
- **Parameters**: Path parameter `id` (integer)
- **Sample Request JSON**: None

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "deleted": true,
    "id": 1
  }
}
```

- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `500`

---

### `GET /api/opportunities/eligible`

List opportunities evaluated against the authenticated student's profile. Supports the same search, category, sorting, and pagination parameters as `GET /api/opportunities` (`active` defaults to `true`), plus `eligible_only` (boolean string `true`/`false`, default `true`).

- **Auth**: Bearer JWT (`student` role only)
- **Query Parameters**: `q`, `category`, `active` (default `true`), `eligible_only` (default `true`), `sort`, `order`, `page`, `per_page`

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "Smart Campus Hackathon 2026",
        "organization": "Tech Club",
        "category": "hackathon",
        "eligibility": {
          "eligible": true,
          "reasons": [],
          "missing_fields": []
        }
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 1,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `422`, `500`

---

## Feature 6 — Applications

### `POST /api/opportunities/<id>/apply`

Submit an application for an active, non-expired opportunity that the authenticated student is eligible for. Re-applying after a `withdrawn` status reactivates the application as `submitted`.

- **Auth**: Bearer JWT (`student` role only)
- **Parameters**: Path parameter `id` (integer)
- **Sample Request JSON** *(optional)*:

```json
{
  "note": "Built 3 Flask APIs and won campus coding sprint."
}
```

#### Sample Success Response (`201 Created`)

```json
{
  "success": true,
  "data": {
    "application": {
      "id": 1,
      "opportunity_id": 1,
      "user_id": 2,
      "status": "submitted",
      "note": "Built 3 Flask APIs and won campus coding sprint.",
      "admin_remarks": null,
      "created_at": "2026-11-26T15:00:00Z",
      "updated_at": "2026-11-26T15:00:00Z",
      "opportunity": {
        "id": 1,
        "title": "Smart Campus Hackathon 2026",
        "organization": "Tech Club",
        "category": "hackathon",
        "deadline": "2026-12-20T18:29:00Z",
        "is_active": true
      }
    }
  }
}
```

- **Status Codes**: `201`, `400`, `401`, `403`, `404`, `405`, `409`, `422`, `500`

---

### `GET /api/applications`

List the authenticated student's submitted applications with optional `status` filter (`submitted`, `shortlisted`, `accepted`, `rejected`, `withdrawn`) and pagination (`page`, `per_page`).

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `401`, `403`, `405`, `422`, `500`

---

### `GET /api/applications/<id>`

View a single application (`student` owner or `admin`). Admin responses include an `applicant` profile summary.

- **Auth**: Bearer JWT (`student` owner or `admin`)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `500`

---

### `POST /api/applications/<id>/withdraw`

Withdraw a student's own application (allowed when status is `submitted` or `shortlisted`).

- **Auth**: Bearer JWT (`student` role only, owner)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `409`, `422`, `500`

---

### `GET /api/opportunities/<id>/applications`

List all applicants for a specific opportunity (includes student `applicant` profile details). Supports `status`, `page`, and `per_page`.

- **Auth**: Bearer JWT (`admin` role only)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `422`, `500`

---

### `PATCH /api/applications/<id>/status`

Update an application's status (`submitted`, `shortlisted`, `accepted`, `rejected`) and optional `admin_remarks`.

- **Auth**: Bearer JWT (`admin` role only)
- **Sample Request JSON**:

```json
{
  "status": "shortlisted",
  "admin_remarks": "Strong Flask backend portfolio."
}
```

- **Status Codes**: `200`, `400`, `401`, `403`, `404`, `405`, `422`, `500`

---

## Feature 7 — Bookmarks (Saved Opportunities)

### `GET /api/bookmarks`

List the authenticated student's bookmarked opportunities (`active`, `page`, `per_page`).

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `401`, `403`, `405`, `422`, `500`

---

### `POST /api/opportunities/<id>/bookmark`

Save an opportunity to the authenticated student's bookmarks (returns `201` when created, `200` with `"already_bookmarked": true` if already saved).

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `201`, `401`, `403`, `404`, `405`, `500`

---

### `DELETE /api/opportunities/<id>/bookmark`

Remove an opportunity from the authenticated student's bookmarks.

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `500`

---

## Feature 8 — Admin Analytics

### `GET /api/admin/stats`

Return aggregate counts of users, opportunities (active/inactive/by category), applications (by status), and bookmarks.

- **Auth**: Bearer JWT (`admin` role only)
- **Status Codes**: `200`, `401`, `403`, `405`, `500`


---

## Feature 5 — Eligibility Check

### `GET /api/opportunities/<id>/eligibility`

Evaluate whether the authenticated student's profile satisfies an opportunity's rules (`eligible_branches`, `eligible_years`, `min_cgpa`, `required_skills`), returning a reason for each failed rule and listing any missing profile fields (`branch`, `year`, `cgpa`, `skills`).

- **Auth**: Bearer JWT (`student` role only)
- **Parameters**: Path parameter `id` (integer)
- **Sample Request JSON**: None

#### Sample Success Response (`200 OK` — Ineligible with Missing Fields)

```json
{
  "success": true,
  "data": {
    "opportunity_id": 1,
    "eligible": false,
    "reasons": [
      "Branch 'MECH' is not in eligible branches (CSE, IT).",
      "Profile CGPA is missing (minimum required: 7.5).",
      "Missing required skills: Flask."
    ],
    "missing_fields": ["cgpa"]
  }
}
```

#### Sample Error Response (`404 Not Found`)

```json
{
  "success": false,
  "error": {
    "code": "OPPORTUNITY_NOT_FOUND",
    "message": "Opportunity not found.",
    "details": {}
  }
}
```

- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `500`

---

### `GET /api/opportunities/eligible`

List opportunities evaluated against the authenticated student's profile. Supports the same search, category, sorting, and pagination parameters as `GET /api/opportunities` (`active` defaults to `true`), plus `eligible_only` (boolean string `true`/`false`, default `true`).

- **Auth**: Bearer JWT (`student` role only)
- **Query Parameters**: `q`, `category`, `active` (default `true`), `eligible_only` (default `true`), `sort`, `order`, `page`, `per_page`

#### Sample Success Response (`200 OK`)

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "Smart Campus Hackathon 2026",
        "organization": "Tech Club",
        "category": "hackathon",
        "eligibility": {
          "eligible": true,
          "reasons": [],
          "missing_fields": []
        }
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 1,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `422`, `500`

---

## Feature 6 — Applications

### `POST /api/opportunities/<id>/apply`

Submit an application for an active, non-expired opportunity that the authenticated student is eligible for. Re-applying after a `withdrawn` status reactivates the application as `submitted`.

- **Auth**: Bearer JWT (`student` role only)
- **Parameters**: Path parameter `id` (integer)
- **Sample Request JSON** *(optional)*:

```json
{
  "note": "Built 3 Flask APIs and won campus coding sprint."
}
```

#### Sample Success Response (`201 Created`)

```json
{
  "success": true,
  "data": {
    "application": {
      "id": 1,
      "opportunity_id": 1,
      "user_id": 2,
      "status": "submitted",
      "note": "Built 3 Flask APIs and won campus coding sprint.",
      "admin_remarks": null,
      "created_at": "2026-11-26T15:00:00Z",
      "updated_at": "2026-11-26T15:00:00Z",
      "opportunity": {
        "id": 1,
        "title": "Smart Campus Hackathon 2026",
        "organization": "Tech Club",
        "category": "hackathon",
        "deadline": "2026-12-20T18:29:00Z",
        "is_active": true
      }
    }
  }
}
```

- **Status Codes**: `201`, `400`, `401`, `403`, `404`, `405`, `409`, `422`, `500`

---

### `GET /api/applications`

List the authenticated student's submitted applications with optional `status` filter (`submitted`, `shortlisted`, `accepted`, `rejected`, `withdrawn`) and pagination (`page`, `per_page`).

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `401`, `403`, `405`, `422`, `500`

---

### `GET /api/applications/<id>`

View a single application (`student` owner or `admin`). Admin responses include an `applicant` profile summary.

- **Auth**: Bearer JWT (`student` owner or `admin`)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `500`

---

### `POST /api/applications/<id>/withdraw`

Withdraw a student's own application (allowed when status is `submitted` or `shortlisted`).

- **Auth**: Bearer JWT (`student` role only, owner)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `409`, `422`, `500`

---

### `GET /api/opportunities/<id>/applications`

List all applicants for a specific opportunity (includes student `applicant` profile details). Supports `status`, `page`, and `per_page`.

- **Auth**: Bearer JWT (`admin` role only)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `422`, `500`

---

### `PATCH /api/applications/<id>/status`

Update an application's status (`submitted`, `shortlisted`, `accepted`, `rejected`) and optional `admin_remarks`.

- **Auth**: Bearer JWT (`admin` role only)
- **Sample Request JSON**:

```json
{
  "status": "shortlisted",
  "admin_remarks": "Strong Flask backend portfolio."
}
```

- **Status Codes**: `200`, `400`, `401`, `403`, `404`, `405`, `422`, `500`

---

## Feature 7 — Bookmarks (Saved Opportunities)

### `GET /api/bookmarks`

List the authenticated student's bookmarked opportunities (`active`, `page`, `per_page`).

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `401`, `403`, `405`, `422`, `500`

---

### `POST /api/opportunities/<id>/bookmark`

Save an opportunity to the authenticated student's bookmarks (returns `201` when created, `200` with `"already_bookmarked": true` if already saved).

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `201`, `401`, `403`, `404`, `405`, `500`

---

### `DELETE /api/opportunities/<id>/bookmark`

Remove an opportunity from the authenticated student's bookmarks.

- **Auth**: Bearer JWT (`student` role only)
- **Status Codes**: `200`, `401`, `403`, `404`, `405`, `500`

---

## Feature 8 — Admin Analytics

### `GET /api/admin/stats`

Return aggregate counts of users, opportunities (active/inactive/by category), applications (by status), and bookmarks.

- **Auth**: Bearer JWT (`admin` role only)
- **Status Codes**: `200`, `401`, `403`, `405`, `500`
