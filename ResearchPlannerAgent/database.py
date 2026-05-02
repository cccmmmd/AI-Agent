import sqlite3
from typing import List, Dict, Any

DB_FILE = "research.db"


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def create_research_plans_table():
    with get_db_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS research_plans (
            id INTEGER PRIMARY KEY,
            short_summary TEXT NOT NULL,
            details TEXT NOT NULL
        )
        """)
        conn.commit()


def get_research_plans() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM research_plans")
        return [dict(row) for row in cursor.fetchall()]


def add_research_plan(short_summary: str, details: str) -> Dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO research_plans (short_summary, details) VALUES (?, ?)",
            (short_summary, details)
        )
        conn.commit()
        return {"id": cursor.lastrowid, "short_summary": short_summary, "details": details}


def delete_research_plan(research_plan_id: int):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM research_plans WHERE id = ?", (research_plan_id,))
        conn.commit()


def init_db():
    create_research_plans_table()