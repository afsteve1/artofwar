# Strategy Planner — Value Proposition Canvas

A minimal Streamlit app with local SQLite storage to create and manage Value Proposition Canvases:

- Customer Segment: Customer Jobs, Pains, Gains
- Value Proposition: Products & Services, Gain Creators, Pain Relievers

Data is stored locally in `strategy.db` next to the app. Export canvases as JSON or Markdown.

## Agents (LLM-powered)

Define reusable "agents" with:

- Name and Function (role)
- Prompt (instructions)
- Backend and Model (OpenAI, Anthropic, OpenRouter, or local Ollama)

You can run an agent against a task input and optionally include the current canvas as context. Output is shown inline.

Supported backends (set the corresponding API key):

- `openai` — requires `OPENAI_API_KEY`
- `anthropic` — requires `ANTHROPIC_API_KEY`
- `openrouter` — requires `OPENROUTER_API_KEY`
- `ollama` — runs against local Ollama at `http://localhost:11434` (no key)
- `echo` — debug fallback (just echoes input and context)

Set keys using environment variables or Streamlit secrets.

Environment variables (example):

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENROUTER_API_KEY="or-..."
```

Streamlit secrets (create `.streamlit/secrets.toml` next to `app.py`):

```toml
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
OPENROUTER_API_KEY = "or-..."
```

## Quick Start

1. Create a virtual environment (recommended) and install deps:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

2. Run the app:

```bash
./.venv/bin/streamlit run app.py
```

3. Open the app in your browser if it doesn't auto-open: http://localhost:8501

## Files

- `app.py` — Streamlit UI and interactions
- `storage.py` — SQLite helpers and exports
- `agents.py` — Multi-backend agent runner (OpenAI, Anthropic, OpenRouter, Ollama, echo)
- `strategy.db` — Created on first run; local database
- `requirements.txt` — Python dependencies

## Notes

- All data stays on your machine. SQLite file lives alongside the app.
- Canvas names must be unique. Use the sidebar to create, save, delete, and export.
- Exports include both JSON and nicely formatted Markdown.
