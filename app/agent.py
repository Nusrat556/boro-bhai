"""Minimal agent orchestration layer for BORO BHAI."""

import logging
import re
from typing import Any

from app.llm import generate_response
from app.logger_config import configure_logging
from memory.database import DEFAULT_DB_PATH, get_recent_memories, get_relevant_context, save_memory
from tools.rag_tool import rag_query
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


def _extract_search_query(task: str) -> str:
    """Extract a plain-language search query from a task prompt."""
    cleaned = task.strip()
    lowered = cleaned.lower()

    for prefix in (
        "search the web for ",
        "search web for ",
        "look up ",
        "find latest ",
        "find current ",
        "latest on ",
        "latest news about ",
        "latest updates on ",
        "what are the latest ",
        "what are current ",
        "current information on ",
        "current news about ",
        "research ",
        "research the ",
        "research current ",
    ):
        if lowered.startswith(prefix):
            return cleaned[len(prefix) :].strip()

    return cleaned


def route_task(task: str) -> str:
    """Route a request to the appropriate tool or the general LLM path."""
    if not task or not task.strip():
        raise ValueError("Task cannot be empty.")

    lowered = task.lower()
    if any(keyword in lowered for keyword in ("plan ", "planner", "step-by-step", "roadmap", "workflow", "break this down", "multi-step", "research plan", "execution plan")):
        return "planner"
    if is_calculation_request(task):
        return "calculator"
    if _extract_file_path(task, ".txt") or (("read" in lowered or "summarize" in lowered or "open" in lowered) and ".txt" in lowered):
        return "text_file"
    if _extract_file_path(task, ".csv") or ("csv" in lowered and ("analyze" in lowered or "inspect" in lowered or "summarize" in lowered or "read" in lowered)):
        return "csv"
    if _extract_file_path(task, ".pdf") or (("read" in lowered or "summarize" in lowered or "extract" in lowered) and "pdf" in lowered):
        return "pdf"
    if any(keyword in lowered for keyword in ("job requirements", "job description", "career research", "skills gap", "match my skills", "job title", "current job requirements", "role requirements")):
        return "career_intelligence"
    if any(keyword in lowered for keyword in ("research ", "research the ", "find the latest", "find current")):
        return "research_synthesis"
    if any(keyword in lowered for keyword in ("latest", "current", "recent", "today", "news", "breaking", "search the web", "search web", "look up ", "live updates", "online")):
        return "web_search"
    if any(keyword in lowered for keyword in ("knowledge base", "memory", "what do you remember", "relevant context", "using our notes", "from the docs")):
        return "rag_query"
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


def create_plan(task: str) -> dict[str, Any]:
    """Create a simple multi-step plan for a complex task."""
    cleaned = task.strip()
    if not cleaned:
        raise ValueError("Task cannot be empty.")

    lowered = cleaned.lower()
    steps = []

    if "research" in lowered or "find" in lowered or "latest" in lowered:
        steps.append({
            "step": 1,
            "name": "Gather evidence",
            "type": "research",
            "prompt": f"Research the topic: {cleaned}",
        })
    else:
        steps.append({
            "step": 1,
            "name": "Clarify goal",
            "type": "analysis",
            "prompt": cleaned,
        })

    if "job" in lowered or "career" in lowered or "skills" in lowered:
        steps.append({
            "step": 2,
            "name": "Assess requirements",
            "type": "career",
            "prompt": cleaned,
        })
    else:
        steps.append({
            "step": 2,
            "name": "Check relevant context",
            "type": "rag",
            "prompt": cleaned,
        })

    steps.append({
        "step": len(steps) + 1,
        "name": "Synthesize answer",
        "type": "synthesis",
        "prompt": f"Summarize the findings for: {cleaned}",
    })

    return {
        "goal": cleaned,
        "steps": steps,
    }


