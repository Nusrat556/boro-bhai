"""Minimal Ollama integration for BORO BHAI."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def generate_response(prompt: str) -> str:
    """Send a prompt to the local Ollama API and return the model text."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
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
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not reach the local Ollama server. "
            "Make sure Ollama is running on http://127.0.0.1:11434."
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama returned invalid JSON.") from exc

    response_text = result.get("response")
    if response_text is None:
        raise ValueError("Ollama response did not include a 'response' field.")

    return response_text.strip()
