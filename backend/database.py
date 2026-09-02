"""
Minimal SQLite data layer for the Venture Agent prototype.

No ORM, no migrations — plain sqlite3 with a handful of functions.
The DB is initialized (schema + seed data) automatically on startup.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "venture_agent.db"
SEED_PATH = Path(__file__).parent.parent / "data" / "seed.json"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist, and seed data on first run."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS business (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            industry TEXT,
            location TEXT,
            revenue REAL DEFAULT 0,
            expenses REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            cash REAL DEFAULT 0,
            assets REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS venture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            objective TEXT NOT NULL,
            budget REAL NOT NULL,
            status TEXT DEFAULT 'proposed',
            recommendation TEXT,
            FOREIGN KEY (business_id) REFERENCES business(id)
        );

        CREATE TABLE IF NOT EXISTS employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            role TEXT,
            salary REAL DEFAULT 0,
            FOREIGN KEY (business_id) REFERENCES business(id)
        );

        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (business_id) REFERENCES business(id)
        );
        """
    )
    conn.commit()

    # Seed only if empty, so re-runs don't duplicate data.
    cur.execute("SELECT COUNT(*) AS c FROM business")
    if cur.fetchone()["c"] == 0 and SEED_PATH.exists():
        with open(SEED_PATH, "r") as f:
            seed = json.load(f)

        b = seed["business"]
        cur.execute(
            """INSERT INTO business (id, name, industry, location, revenue, expenses, profit, cash, assets)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                b.get("id"), b["name"], b.get("industry"), b.get("location"),
                b.get("revenue", 0), b.get("expenses", 0), b.get("profit", 0),
                b.get("cash", 0), b.get("assets", 0),
            ),
        )

        for e in seed.get("employees", []):
            cur.execute(
                """INSERT INTO employee (id, business_id, name, role, salary)
                   VALUES (?, ?, ?, ?, ?)""",
                (e.get("id"), e["business_id"], e["name"], e.get("role"), e.get("salary", 0)),
            )

        for v in seed.get("ventures", []):
            cur.execute(
                """INSERT INTO venture (id, business_id, objective, budget, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (v.get("id"), v["business_id"], v["objective"], v["budget"], v.get("status", "proposed")),
            )

        conn.commit()

    conn.close()


# --- Business ---

def get_business(business_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM business WHERE id = ?", (business_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_business(business: dict):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO business (name, industry, location, revenue, expenses, profit, cash, assets)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            business["name"], business.get("industry"), business.get("location"),
            business.get("revenue", 0), business.get("expenses", 0), business.get("profit", 0),
            business.get("cash", 0), business.get("assets", 0),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return get_business(new_id)


# --- Venture ---

def get_venture(venture_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM venture WHERE id = ?", (venture_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_ventures(business_id: int = None):
    conn = get_connection()
    if business_id is not None:
        rows = conn.execute("SELECT * FROM venture WHERE business_id = ?", (business_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM venture").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_venture(venture: dict):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO venture (business_id, objective, budget, status)
           VALUES (?, ?, ?, ?)""",
        (venture["business_id"], venture["objective"], venture["budget"], venture.get("status", "proposed")),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return get_venture(new_id)


def update_venture_recommendation(venture_id: int, recommendation: str):
    conn = get_connection()
    conn.execute("UPDATE venture SET recommendation = ? WHERE id = ?", (recommendation, venture_id))
    conn.commit()
    conn.close()


# --- Employees / Finance ---

def get_employees(business_id: int):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM employee WHERE business_id = ?", (business_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_finance(business_id: int):
    """Finance is derived from the business record for this prototype."""
    business = get_business(business_id)
    if not business:
        return None
    return {
        "business_id": business_id,
        "revenue": business["revenue"],
        "expenses": business["expenses"],
        "profit": business["profit"],
        "cash": business["cash"],
        "debt": 0,
    }


# --- Memory ---

def save_memory(business_id: int, content: str):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO memory (business_id, content) VALUES (?, ?)",
        (business_id, content),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, "business_id": business_id, "content": content}


def get_memories(business_id: int):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM memory WHERE business_id = ?", (business_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
