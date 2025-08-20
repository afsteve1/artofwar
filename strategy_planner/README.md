# Strategy Planner — Value Proposition Canvas

A minimal Streamlit app with local SQLite storage to create and manage Value Proposition Canvases:

- Customer Segment: Customer Jobs, Pains, Gains
- Value Proposition: Products & Services, Gain Creators, Pain Relievers

Data is stored locally in `strategy.db` next to the app. Export canvases as JSON or Markdown.

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
- `strategy.db` — Created on first run; local database
- `requirements.txt` — Python dependencies

## Notes

- All data stays on your machine. SQLite file lives alongside the app.
- Canvas names must be unique. Use the sidebar to create, save, delete, and export.
- Exports include both JSON and nicely formatted Markdown.
