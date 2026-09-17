"""Minimal Ollama integration for BORO BHAI."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from config import settings

OLLAMA_API_URL = settings.ollama_url
MODEL_NAME = settings.model_name


def sanitize_prompt(prompt: str, max_length: int = 20000) -> str:
    """Remove control characters and limit prompt length to reduce injection risk."""
    if prompt is None:
        raise ValueError("Prompt cannot be empty.")

    cleaned = str(prompt).replace("\x00", "").strip()
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        raise ValueError("Prompt cannot be empty.")
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def generate_response(prompt: str) -> str:
    """Send a prompt to the local Ollama API and return the model text."""
    safe_prompt = sanitize_prompt(prompt)

    payload = {
        "model": MODEL_NAME,
        "prompt": safe_prompt,
        "stream": False,
    }

    request_body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_API_URL,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not reach the local Ollama server. "
            "Make sure Ollama is running on http://127.0.0.1:11434."
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama returned invalid JSON.") from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"Ollama request failed: {exc}") from exc

    response_text = result.get("response")
    if response_text is None:
        raise ValueError("Ollama response did not include a 'response' field.")

    cleaned = str(response_text).strip()
    if not cleaned:
        raise ValueError("Ollama returned an empty response.")
    return cleaned
