from fastmcp import FastMCP
import os
import aiosqlite
import tempfile
import json


# --------------------------------------------------
# Configuration
# --------------------------------------------------

TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")


# --------------------------------------------------
# Database Initialization
# --------------------------------------------------


async def init_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
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

        await conn.commit()


# --------------------------------------------------
# Add Expense
# --------------------------------------------------


@mcp.tool()
async def add_expense(
    date: str, amount: float, category: str, subcategory: str = "", note: str = ""
):
    """Add a new expense entry."""

    try:
        await init_db()

        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO expenses
                (date, amount, category, subcategory, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (date, amount, category, subcategory, note),
            )

            expense_id = cursor.lastrowid

            await conn.commit()

            return {
                "status": "success",
                "id": expense_id,
                "message": "Expense added successfully",
            }

    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


# --------------------------------------------------
# List Expenses
# --------------------------------------------------


@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    """List expenses within an inclusive date range."""

    try:
        await init_db()

        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
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

            rows = await cursor.fetchall()

            columns = [column[0] for column in cursor.description]

            return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}


# --------------------------------------------------
# Summarize Expenses
# --------------------------------------------------


@mcp.tool()
async def summarize(start_date: str, end_date: str, category: str | None = None):
    """Summarize expenses by category."""

    try:
        await init_db()

        async with aiosqlite.connect(DB_PATH) as conn:
            query = """
                SELECT
                    category,
                    SUM(amount) AS total_amount,
                    COUNT(*) AS count
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """

            params = [start_date, end_date]

            if category:
                query += """
                    AND category = ?
                """

                params.append(category)

            query += """
                GROUP BY category
                ORDER BY total_amount DESC
            """

            cursor = await conn.execute(query, params)

            rows = await cursor.fetchall()

            columns = [column[0] for column in cursor.description]

            return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}


# --------------------------------------------------
# Categories Resource
# --------------------------------------------------


@mcp.resource("expense://categories", mime_type="application/json")
async def categories():
    """Return available expense categories."""

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
        return json.dumps({"error": str(e)})


# --------------------------------------------------
# Run Server
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
