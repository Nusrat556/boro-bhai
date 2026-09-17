"""Structured report generation for BORO BHAI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "reports"


def _validate_title(title: str) -> str:
    cleaned = (title or "").strip()
    if not cleaned:
        raise ValueError("Report title cannot be empty.")
    return cleaned


def _safe_output_dir(output_dir: str | Path | None) -> Path:
    if output_dir is None:
        target_dir = DEFAULT_REPORTS_DIR
    else:
        raw_path = str(output_dir)
        if ".." in Path(raw_path).parts:
            raise ValueError("Path traversal is not allowed in report output directories.")
        target_dir = Path(raw_path).expanduser()
        if not target_dir.is_absolute():
            target_dir = (PROJECT_ROOT / target_dir).resolve(strict=False)
        else:
            target_dir = target_dir.resolve(strict=False)

    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def _safe_filename(title: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._\- ]+", "_", title.strip())
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._")
    return cleaned.lower() or "report"


def _normalize_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            if isinstance(item, dict):
                items.extend(f"{key}: {entry}" for key, entry in item.items())
            else:
                text = str(item).strip()
                if text:
                    items.append(text)
        return items
    if isinstance(value, dict):
        return [f"{key}: {entry}" for key, entry in value.items()]
    return [str(value)]


def generate_markdown_report(
    title: str,
    sections: dict[str, Any],
    output_dir: str | Path | None = None,
    filename: str | None = None,
) -> str:
    """Create a Markdown report with a safe filename and safe output directory."""
    cleaned_title = _validate_title(title)
    if not sections:
        raise ValueError("At least one report section is required.")

    target_dir = _safe_output_dir(output_dir)
    report_name = _safe_filename(filename or cleaned_title)
    report_path = target_dir / f"{report_name}.md"

    lines = [f"# {cleaned_title}", ""]
    for heading, content in sections.items():
        lines.append(f"## {heading}")
        items = _normalize_items(content)
        if not items:
            lines.append("- None provided.")
        else:
            for item in items:
                lines.append(f"- {item}")
        lines.append("")

    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return str(report_path)


def generate_report(title: str, sections: dict[str, Any], output_dir: str | Path | None = None) -> str:
    """Backward-compatible report generation entry point."""
    return generate_markdown_report(title, sections, output_dir=output_dir)


def generate_source_list(title: str, sources: list[dict[str, str]] | list[str], output_dir: str | Path | None = None) -> str:
    """Generate a source list report with preserved titles and URLs."""
    cleaned_title = _validate_title(title)
    normalized_sources: list[str] = []
    for source in sources or []:
        if isinstance(source, dict):
            title_text = str(source.get("title", "Untitled source")).strip()
            url_text = str(source.get("url", "")).strip()
            if url_text:
                normalized_sources.append(f"- {title_text}: {url_text}")
            else:
                normalized_sources.append(f"- {title_text}")
        elif isinstance(source, str):
            text = source.strip()
            if text:
                normalized_sources.append(f"- {text}")

    sections = {"Sources": normalized_sources or ["No sources were provided."]}
    return generate_markdown_report(cleaned_title, sections, output_dir=output_dir)


def generate_research_report(
    title: str,
    summary: str,
    sources: list[dict[str, str]] | list[str],
    findings: list[str] | str,
    output_dir: str | Path | None = None,
) -> str:
    """Create a structured research report with preserved sources."""
    cleaned_title = _validate_title(title)
    summary_text = (summary or "No summary was provided.").strip()
    sections = {
        "Summary": [summary_text],
        "Key findings": _normalize_items(findings),
    }
    if sources:
        sections["Sources"] = [
            f"{item.get('title', 'Source')} - {item.get('url', 'No URL')}" if isinstance(item, dict) else str(item)
            for item in sources
        ]
    else:
        sections["Sources"] = ["No sources were provided."]
    return generate_markdown_report(cleaned_title, sections, output_dir=output_dir)


def generate_career_report(title: str, report_data: dict[str, Any], output_dir: str | Path | None = None) -> str:
    """Create a structured career analysis report."""
    cleaned_title = _validate_title(title)
    sections: dict[str, Any] = {
        "Job title": [report_data.get("job_title", "Not specified")],
        "Required skills": _normalize_items(report_data.get("required_skills", [])),
        "Experience": [report_data.get("experience", "Not specified")],
        "Education": [report_data.get("education", "Not specified")],
        "Responsibilities": _normalize_items(report_data.get("responsibilities", [])),
        "Preferred skills": _normalize_items(report_data.get("preferred_skills", [])),
    }
    return generate_markdown_report(cleaned_title, sections, output_dir=output_dir)


def generate_job_analysis_report(title: str, job_analysis: dict[str, Any], output_dir: str | Path | None = None) -> str:
    """Create a job-analysis report from structured requirement data."""
    cleaned_title = _validate_title(title)
    sections = {
        "Job title": [job_analysis.get("job_title", "Untitled job")],
        "Required skills": _normalize_items(job_analysis.get("required_skills", [])),
        "Technologies": _normalize_items(job_analysis.get("technologies", [])),
        "Experience": [job_analysis.get("experience", "Not specified")],
        "Education": [job_analysis.get("education", "Not specified")],
        "Responsibilities": _normalize_items(job_analysis.get("responsibilities", [])),
    }
    if "preferred_skills" in job_analysis:
        sections["Preferred skills"] = _normalize_items(job_analysis.get("preferred_skills", []))
    return generate_markdown_report(cleaned_title, sections, output_dir=output_dir)


def generate_skill_gap_report(title: str, skill_gap: dict[str, Any], output_dir: str | Path | None = None) -> str:
    """Create a skill-gap report from structured missing-skill analysis."""
    cleaned_title = _validate_title(title)
    sections = {
        "Job title": [skill_gap.get("job_title", "Unknown role")],
        "Matched skills": _normalize_items(skill_gap.get("matched_skills", [])),
        "Missing skills": _normalize_items(skill_gap.get("missing_skills", [])),
        "Partially matched": _normalize_items(skill_gap.get("partially_matched_skills", [])),
        "Learning priorities": _normalize_items(skill_gap.get("learning_priorities", [])),
    }
    return generate_markdown_report(cleaned_title, sections, output_dir=output_dir)
