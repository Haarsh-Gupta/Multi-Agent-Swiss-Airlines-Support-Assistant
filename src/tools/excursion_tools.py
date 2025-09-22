# src/tools/excursion_tools.py
import sqlite3
import os
from typing import Optional
from langchain_core.tools import tool

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # .../src/tools
_SRC_DIR = os.path.dirname(_CURRENT_DIR)                 # .../src
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)                # .../
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "db", "travel2.sqlite")
DB_PATH = os.getenv("DB_PATH", _DEFAULT_DB_PATH)

@tool
def search_trip_recommendations(
    location: Optional[str] = None,
    name: Optional[str] = None,
    keywords: Optional[str] = None,
) -> list[dict]:
    """Search for trip recommendations based on location, name, and keywords."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT * FROM trip_recommendations WHERE 1=1"
    params = []
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    if keywords:
        keyword_list = keywords.split(",")
        keyword_conditions = " OR ".join(["keywords LIKE ?" for _ in keyword_list])
        query += f" AND ({keyword_conditions})"
        params.extend([f"%{keyword.strip()}%" for keyword in keyword_list])
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return [dict(zip([column[0] for column in cursor.description], row)) for row in results]

@tool
def book_excursion(recommendation_id: int) -> str:
    """Book an excursion by its recommendation ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE trip_recommendations SET booked = 1 WHERE id = ?", (recommendation_id,))
    conn.commit()
    if cursor.rowcount > 0:
        conn.close()
        return f"Trip recommendation {recommendation_id} successfully booked."
    else:
        conn.close()
        return f"No trip recommendation found with ID {recommendation_id}."

@tool
def update_excursion(recommendation_id: int, details: str) -> str:
    """Update a trip recommendation's details by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE trip_recommendations SET details = ? WHERE id = ?", (details, recommendation_id))
    conn.commit()
    if cursor.rowcount > 0:
        conn.close()
        return f"Trip recommendation {recommendation_id} successfully updated."
    else:
        conn.close()
        return f"No trip recommendation found with ID {recommendation_id}."

@tool
def cancel_excursion(recommendation_id: int) -> str:
    """Cancel a trip recommendation by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE trip_recommendations SET booked = 0 WHERE id = ?", (recommendation_id,))
    conn.commit()
    if cursor.rowcount > 0:
        conn.close()
        return f"Trip recommendation {recommendation_id} successfully cancelled."
    else:
        conn.close()
        return f"No trip recommendation found with ID {recommendation_id}."