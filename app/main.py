"""Simple interactive CLI for BORO BHAI."""

from app.agent import run_agent


def main() -> None:
    print("BORO BHAI ready. Type 'exit' or 'quit' to end.")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("BORO BHAI: Goodbye!")
            break
        if not user_input:
            print("BORO BHAI: Please enter a task.")
            continue
        print("\nBORO BHAI:")
        print(run_agent(user_input))


if __name__ == "__main__":
    main()
