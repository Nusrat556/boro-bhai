"""Simple structured report generation for BORO BHAI."""

from __future__ import annotations

from pathlib import Path


def generate_report(title: str, sections: dict, output_dir: str | None = None) -> str:
    """Create a simple Markdown report file with clear sections."""
    if not title:
        raise ValueError("Report title cannot be empty.")
    if not sections:
        raise ValueError("At least one report section is required.")

    target_dir = Path(output_dir) if output_dir else Path(__file__).resolve().parent
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_title = title.strip().replace("/", "-")
    report_path = target_dir / f"{safe_title.lower().replace(' ', '_')}.md"

    lines = [f"# {title}", ""]
    for heading, items in sections.items():
        lines.append(f"## {heading}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    report_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return str(report_path)
