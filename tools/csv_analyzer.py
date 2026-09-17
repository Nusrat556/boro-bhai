"""Basic CSV analysis for BORO BHAI."""

from __future__ import annotations

import csv
import math
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"


def _resolve_csv_path(file_path: str) -> Path:
    requested = str(file_path).replace("\\", "/")
    if requested.startswith("./"):
        requested = requested[2:]
    if requested.startswith("data/"):
        requested = requested[len("data/") :]
    elif requested.startswith("data\\"):
        requested = requested[len("data\\") :]

    target = Path(requested)
    resolved = target if target.is_absolute() else (DATA_DIR / target).resolve(strict=False)
    try:
        resolved.relative_to(DATA_DIR.resolve())
    except ValueError as exc:
        raise ValueError("Access denied: CSV must be inside the approved data directory.") from exc
    return resolved


def _is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def analyze_csv(file_path: str) -> dict:
    """Return basic dataset statistics for a CSV file."""
    resolved = _resolve_csv_path(file_path)
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"CSV file not found: {resolved}")
    if resolved.suffix.lower() != ".csv":
        raise ValueError("Only .csv files are allowed.")

    with resolved.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if not fieldnames:
        return {
            "file": str(resolved),
            "row_count": 0,
            "column_names": [],
            "missing_values": {},
            "numeric_columns": {},
        }

    missing_values = {}
    numeric_columns = {}

    for column in fieldnames:
        values = [row.get(column, "") for row in rows]
        missing_values[column] = sum(1 for value in values if value in (None, "", " "))

        numeric_values = [float(value) for value in values if value not in (None, "", " ") and _is_number(value)]
        if numeric_values:
            numeric_columns[column] = {
                "count": len(numeric_values),
                "mean": round(sum(numeric_values) / len(numeric_values), 4),
                "min": min(numeric_values),
                "max": max(numeric_values),
            }

    return {
        "file": str(resolved),
        "row_count": len(rows),
        "column_names": fieldnames,
        "missing_values": missing_values,
        "numeric_columns": numeric_columns,
    }