def execute_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Execute a previously created plan and return intermediate outputs."""
    if not plan or "steps" not in plan or not plan["steps"]:
        return {"success": False, "steps": [], "error": "No valid plan was provided."}

    outputs: list[dict[str, Any]] = []
    try:
        for step in plan["steps"]:
            step_name = step.get("name", "Unnamed step")
            step_type = step.get("type", "analysis")
            prompt = step.get("prompt", plan.get("goal", ""))

            if step_type == "research":
                result = _execute_registered_tool("research_synthesis", prompt)
            elif step_type == "rag":
                result = rag_query(prompt, top_k=3)
            elif step_type == "career":
                result = _execute_registered_tool("career_intelligence", prompt)
            else:
                result = {"summary": f"Completed step: {step_name}"}

            outputs.append({
                "step": step.get("step", len(outputs) + 1),
                "name": step_name,
                "status": "completed",
                "output": result,
            })
        return {"success": True, "goal": plan.get("goal", ""), "steps": outputs}
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {"success": False, "steps": outputs, "error": str(exc)}


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

    if route == "web_search":
        query = _extract_search_query(task)
        return tool(query)

    if route == "research_synthesis":
        query = _extract_search_query(task)
        return tool(query)

    if route == "career_intelligence":
        return tool(task)

    if route == "rag_query":
        return tool(task)

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

    if route == "web_search":
        try:
            result = _execute_registered_tool(route, task)
            if result.success and isinstance(result.result, list):
                summary = "\n".join(f"- {item['title']}: {item['url']}" for item in result.result)
            else:
                summary = result.error or "I could not find current information for that query."
            final_response = f"[Agent]\n[Tool: Web Search]\n[Final Response]\n{summary}"
            save_memory(task, final_response)
            logging.info("Web search used for task: %s", task)
            return final_response
        except (KeyError, ValueError, TypeError) as exc:
            final_response = f"[Agent]\n[Tool: Web Search]\nError: {exc}\n[Final Response]\nI could not retrieve current information safely."
            logging.error("Web search error: %s", exc)
            save_memory(task, final_response)
            return final_response

    if route == "planner":
        try:
            plan = create_plan(task)
            execution = execute_plan(plan)
            if execution["success"]:
                summary = "\n".join(f"{entry['step']}. {entry['name']}: {entry['status']}" for entry in execution["steps"])
                final_response = f"[Agent]\n[Tool: Planner]\n[Final Response]\nPlan created:\n{summary}"
            else:
                final_response = f"[Agent]\n[Tool: Planner]\nError: {execution.get('error', 'Plan failed')}\n[Final Response]\nI could not create a working plan for that request."
            save_memory(task, final_response)
            logging.info("Planner used for task: %s", task)
            return final_response
        except (KeyError, ValueError, TypeError) as exc:
            final_response = f"[Agent]\n[Tool: Planner]\nError: {exc}\n[Final Response]\nI could not create a working plan for that request."
            logging.error("Planner error: %s", exc)
            save_memory(task, final_response)
            return final_response

    if route == "research_synthesis":
        try:
            query = _extract_search_query(task)
            result = _execute_registered_tool(route, query)
            if result.success:
                answer = result.result.get("answer", "I could not synthesize a reliable answer.")
                sources = result.result.get("sources", [])
                formatted_sources = "\n".join(f"- {source['title']}: {source['url']}" for source in sources)
                final_response = f"[Agent]\n[Tool: Research Synthesis]\n[Final Response]\n{answer}\n\nSources:\n{formatted_sources}"
            else:
                final_response = f"[Agent]\n[Tool: Research Synthesis]\nError: {result.error}\n[Final Response]\nI could not synthesize current information reliably."
            save_memory(task, final_response)
            logging.info("Research synthesis used for task: %s", task)
            return final_response
        except (KeyError, ValueError, TypeError) as exc:
            final_response = f"[Agent]\n[Tool: Research Synthesis]\nError: {exc}\n[Final Response]\nI could not synthesize current information reliably."
            logging.error("Research synthesis error: %s", exc)
            save_memory(task, final_response)
            return final_response

    if route == "rag_query":
        try:
            result = _execute_registered_tool(route, task)
            if result.success:
                context = result.result.get("context", "")
                final_response = f"[Agent]\n[Tool: RAG Query]\n[Final Response]\n{context or 'I found relevant knowledge base entries.'}"
            else:
                final_response = f"[Agent]\n[Tool: RAG Query]\nError: {result.error}\n[Final Response]\nI could not retrieve relevant knowledge from the local index."
            save_memory(task, final_response)
            logging.info("RAG query used for task: %s", task)
            return final_response
        except (KeyError, ValueError, TypeError) as exc:
            final_response = f"[Agent]\n[Tool: RAG Query]\nError: {exc}\n[Final Response]\nI could not retrieve relevant knowledge from the local index."
            logging.error("RAG query error: %s", exc)
            save_memory(task, final_response)
            return final_response

    if route == "career_intelligence":
        try:
            result = _execute_registered_tool(route, task)
            if result.success:
                payload = result.result
                formatted = payload if isinstance(payload, str) else str(payload)
                final_response = f"[Agent]\n[Tool: Career Intelligence]\n[Final Response]\n{formatted}"
            else:
                final_response = f"[Agent]\n[Tool: Career Intelligence]\nError: {result.error}\n[Final Response]\nI could not analyze that career request."
            save_memory(task, final_response)
            logging.info("Career intelligence used for task: %s", task)
            return final_response
        except (KeyError, ValueError, TypeError) as exc:
            final_response = f"[Agent]\n[Tool: Career Intelligence]\nError: {exc}\n[Final Response]\nI could not analyze that career request."
            logging.error("Career intelligence error: %s", exc)
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
