"""Minimal agent orchestration layer for BORO BHAI."""

import logging
import re

from app.llm import generate_response
from app.logger_config import configure_logging
from memory.database import DEFAULT_DB_PATH, get_recent_memories, get_relevant_context, save_memory
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


def _extract_file_path(task: str, extension: str) -> str | None:
    """Extract a path ending in the given extension from a task string."""
    pattern = rf"[A-Za-z0-9_./\\-]+\{extension}"
    match = re.search(pattern, task, re.IGNORECASE)
    if match:
        return match.group(0)
    return None


def route_task(task: str) -> str:
    """Route a request to the appropriate tool or the general LLM path."""
    if not task or not task.strip():
        raise ValueError("Task cannot be empty.")

    lowered = task.lower()
    if is_calculation_request(task):
        return "calculator"
    if _extract_file_path(task, ".txt") or (("read" in lowered or "summarize" in lowered or "open" in lowered) and ".txt" in lowered):
        return "text_file"
    if _extract_file_path(task, ".csv") or ("csv" in lowered and ("analyze" in lowered or "inspect" in lowered or "summarize" in lowered or "read" in lowered)):
        return "csv"
    if _extract_file_path(task, ".pdf") or (("read" in lowered or "summarize" in lowered or "extract" in lowered) and "pdf" in lowered):
        return "pdf"
    return "llm"


def _build_memory_context(task: str = "", db_path: str = DEFAULT_DB_PATH) -> str:
    if task:
        recent_memories = get_relevant_context(task, limit=3, db_path=db_path)
    else:
        recent_memories = get_recent_memories(limit=3, db_path=db_path)

    if not recent_memories:
        return ""

    entries = []
    for entry in recent_memories:
        entries.append(f"- User: {entry['user_input']}\n- Assistant: {entry['agent_response']}")
    return "\nRelevant conversation context:\n" + "\n".join(entries)


def _safe_llm_response(task: str, context: str = "") -> str:
    prompt = (
        "You are BORO BHAI, a helpful AI assistant. "
        "Your task is to provide a concise and useful answer to the user request. "
        f"User request: {task}"
    )
    if context:
        prompt = f"{prompt}\n\nConversation context:\n{context}"
    return generate_response(prompt).strip()


def _execute_registered_tool(route: str, task: str):
    """Execute a tool selected from the tool registry for the provided task."""
    registry = build_registry()
    tool = registry.get(route)

    if route == "calculator":
        expression = extract_expression(task)
        if expression is None:
            raise ValueError("No arithmetic expression found.")
        return tool(expression)

    if route == "text_file":
        file_path = _extract_file_path(task, ".txt") or "example.txt"
        return tool(file_path)

    if route == "csv":
        file_path = _extract_file_path(task, ".csv") or "sample.csv"
        return tool(file_path)

    if route == "pdf":
        file_path = _extract_file_path(task, ".pdf") or "sample.pdf"
        return tool(file_path)

    raise KeyError(f"Tool '{route}' is not a registered executable tool.")


def run_agent(task: str) -> str:
    """Run a minimal agent loop with routing and safe tool usage."""
    if not task or not task.strip():
        raise ValueError("Task cannot be empty.")

    memory_context = _build_memory_context(task)
    route = route_task(task)

    if route == "calculator":
        try:
            result = _execute_registered_tool(route, task)
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

    if route in {"text_file", "csv", "pdf"}:
        try:
            tool_name = {
                "text_file": "File Reader",
                "csv": "CSV Analyzer",
                "pdf": "PDF Reader",
            }[route]
            result = _execute_registered_tool(route, task)
            if route == "text_file":
                summary = _safe_llm_response(f"Summarize this text file content in a clear way.\n\n{result}", context=memory_context)
            elif route == "csv":
                summary = _safe_llm_response(f"Explain this CSV dataset in simple language.\n\n{result}", context=memory_context)
            else:
                summary = _safe_llm_response(f"Summarize this PDF content in simple language.\n\n{result}", context=memory_context)
            final_response = f"[Agent]\n[Tool: {tool_name}]\n[Final Response]\n{summary}"
            save_memory(task, final_response)
            logging.info("%s used for task: %s", tool_name, task)
            return final_response
        except (FileNotFoundError, ValueError, KeyError) as exc:
            final_response = f"[Agent]\n[Tool: {tool_name}]\nError: {exc}\n[Final Response]\nI could not process that file safely."
            logging.error("Tool execution error for %s: %s", route, exc)
            save_memory(task, final_response)
            return final_response

    answer = _safe_llm_response(task, context=memory_context)
    final_response = f"[Agent]\n[Tool: LLM]\n[Final Response]\n{answer}"
    save_memory(task, final_response)
    return final_response
