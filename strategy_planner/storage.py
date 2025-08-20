from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "strategy.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS canvases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                customer_jobs TEXT,
                pains TEXT,
                gains TEXT,
                products_services TEXT,
                gain_creators TEXT,
                pain_relievers TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                function TEXT,
                prompt TEXT,
                backend TEXT,
                model TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


def _row_to_dict(row: sqlite3.Row) -> Dict:
    return {k: row[k] for k in row.keys()}


def list_canvases() -> List[Dict]:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id, name, updated_at FROM canvases ORDER BY datetime(updated_at) DESC, name ASC"
        )
        rows = cur.fetchall()
        return [{"id": r["id"], "name": r["name"], "updated_at": r["updated_at"]} for r in rows]


def get_canvas_by_id(canvas_id: int) -> Optional[Dict]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM canvases WHERE id = ?", (canvas_id,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def get_canvas_by_name(name: str) -> Optional[Dict]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM canvases WHERE name = ?", (name,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def save_canvas(
    *,
    name: str,
    customer_jobs: str = "",
    pains: str = "",
    gains: str = "",
    products_services: str = "",
    gain_creators: str = "",
    pain_relievers: str = "",
    canvas_id: Optional[int] = None,
) -> Dict:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with get_conn() as conn:
        if canvas_id is None:
            cur = conn.execute(
                """
                INSERT INTO canvases (
                    name, customer_jobs, pains, gains,
                    products_services, gain_creators, pain_relievers,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    customer_jobs,
                    pains,
                    gains,
                    products_services,
                    gain_creators,
                    pain_relievers,
                    now,
                    now,
                ),
            )
            new_id = cur.lastrowid
            return {"id": new_id, "name": name, "updated_at": now}
        else:
            conn.execute(
                """
                UPDATE canvases
                SET name = ?, customer_jobs = ?, pains = ?, gains = ?,
                    products_services = ?, gain_creators = ?, pain_relievers = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    name,
                    customer_jobs,
                    pains,
                    gains,
                    products_services,
                    gain_creators,
                    pain_relievers,
                    now,
                    canvas_id,
                ),
            )
            return {"id": canvas_id, "name": name, "updated_at": now}


def delete_canvas(canvas_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM canvases WHERE id = ?", (canvas_id,))


def export_json(canvas_id: int) -> str:
    import json

    data = get_canvas_by_id(canvas_id)
    if not data:
        return "{}"
    return json.dumps(data, indent=2)


def export_markdown(canvas_id: int) -> str:
    data = get_canvas_by_id(canvas_id)
    if not data:
        return "# Value Proposition Canvas\n\n(Not found)"

    name = data.get("name", "Untitled")
    created = data.get("created_at", "")
    updated = data.get("updated_at", "")

    def sec(title: str, key: str) -> str:
        val = (data.get(key) or "").strip()
        return f"## {title}\n\n{val if val else '-'}\n"

    md = [
        f"# Value Proposition Canvas — {name}",
        "",
        f"Created: {created}",
        f"Last Updated: {updated}",
        "",
        "# Customer Segment",
        sec("Customer Jobs", "customer_jobs"),
        sec("Pains", "pains"),
        sec("Gains", "gains"),
        "# Value Proposition",
        sec("Products & Services", "products_services"),
        sec("Gain Creators", "gain_creators"),
        sec("Pain Relievers", "pain_relievers"),
    ]
    return "\n".join(md)


# ---------------------------
# Agents CRUD
# ---------------------------

def list_agents() -> List[Dict]:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id, name, function, backend, model, updated_at FROM agents ORDER BY datetime(updated_at) DESC, name ASC"
        )
        rows = cur.fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "function": r["function"],
                "backend": r["backend"],
                "model": r["model"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]


def get_agent_by_id(agent_id: int) -> Optional[Dict]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def get_agent_by_name(name: str) -> Optional[Dict]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM agents WHERE name = ?", (name,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def save_agent(
    *,
    name: str,
    function: str = "",
    prompt: str = "",
    backend: str = "",
    model: str = "",
    agent_id: Optional[int] = None,
) -> Dict:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with get_conn() as conn:
        if agent_id is None:
            cur = conn.execute(
                """
                INSERT INTO agents (
                    name, function, prompt, backend, model, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    function,
                    prompt,
                    backend,
                    model,
                    now,
                    now,
                ),
            )
            new_id = cur.lastrowid
            return {"id": new_id, "name": name, "updated_at": now}
        else:
            conn.execute(
                """
                UPDATE agents
                SET name = ?, function = ?, prompt = ?, backend = ?, model = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, function, prompt, backend, model, now, agent_id),
            )
            return {"id": agent_id, "name": name, "updated_at": now}


def delete_agent(agent_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
