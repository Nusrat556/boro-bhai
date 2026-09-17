"""Service layer for BORO BHAI web API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import jsonify

from app.agent import run_agent
from rag.retriever import ingest_document
from reports.report_generator import generate_research_report
from tools.career_intelligence import analyze_skill_gap, extract_job_requirements
from tools.research_synthesis import research_and_synthesize

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
REPORTS_DIR = PROJECT_ROOT / "reports"
ALLOWED_UPLOAD_TYPES = {".txt", ".csv", ".pdf"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
SESSION_HISTORY: dict[str, list[dict[str, str]]] = {}


def _session_id(session_id: str | None) -> str:
    return (session_id or "default").strip() or "default"


def get_history(session_id: str | None = None) -> list[dict[str, str]]:
    key = _session_id(session_id)
    if key not in SESSION_HISTORY:
        SESSION_HISTORY[key] = []
    return SESSION_HISTORY[key]


def add_history_entry(session_id: str | None, role: str, content: str) -> None:
    history = get_history(session_id)
    history.append({"role": role, "content": content})


def error_response(message: str, status: int = 400, code: str = "validation_error"):
    payload = {"success": False, "error": message, "code": code}
    return jsonify(payload), status


def validate_message(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be an object.")

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message is required.")
    return message.strip()


def validate_query(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be an object.")

    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Research query is required.")
    return query.strip()


def validate_job_input(payload: dict[str, Any]) -> str:
    job_text = payload.get("job_text") if isinstance(payload, dict) else None
    if not isinstance(job_text, str) or not job_text.strip():
        raise ValueError("Job description text is required.")
    return job_text.strip()


def handle_chat(payload: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
    message = validate_message(payload)
    response = run_agent(message)
    add_history_entry(session_id, "user", message)
    add_history_entry(session_id, "assistant", response)
    return {"success": True, "response": response, "history": get_history(session_id)}


def handle_research(payload: dict[str, Any]) -> dict[str, Any]:
    query = validate_query(payload)
    max_results = int(payload.get("max_results", 5) or 5)
    if max_results < 1 or max_results > 10:
        raise ValueError("max_results must be between 1 and 10.")

    result = research_and_synthesize(query, max_results=max_results)
    if not result.success:
        raise RuntimeError(result.error or "Research failed.")

    payload_dict = result.result or {}
    source_list = payload_dict.get("sources", [])
    report_path = generate_research_report(
        title=f"Research: {query[:40]}",
        summary=payload_dict.get("answer", "Research summary unavailable."),
        sources=source_list,
        findings=[payload_dict.get("answer", "Research summary unavailable.")],
    )
    return {
        "success": True,
        "query": query,
        "answer": payload_dict.get("answer", ""),
        "sources": source_list,
        "report_path": report_path,
    }


def handle_job_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    job_text = validate_job_input(payload)
    user_skills = payload.get("user_skills") or []
    if not isinstance(user_skills, list):
        raise ValueError("user_skills must be a list of strings.")

    result = extract_job_requirements(job_text)
    if not result.success:
        raise RuntimeError(result.error or "Job analysis failed.")
    return {"success": True, "analysis": result.result}


def handle_skill_gap(payload: dict[str, Any]) -> dict[str, Any]:
    job_text = validate_job_input(payload)
    user_skills = payload.get("user_skills") or []
    if not isinstance(user_skills, list):
        raise ValueError("user_skills must be a list of strings.")

    result = analyze_skill_gap(job_text, user_skills)
    if not result.success:
        raise RuntimeError(result.error or "Skill-gap analysis failed.")
    return {"success": True, "analysis": result.result}


def handle_upload(file_storage: Any, session_id: str | None = None) -> dict[str, Any]:
    if file_storage is None or getattr(file_storage, "filename", "") in {None, ""}:
        raise ValueError("A file upload is required.")

    name = Path(file_storage.filename).name
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_UPLOAD_TYPES:
        raise ValueError("Unsupported file type. Use .txt, .csv, or .pdf.")

    try:
        file_storage.seek(0, os.SEEK_END)
        size = file_storage.tell()
        file_storage.seek(0)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise ValueError("Unable to read uploaded file size.") from exc

    if size <= 0 or size > MAX_UPLOAD_BYTES:
        raise ValueError("Uploaded file size must be between 1 byte and 5 MB.")

    safe_name = Path(name).name
    if ".." in Path(safe_name).parts:
        raise ValueError("Invalid upload path.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = (UPLOAD_DIR / safe_name).resolve()
    data_root = DATA_DIR.resolve()
    if data_root not in target.parents and target != data_root:
        raise ValueError("File upload path is invalid.")

    file_storage.save(target)
    relative_path = str(target.relative_to(data_root))
    ingest_document(relative_path)

    add_history_entry(session_id, "system", f"Uploaded document: {safe_name}")
    return {"success": True, "filename": safe_name, "size_bytes": size, "path": relative_path}


def list_reports() -> list[dict[str, str]]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for item in sorted(REPORTS_DIR.iterdir()):
        if item.is_file() and item.suffix.lower() == ".md":
            entries.append({"name": item.name, "path": str(item.relative_to(PROJECT_ROOT))})
    return entries


def get_report_text(filename: str) -> str:
    if not filename or ".." in Path(filename).parts:
        raise ValueError("Invalid report filename.")
    safe_path = (REPORTS_DIR / filename).resolve()
    if safe_path.parent != REPORTS_DIR.resolve():
        raise ValueError("Report path is invalid.")
    if not safe_path.exists() or not safe_path.is_file():
        raise FileNotFoundError(f"Report '{filename}' was not found.")
    return safe_path.read_text(encoding="utf-8")
