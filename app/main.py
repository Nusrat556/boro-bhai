"""Simple local test for the Ollama connection."""

from app.llm import generate_response


def main() -> None:
    prompt = "Explain what an AI agent is in two sentences."
    print("Prompt:")
    print(prompt)
    print("\nResponse from Qwen 2.5 3B:")
    print(generate_response(prompt))


if __name__ == "__main__":
    main()
