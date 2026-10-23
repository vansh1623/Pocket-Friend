import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "pocket_friend.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_expense(amount, category, note=""):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO expenses (amount, category, note) VALUES (?, ?, ?)",
            (amount, category, note)
        )


def get_expenses():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            """
            SELECT amount, category, note, created_at
            FROM expenses
            ORDER BY created_at DESC
            """,
            conn
        )

    return df


def get_summary(monthly_budget):
    expenses = get_expenses()
    total_spent = float(expenses["amount"].sum()) if not expenses.empty else 0.0

    return {
        "total_spent": total_spent,
        "monthly_budget": float(monthly_budget),
        "remaining": float(monthly_budget) - total_spent
    }