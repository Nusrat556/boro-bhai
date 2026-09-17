"""Simple scheduling layer for recurring BORO BHAI tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from reports.report_generator import generate_career_report, generate_research_report
from tools.registry import build_registry

ALLOWED_CADENCES = {"daily", "weekly"}
ALLOWED_TASK_TYPES = {"technology_research", "remote_job_research", "career_report"}


@dataclass
class AutomationTask:
    """A scheduled task definition without runtime agent coupling."""

    name: str
    cadence: str
    task_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    report_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "cadence": self.cadence,
            "task_type": self.task_type,
            "payload": self.payload,
            "description": self.description,
            "report_path": self.report_path,
        }


def create_automation_task(
    name: str,
    cadence: str,
    task_type: str,
    payload: dict[str, Any] | None = None,
    description: str = "",
) -> AutomationTask:
    """Create a validated automation task."""
    cleaned_name = (name or "").strip()
    if not cleaned_name:
        raise ValueError("Automation task name cannot be empty.")

    cadence_key = (cadence or "").strip().lower()
    if cadence_key not in ALLOWED_CADENCES:
        raise ValueError("Unsupported schedule. Use 'daily' or 'weekly'.")

    task_key = (task_type or "").strip().lower()
    if task_key not in ALLOWED_TASK_TYPES:
        raise ValueError("Unsupported automation task type.")

    scheduled = AutomationTask(
        name=cleaned_name,
        cadence=cadence_key,
        task_type=task_key,
        payload=dict(payload or {}),
        description=(description or "").strip(),
    )
    return scheduled


def _execute_research_task(task: AutomationTask) -> dict[str, Any]:
    registry = build_registry()
    research_tool = registry.get("research_synthesis")
    query = task.payload.get("query") or task.payload.get("topic")
    if not query or not str(query).strip():
        return {"success": False, "error": "Research query is required."}
    max_results = int(task.payload.get("max_results", 3))

    result = research_tool(query, max_results=max_results)
    if not result.success:
        return {"success": False, "error": result.error or "Research execution failed."}

    report_path = generate_research_report(
        title=f"{task.name} report",
        summary=result.result.get("answer", "Research summary unavailable."),
        sources=result.result.get("sources", []),
        findings=[result.result.get("answer", "Research summary unavailable.")],
    )

    return {"success": True, "report_path": report_path, "result": result.result}


def _execute_career_task(task: AutomationTask) -> dict[str, Any]:
    registry = build_registry()
    career_tool = registry.get("career_intelligence")
    job_title = task.payload.get("job_title") or task.payload.get("title")
    if not job_title or not str(job_title).strip():
        return {"success": False, "error": "Job title is required for a career report."}
    user_skills = task.payload.get("user_skills") or []

    task_text = f"job requirements for {job_title}"
    result = career_tool(task_text, user_skills=user_skills)
    if not result.success:
        return {"success": False, "error": result.error or "Career report execution failed."}

    report_path = generate_career_report(
        title=f"{task.name} career report",
        report_data={
            "job_title": result.result.get("job_title", job_title),
            "required_skills": result.result.get("required_skills", []),
            "experience": result.result.get("experience", "Not specified"),
            "education": result.result.get("education", "Not specified"),
            "responsibilities": result.result.get("responsibilities", []),
            "preferred_skills": result.result.get("preferred_skills", []),
        },
    )

    return {"success": True, "report_path": report_path, "result": result.result}


def execute_automation_task(task: AutomationTask | dict[str, Any]) -> dict[str, Any]:
    """Execute a scheduled task and return a structured result."""
    if isinstance(task, dict):
        task = create_automation_task(
            name=task.get("name", "unnamed-task"),
            cadence=task.get("cadence", "daily"),
            task_type=task.get("task_type", "technology_research"),
            payload=task.get("payload", {}),
            description=task.get("description", ""),
        )

    if task.task_type == "technology_research":
        payload = _execute_research_task(task)
        return {"name": task.name, "cadence": task.cadence, "task_type": task.task_type, **payload}

    if task.task_type == "remote_job_research":
        task.payload.setdefault("query", "global remote software engineer jobs and employee requirements")
        payload = _execute_research_task(task)
        return {"name": task.name, "cadence": task.cadence, "task_type": task.task_type, **payload}

    if task.task_type == "career_report":
        payload = _execute_career_task(task)
        return {"name": task.name, "cadence": task.cadence, "task_type": task.task_type, **payload}

    return {"success": False, "name": task.name, "cadence": task.cadence, "task_type": task.task_type, "error": "Unknown automation task type."}
