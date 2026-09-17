"""Minimal agent orchestration layer for BORO BHAI."""

from app.llm import generate_response


def run_agent(task: str) -> str:
    """Run a minimal agent loop around the local LLM."""
    if not task or not task.strip():
        raise ValueError("Task cannot be empty.")

    prompt = (
        "You are BORO BHAI, a helpful AI assistant. "
        "Your task is to provide a concise and useful answer to the user request. "
        f"User request: {task}"
    )

    answer = generate_response(prompt)
    return answer.strip()
