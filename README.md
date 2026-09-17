# BORO BHAI

BORO BHAI is a personal AI agent project built progressively in Python with a local Ollama model.

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
Agent Router
↓
LLM or Tool
↓
Observation/result
↓
Final response
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
- tools/
  - calculator.py
  - registry.py
  - file_reader.py
  - csv_analyzer.py
  - pdf_reader.py
  - result.py
- memory/
  - database.py
- tests/
- data/
- reports/

## How to run

```powershell
cd "C:\Users\HP\jonayed\A ai agent named BORO BHAI"
.\.venv\Scripts\Activate.ps1
python -m app.main
```

## Notes

- The agent is intentionally simple and modular.
- We do not rely on heavy frameworks yet.
- The design separates LLM communication from agent logic.
- Tool access is kept narrow and explicit.

## Security and safety

- arithmetic is evaluated using a safe AST check
- file access is restricted to the approved `data/` directory
- path traversal is blocked
- no arbitrary shell execution is allowed
