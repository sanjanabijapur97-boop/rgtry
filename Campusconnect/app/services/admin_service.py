"""Admin analytics and platform statistics service."""

from typing import Any

from app.db import get_db


def get_admin_stats() -> dict[str, Any]:
    """Return platform-wide aggregate counts for the admin dashboard."""
    db = get_db()

    user_rows = db.execute(
        "SELECT role, COUNT(*) AS cnt FROM users GROUP BY role"
    ).fetchall()
    users_by_role = {"student": 0, "admin": 0}
    for row in user_rows:
        users_by_role[row["role"]] = int(row["cnt"])

    opp_active_rows = db.execute(
        "SELECT is_active, COUNT(*) AS cnt FROM opportunities GROUP BY is_active"
    ).fetchall()
    active_opps = 0
    inactive_opps = 0
    for row in opp_active_rows:
        if int(row["is_active"]) == 1:
            active_opps = int(row["cnt"])
        else:
            inactive_opps = int(row["cnt"])

    category_rows = db.execute(
        "SELECT category, COUNT(*) AS cnt FROM opportunities GROUP BY category ORDER BY category ASC"
    ).fetchall()
    opps_by_category = {row["category"]: int(row["cnt"]) for row in category_rows}

    app_rows = db.execute(
        "SELECT status, COUNT(*) AS cnt FROM applications GROUP BY status"
    ).fetchall()
    apps_by_status = {
        "submitted": 0,
        "shortlisted": 0,
        "accepted": 0,
        "rejected": 0,
        "withdrawn": 0,
    }
    for row in app_rows:
        apps_by_status[row["status"]] = int(row["cnt"])

    bookmark_count = int(
        db.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]
    )

    return {
        "stats": {
            "users": {
                "total": sum(users_by_role.values()),
                "students": users_by_role["student"],
                "admins": users_by_role["admin"],
            },
            "opportunities": {
                "total": active_opps + inactive_opps,
                "active": active_opps,
                "inactive": inactive_opps,
                "by_category": opps_by_category,
            },
            "applications": {
                "total": sum(apps_by_status.values()),
                "by_status": apps_by_status,
            },
            "bookmarks": {
                "total": bookmark_count,
            },
        }
    }
