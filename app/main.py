"""Simple entry point for demonstrating the BORO BHAI agent loop."""

from app.agent import run_agent


def main() -> None:
    task = "Explain why learning Git is useful for a software developer."
    print("User task:")
    print(task)
    print("\nAgent: analyzing task...")
    print("LLM: generating answer...")
    print("\nFinal response:")
    print(run_agent(task))


if __name__ == "__main__":
    main()
