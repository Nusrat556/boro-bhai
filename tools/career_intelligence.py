"""Career intelligence helpers for BORO BHAI."""

from __future__ import annotations

import re

from tools.research_synthesis import research_and_synthesize
from tools.result import ToolResult

COMMON_SKILLS = {
    "python",
    "sql",
    "java",
    "javascript",
    "typescript",
    "c#",
    "c++",
    "aws",
    "azure",
    "docker",
    "kubernetes",
    "git",
    "rest",
    "api",
    "machine learning",
    "data analysis",
    "pandas",
    "numpy",
    "excel",
    "powerbi",
    "tableau",
    "etl",
    "spark",
    "postgresql",
    "mysql",
    "mongodb",
    "linux",
    "agile",
    "scrum",
    "mlops",
    "ai",
    "data science",
    "statistics",
    "communication",
    "project management",
    "problem solving",
    "leadership",
}


def _normalize_skill(skill: str) -> str:
    cleaned = re.sub(r"[^a-z0-9+\-/\s]", "", (skill or "").lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def _extract_job_title(text: str) -> str:
    if not text:
        return "Untitled job"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:10]:
        if re.search(r"(job title|title|position|role)", line, flags=re.IGNORECASE):
            continue
        if len(line) <= 80 and not re.search(r"[0-9]{2,}%|[0-9]+ years|experience|responsibilities|skills", line, flags=re.IGNORECASE):
            return line
    if len(lines) > 0:
        return lines[0][:80]
    return "Untitled job"


def extract_job_requirements(job_text: str) -> ToolResult:
    """Extract structured job requirements from a job description or text input."""
    if not job_text or not job_text.strip():
        return ToolResult(False, "job_analyzer", error="Job description is empty.")

    normalized = job_text.strip()
    title = _extract_job_title(normalized)
    text_lower = normalized.lower()

    skills = []
    for skill in sorted(COMMON_SKILLS, key=len, reverse=True):
        if skill in text_lower:
            skills.append(skill)

    experience_match = re.search(r"(\d+\+?)\s*(?:to\s*\d+\+?\s*)?(?:years?|yrs?)", normalized, flags=re.IGNORECASE)
    if experience_match:
        experience = f"{experience_match.group(0).strip()} of experience"
    else:
        experience = "Not specified"

    education = "Not specified"
    for pattern in (r"bachelor(?:'s)? degree", r"master(?:'s)? degree", r"phd", r"degree", r"bsc", r"msc"):
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            education = re.search(pattern, normalized, flags=re.IGNORECASE).group(0)
            break

    responsibilities = []
    for segment in re.split(r"(?i)(?:responsibilities|duties|what you will do)", normalized):
        if len(segment) < 120:
            continue
        cleaned = re.sub(r"\s+", " ", segment).strip()
        if cleaned:
            responsibilities.append(cleaned[:220])

    preferred = []
    for skill in sorted(COMMON_SKILLS, key=len, reverse=True):
        if skill in text_lower and skill not in skills:
            preferred.append(skill)

    return ToolResult(
        True,
        "job_analyzer",
        result={
            "job_title": title,
            "required_skills": skills[:10],
            "technologies": skills[:10],
            "experience": experience,
            "education": education,
            "responsibilities": responsibilities[:3],
            "preferred_skills": preferred[:10],
        },
    )


def analyze_skill_gap(job_text: str, user_skills: list[str]) -> ToolResult:
    """Compare a job profile with a user skill list and identify gaps."""
    if not job_text or not job_text.strip():
        return ToolResult(False, "skill_gap_analyzer", error="Job description is empty.")
    if user_skills is None:
        user_skills = []

    job_result = extract_job_requirements(job_text)
    if not job_result.success:
        return job_result

    profile = job_result.result
    normalized_user = {_normalize_skill(skill) for skill in user_skills if skill and str(skill).strip()}
    job_skills = {_normalize_skill(skill) for skill in profile["required_skills"]}

    matched = sorted(normalized_user & job_skills)
    missing = sorted(job_skills - normalized_user)
    partial_matches = []
    for skill in sorted(job_skills):
        if skill not in normalized_user:
            for user_skill in normalized_user:
                if skill in user_skill or user_skill in skill:
                    partial_matches.append(skill)
                    break

    recommended = missing[:5]
    learning_priorities = recommended if recommended else ["Build more evidence of core skills in your profile."]

    return ToolResult(
        True,
        "skill_gap_analyzer",
        result={
            "job_title": profile["job_title"],
            "matched_skills": matched,
            "missing_skills": missing,
            "partially_matched_skills": sorted(set(partial_matches)),
            "learning_priorities": learning_priorities,
            "recommended_next_skills": recommended,
        },
    )


def research_career_skills(job_title: str, max_results: int = 5) -> ToolResult:
    """Research the current job market for a given career title and summarize recurring skills."""
    if not job_title or not job_title.strip():
        return ToolResult(False, "career_research", error="Job title is empty.")

    query = f"{job_title.strip()} job requirements skills technologies experience"
    research_result = research_and_synthesize(query, max_results=max_results)
    if not research_result.success:
        return ToolResult(False, "career_research", error=research_result.error or "Could not research job requirements.")

    return ToolResult(
        True,
        "career_research",
        result={
            "job_title": job_title.strip(),
            "research": research_result.result,
        },
        metadata={"query": query, "source_count": len(research_result.result.get("sources", [])) if isinstance(research_result.result, dict) else 0},
    )


def career_intelligence(task: str, user_skills: list[str] | None = None) -> ToolResult:
    """Dispatch the requested career-analysis action."""
    if not task or not task.strip():
        return ToolResult(False, "career_intelligence", error="Task is empty.")

    lowered = task.lower()
    if any(keyword in lowered for keyword in ("skills gap", "match my skills", "compare my skills", "skill gap", "missing skills")):
        job_text = task
        if "job description" in lowered:
            job_text = task.split("job description", 1)[1].strip()
        elif "job" in lowered and "skills" in lowered:
            job_text = task
        return analyze_skill_gap(job_text, user_skills or [])

    if any(keyword in lowered for keyword in ("job requirements", "job description", "job title", "role requirements", "candidate profile")):
        job_text = task
        if "job description" in lowered:
            job_text = task.split("job description", 1)[1].strip()
        return extract_job_requirements(job_text)

    if any(keyword in lowered for keyword in ("career research", "research job", "current job requirements", "market research")):
        job_title = re.sub(r"(?i)(career research|research job|current job requirements|market research)[:\-\s]*", "", task).strip()
        return research_career_skills(job_title or "software engineer")

    return ToolResult(False, "career_intelligence", error="Unrecognized career intelligence request.")
