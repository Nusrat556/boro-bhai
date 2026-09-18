"""Service layer for BORO BHAI web API."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from flask import jsonify

from app.agent import run_agent
from config import settings
from rag.retriever import ingest_document
from reports.report_generator import generate_research_report
from tools.career_intelligence import analyze_skill_gap, extract_job_requirements
from tools.research_synthesis import research_and_synthesize

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
REPORTS_DIR = PROJECT_ROOT / settings.reports_dir
ALLOWED_UPLOAD_TYPES = {".txt", ".csv", ".pdf"}
MAX_UPLOAD_BYTES = settings.max_upload_bytes
SESSION_HISTORY: dict[str, list[dict[str, str]]] = {}


def sanitize_text(value: str | None, *, max_length: int | None = None, allow_newlines: bool = False) -> str:
    """Normalize untrusted text before passing it to tools or the model."""
    if value is None:
        raise ValueError("Value is required.")
    cleaned = str(value).replace("\x00", "").strip()
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", cleaned)
    cleaned = re.sub(r"\s+", "\n" if allow_newlines else " ", cleaned)
    if not cleaned:
        raise ValueError("Value cannot be empty.")
    if max_length is not None and len(cleaned) > max_length:
        raise ValueError(f"Input exceeds the maximum supported length of {max_length} characters.")
    return cleaned.strip()


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
    return sanitize_text(message, max_length=settings.max_message_length)


def validate_query(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be an object.")

    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Research query is required.")
    return sanitize_text(query, max_length=settings.max_query_length)


def validate_job_input(payload: dict[str, Any]) -> str:
    job_text = payload.get("job_text") if isinstance(payload, dict) else None
    if not isinstance(job_text, str) or not job_text.strip():
        raise ValueError("Job description text is required.")
    return sanitize_text(job_text, max_length=settings.max_job_text_length, allow_newlines=True)


def handle_chat(payload: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
    message = validate_message(payload)
    normalized_session_id = _session_id(session_id)
    response = run_agent(message, session_id=normalized_session_id)
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

    original_name = str(getattr(file_storage, "filename", ""))
    if any(part == ".." for part in Path(original_name).parts):
        raise ValueError("Invalid upload path.")

    name = Path(original_name).name
    if not name or name in {".", ".."}:
        raise ValueError("Uploaded file name is invalid.")

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
        raise ValueError(f"Uploaded file size must be between 1 byte and {MAX_UPLOAD_BYTES} bytes.")

    safe_name = Path(name).name
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = (UPLOAD_DIR / safe_name).resolve()
    data_root = DATA_DIR.resolve()
    if data_root not in target.parents and target != data_root:
        raise ValueError("File upload path is invalid.")

    if hasattr(file_storage, "save"):
        file_storage.save(target)
    else:
        file_storage.seek(0)
        target.write_bytes(file_storage.read())

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
    if not filename or not isinstance(filename, str):
        raise ValueError("Invalid report filename.")
    sanitized_filename = sanitize_text(filename, max_length=255)
    if ".." in Path(sanitized_filename).parts:
        raise ValueError("Invalid report filename.")
    safe_path = (REPORTS_DIR / sanitized_filename).resolve()
    if safe_path.parent != REPORTS_DIR.resolve():
        raise ValueError("Report path is invalid.")
    if not safe_path.exists() or not safe_path.is_file():
        raise FileNotFoundError(f"Report '{sanitized_filename}' was not found.")
    return safe_path.read_text(encoding="utf-8")
