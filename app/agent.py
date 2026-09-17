"""Minimal agent orchestration layer for BORO BHAI."""

import logging
import re

from app.llm import generate_response
from app.logger_config import configure_logging
from memory.database import get_recent_memories, save_memory
from tools.csv_analyzer import analyze_csv
from tools.file_reader import read_text_file
from tools.pdf_reader import read_pdf_text
from tools.registry import build_registry
from tools.result import ToolResult

configure_logging()


def extract_expression(task: str) -> str | None:
    """Extract a numeric expression from a natural-language request."""
    if not task:
        return None

    matches = re.findall(r"[0-9\+\-\*\/\%\(\)\.\s]+", task)
    for candidate in matches:
        cleaned = candidate.strip()
        if cleaned and re.search(r"\d", cleaned) and any(ch in cleaned for ch in "+-*/%()"):
            return cleaned
    return None


def is_calculation_request(task: str) -> bool:
    """Detect whether the user request is a simple arithmetic calculation."""
    return extract_expression(task) is not None


def route_task(task: str) -> str:
    """Route a request to the appropriate tool or the general LLM path."""
    lowered = task.lower()
    if is_calculation_request(task):
        return "calculator"
    if ("read" in lowered or "summarize" in lowered) and ".txt" in lowered:
        return "text_file"
    if "csv" in lowered or "analyze" in lowered and ".csv" in lowered:
        return "csv"
    if "pdf" in lowered or ".pdf" in lowered:
        return "pdf"
    return "llm"


def _build_memory_context() -> str:
    recent_memories = get_recent_memories(limit=3)
    if not recent_memories:
        return ""
    entries = []
    for entry in recent_memories:
        entries.append(f"- User: {entry['user_input']}\n- Assistant: {entry['agent_response']}")
    return "\nRecent memory:\n" + "\n".join(entries)


def _safe_llm_response(task: str, context: str = "") -> str:
    prompt = (
        "You are BORO BHAI, a helpful AI assistant. "
        "Your task is to provide a concise and useful answer to the user request. "
        f"User request: {task}{context}"
    )
    return generate_response(prompt).strip()


def run_agent(task: str) -> str:
    """Run a minimal agent loop with routing and safe tool usage."""
    if not task or not task.strip():
        raise ValueError("Task cannot be empty.")

    memory_context = _build_memory_context()
    route = route_task(task)

    if route == "calculator":
        try:
            expression = extract_expression(task)
            registry = build_registry()
            calculator = registry.get("calculator")
            result = calculator(expression)
            tool_result = ToolResult(True, "calculator", result=result)
            final_response = f"[Agent]\n[Tool: Calculator]\nResult: {result}\n[Final Response]\n{result}"
            logging.info("Calculator used for task: %s", task)
            save_memory(task, final_response)
            return final_response
        except (KeyError, ValueError) as exc:
            tool_result = ToolResult(False, "calculator", error=str(exc))
            final_response = f"[Agent]\n[Tool: Calculator]\nError: {tool_result.error}\n[Final Response]\nI could not evaluate that arithmetic expression safely."
            logging.error("Calculator error: %s", exc)
            save_memory(task, final_response)
            return final_response

    if route == "text_file":
        try:
            filename = re.search(r"[A-Za-z0-9_./\\-]+\.txt", task)
            file_name = filename.group(0) if filename else "example.txt"
            content = read_text_file(file_name)
            summary = _safe_llm_response(
                f"Summarize this text file content in a clear way.\n\n{content}",
                context=memory_context,
            )
            final_response = f"[Agent]\n[Tool: File Reader]\n[Final Response]\n{summary}"
            save_memory(task, final_response)
            logging.info("Text file read for: %s", file_name)
            return final_response
        except (FileNotFoundError, ValueError) as exc:
            final_response = f"[Agent]\n[Tool: File Reader]\nError: {exc}\n[Final Response]\nI could not read that text file safely."
            logging.error("File reader error: %s", exc)
            save_memory(task, final_response)
            return final_response

    if route == "csv":
        try:
            filename = re.search(r"[A-Za-z0-9_./\\-]+\.csv", task)
            file_name = filename.group(0) if filename else "sample.csv"
            data = analyze_csv(file_name)
            summary = _safe_llm_response(
                f"Explain this CSV dataset in simple language.\n\n{data}",
                context=memory_context,
            )
            final_response = f"[Agent]\n[Tool: CSV Analyzer]\n[Final Response]\n{summary}"
            save_memory(task, final_response)
            logging.info("CSV analyzed for: %s", file_name)
            return final_response
        except (FileNotFoundError, ValueError) as exc:
            final_response = f"[Agent]\n[Tool: CSV Analyzer]\nError: {exc}\n[Final Response]\nI could not analyze that CSV file safely."
            logging.error("CSV analyzer error: %s", exc)
            save_memory(task, final_response)
            return final_response

    if route == "pdf":
        try:
            filename = re.search(r"[A-Za-z0-9_./\\-]+\.pdf", task)
            file_name = filename.group(0) if filename else "sample.pdf"
            text = read_pdf_text(file_name)
            summary = _safe_llm_response(
                f"Summarize this PDF content in simple language.\n\n{text}",
                context=memory_context,
            )
            final_response = f"[Agent]\n[Tool: PDF Reader]\n[Final Response]\n{summary}"
            save_memory(task, final_response)
            logging.info("PDF read for: %s", file_name)
            return final_response
        except (FileNotFoundError, ValueError) as exc:
            final_response = f"[Agent]\n[Tool: PDF Reader]\nError: {exc}\n[Final Response]\nI could not read that PDF file safely."
            logging.error("PDF reader error: %s", exc)
            save_memory(task, final_response)
            return final_response

    answer = _safe_llm_response(task, context=memory_context)
    final_response = f"[Agent]\n[Tool: LLM]\n[Final Response]\n{answer}"
    save_memory(task, final_response)
    return final_response
