# BORO BHAI

BORO BHAI is a local, explainable AI agent built in Python. It uses a local Ollama model, a lightweight router, and a small set of deterministic tools instead of depending on a large framework too early.

## Project goals

- understand how a real AI agent works
- keep the architecture simple and explainable
- use local tools instead of heavy frameworks too early
- support calculation, memory, file analysis, and structured reasoning
- build toward job-market and technology research later

## Current implemented architecture

```text
User
↓
Interface / CLI
↓
Agent orchestrator
↓
Task router
├─ arithmetic request → calculator tool
├─ .txt request → file reader tool
├─ .csv request → CSV analyzer tool
├─ .pdf request → PDF reader tool
└─ general question → LLM response
↓
Observation / structured result
↓
Memory + final answer
```

## Current stack

- Python 3.13
- Ollama 0.34.1
- Qwen 2.5 3B
- SQLite for local memory
- Standard-library Python modules where possible
- `pypdf` for PDF extraction

## Project structure

- app/
  - llm.py
  - agent.py
  - main.py
  - logger_config.py
- tools/
  - calculator.py
  - registry.py
  - file_reader.py
  - csv_analyzer.py
  - pdf_reader.py
  - web_search.py
  - result.py
- memory/
  - database.py
- tests/
- data/
- reports/

## Available tools

- calculator: safe arithmetic evaluation for numeric expressions
- text_file: reads approved `.txt` files from the `data/` directory
- csv: analyzes CSV structure, missing values, and numeric columns
- pdf: extracts text from approved `.pdf` files inside `data/`
- web_search: fetches current external information from the web for up-to-date queries

## How tool routing works

The agent uses a deterministic routing layer in `app/agent.py`:

1. Validate that the task is not empty.
2. Detect whether the prompt looks like a calculation.
3. Detect whether the prompt includes a supported file type such as `.txt`, `.csv`, or `.pdf`.
4. Route to the matching tool name.
5. Resolve the requested tool from the registry in `tools/registry.py`.
6. Execute the tool, capture the structured result, and use it to generate the final response.
7. Fallback to the LLM-only path for general conversational prompts.

This keeps the logic simple, explainable, and testable without introducing unnecessary framework abstractions.

## How to run BORO BHAI

```powershell
cd "C:\Users\HP\jonayed\A ai agent named BORO BHAI"
.\.venv\Scripts\Activate.ps1
python -m app.main
```

Example prompts:

- `What is 12 * 7?`
- `Read data/example.txt and summarize it.`
- `Analyze data/sample.csv for missing values.`
- `Read data/sample.pdf and summarize the contents.`
- `What is the capital of France?`

## How to run tests

```powershell
cd "C:\Users\HP\jonayed\A ai agent named BORO BHAI"
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
```

## Security and safety

- arithmetic is evaluated using a safe AST check
- file access is restricted to the approved `data/` directory
- path traversal is blocked
- no arbitrary shell execution is allowed
- no `eval()`, `exec()`, `subprocess`, or `os.system()` usage is permitted
- sensitive data is not logged

## Notes

- The project intentionally stays modular and incremental.
- We do not rely on heavy frameworks yet.
- The design keeps LLM communication separate from agent logic and tool execution.
