from fastmcp import FastMCP
import os
import sqlite3
import tempfile
import json


# ============================================================
# Paths
# ============================================================

TEMP_DIR = tempfile.gettempdir()

DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print(f"Database path: {DB_PATH}")


# ============================================================
# FastMCP Server
# ============================================================

mcp = FastMCP("ExpenseTracker")


# ============================================================
# Database Initialization
# ============================================================


def init_db():

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
            """
        )

        conn.commit()

    print("Database initialized successfully.")


# Initialize database when server starts
init_db()


# ============================================================
# TOOL 1: Add Expense
# ============================================================


@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    """
    Add a new expense entry to the database.
    """

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """
                INSERT INTO expenses
                (date, amount, category, subcategory, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (date, amount, category, subcategory, note),
            )

            expense_id = cursor.lastrowid

            conn.commit()

        return {
            "status": "success",
            "id": expense_id,
            "message": "Expense added successfully",
        }

    except sqlite3.OperationalError as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}

    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


# ============================================================
# TOOL 2: List Expenses
# ============================================================


@mcp.tool()
def list_expenses(start_date, end_date):
    """
    List expense entries within an inclusive date range.
    """

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """
                SELECT
                    id,
                    date,
                    amount,
                    category,
                    subcategory,
                    note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (start_date, end_date),
            )

            columns = [column[0] for column in cursor.description]

            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}


# ============================================================
# TOOL 3: Summarize Expenses
# ============================================================


@mcp.tool()
def summarize(start_date, end_date, category=None):
    """
    Summarize expenses by category
    within an inclusive date range.
    """

    try:
        with sqlite3.connect(DB_PATH) as conn:
            query = """
                SELECT
                    category,
                    SUM(amount) AS total_amount,
                    COUNT(*) AS count
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """

            params = [start_date, end_date]

            # Optional category filter
            if category:
                query += """
                    AND category = ?
                """

                params.append(category)

            query += """
                GROUP BY category
                ORDER BY total_amount DESC
            """

            cursor = conn.execute(query, params)

            columns = [column[0] for column in cursor.description]

            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}


# ============================================================
# RESOURCE: Categories
# ============================================================


@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """
    Return expense categories from categories.json.
    """

    default_categories = {
        "categories": [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Travel",
            "Education",
            "Business",
            "Other",
        ]
    }

    try:
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()

    except FileNotFoundError:
        return json.dumps(default_categories, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Could not load categories: {str(e)}"})


# ============================================================
# Start MCP Server
# ============================================================

if __name__ == "__main__":
    mcp.run()
