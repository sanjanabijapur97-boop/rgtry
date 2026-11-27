"""Database seed service for local development and demo data."""

from typing import Any

from app.db import get_db
from app.models.opportunity import OpportunityModel
from app.models.profile import StudentProfileModel
from app.models.user import UserModel
from app.utils.datetime_utils import parse_deadline_to_utc_iso

SAMPLE_OPPORTUNITIES: list[dict[str, Any]] = [
    {
        "title": "Smart Campus Hackathon 2027",
        "organization": "Campus Tech Club",
        "description": "Build innovative software solutions for campus life in 36 hours.",
        "category": "hackathon",
        "eligible_branches": ["CSE", "IT", "ECE"],
        "eligible_years": [2, 3, 4],
        "min_cgpa": 7.0,
        "required_skills": ["Python", "Flask"],
        "deadline": "2027-03-15",
        "link": "https://campusconnect.example.com/hackathon-2027",
        "is_active": True,
    },
    {
        "title": "Summer Backend Engineering Internship",
        "organization": "CloudScale Labs",
        "description": "8-week paid internship building REST APIs and data pipelines.",
        "category": "internship",
        "eligible_branches": ["CSE", "IT"],
        "eligible_years": [3, 4],
        "min_cgpa": 8.0,
        "required_skills": ["Python", "SQL"],
        "deadline": "2027-02-28",
        "link": "https://campusconnect.example.com/summer-internship",
        "is_active": True,
    },
    {
        "title": "Docker & Kubernetes Hands-On Workshop",
        "organization": "DevOps Society",
        "description": "Beginner-friendly containerization and deployment bootcamp.",
        "category": "workshop",
        "eligible_branches": [],
        "eligible_years": [],
        "min_cgpa": None,
        "required_skills": [],
        "deadline": "2027-01-25",
        "link": "https://campusconnect.example.com/devops-workshop",
        "is_active": True,
    },
    {
        "title": "Merit Excellence Scholarship",
        "organization": "Alumni Foundation",
        "description": "Annual financial grant for top-performing undergraduate students.",
        "category": "scholarship",
        "eligible_branches": [],
        "eligible_years": [2, 3, 4],
        "min_cgpa": 8.5,
        "required_skills": [],
        "deadline": "2027-04-10",
        "link": "https://campusconnect.example.com/merit-scholarship",
        "is_active": True,
    },
]


def seed_sample_data(
    *,
    admin_email: str = "admin@campusconnect.local",
    admin_password: str = "AdminPass123",
    student_email: str = "aarav@campus.edu",
    student_password: str = "Password123",
) -> dict[str, Any]:
    """Idempotently seed sample admin, student, and opportunities."""
    db = get_db()
    admin_row = UserModel.find_by_email(admin_email)
    admin_created = False
    if admin_row is None:
        admin_row = UserModel.create_admin(admin_email, admin_password)
        admin_created = True

    student_row = UserModel.find_by_email(student_email)
    student_created = False
    if student_row is None:
        student_row = UserModel.create_student("Aarav Sharma", student_email, student_password)
        StudentProfileModel.update(
            int(student_row["id"]),
            {
                "branch": "CSE",
                "year": 3,
                "cgpa": 8.75,
                "skills": ["Python", "Flask", "SQL"],
                "phone": "+91-9876543210",
            },
        )
        student_created = True

    existing_titles = {
        row["title"]
        for row in db.execute("SELECT title FROM opportunities").fetchall()
    }
    opportunities_created = 0
    for item in SAMPLE_OPPORTUNITIES:
        if item["title"] not in existing_titles:
            payload = dict(item)
            payload["deadline"] = parse_deadline_to_utc_iso(payload["deadline"])
            OpportunityModel.create(payload, created_by=int(admin_row["id"]))
            opportunities_created += 1

    return {
        "admin_created": admin_created,
        "admin_email": admin_email,
        "student_created": student_created,
        "student_email": student_email,
        "opportunities_created": opportunities_created,
    }
