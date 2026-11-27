"""Eligibility evaluation business logic."""

from typing import Any

from app.errors import AppError
from app.models.opportunity import OpportunityModel
from app.models.profile import StudentProfileModel


def find_missing_profile_fields(profile: dict[str, Any]) -> list[str]:
    """Return eligibility-relevant student profile fields that are unset."""
    missing: list[str] = []
    if not profile.get("branch"):
        missing.append("branch")
    if profile.get("year") is None:
        missing.append("year")
    if profile.get("cgpa") is None:
        missing.append("cgpa")
    if not profile.get("skills"):
        missing.append("skills")
    return missing


def evaluate_eligibility(
    profile: dict[str, Any], opportunity: dict[str, Any]
) -> dict[str, Any]:
    """Evaluate student profile against an opportunity's eligibility rules."""
    reasons: list[str] = []
    missing_fields = find_missing_profile_fields(profile)

    # 1. Eligible branches
    eligible_branches: list[str] = opportunity.get("eligible_branches") or []
    if eligible_branches:
        student_branch = profile.get("branch")
        allowed_lower = {b.lower() for b in eligible_branches}
        if not student_branch:
            reasons.append(
                f"Profile branch is missing (eligible branches: {', '.join(eligible_branches)})."
            )
        elif student_branch.lower() not in allowed_lower:
            reasons.append(
                f"Branch '{student_branch}' is not in eligible branches ({', '.join(eligible_branches)})."
            )

    # 2. Eligible years
    eligible_years: list[int] = opportunity.get("eligible_years") or []
    if eligible_years:
        student_year = profile.get("year")
        years_str = ", ".join(str(y) for y in eligible_years)
        if student_year is None:
            reasons.append(
                f"Profile year is missing (eligible years: {years_str})."
            )
        elif student_year not in eligible_years:
            reasons.append(
                f"Academic year {student_year} is not in eligible years ({years_str})."
            )

    # 3. Minimum CGPA
    min_cgpa = opportunity.get("min_cgpa")
    if min_cgpa is not None:
        student_cgpa = profile.get("cgpa")
        if student_cgpa is None:
            reasons.append(
                f"Profile CGPA is missing (minimum required: {min_cgpa})."
            )
        elif student_cgpa < min_cgpa:
            reasons.append(
                f"CGPA {student_cgpa} is below the minimum required {min_cgpa}."
            )

    # 4. Required skills
    required_skills: list[str] = opportunity.get("required_skills") or []
    if required_skills:
        student_skills: list[str] = profile.get("skills") or []
        student_skills_lower = {s.lower() for s in student_skills}
        if not student_skills:
            reasons.append(
                f"Profile skills are missing (required skills: {', '.join(required_skills)})."
            )
        else:
            lacking = [
                skill
                for skill in required_skills
                if skill.lower() not in student_skills_lower
            ]
            if lacking:
                reasons.append(
                    f"Missing required skills: {', '.join(lacking)}."
                )

    return {
        "opportunity_id": opportunity["id"],
        "eligible": len(reasons) == 0,
        "reasons": reasons,
        "missing_fields": missing_fields,
    }


def check_student_eligibility(user_id: int, opportunity_id: int) -> dict[str, Any]:
    """Load student profile and opportunity and evaluate eligibility."""
    opp_row = OpportunityModel.find_by_id(opportunity_id)
    if opp_row is None:
        raise AppError(
            code="OPPORTUNITY_NOT_FOUND",
            message="Opportunity not found.",
            status_code=404,
        )

    profile_row = StudentProfileModel.find_by_user_id(user_id)
    if profile_row is None:
        raise AppError(
            code="PROFILE_NOT_FOUND",
            message="Student profile not found.",
            status_code=404,
        )

    return evaluate_eligibility(
        StudentProfileModel.serialize(profile_row),
        OpportunityModel.serialize(opp_row),
    )
