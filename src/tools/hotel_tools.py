# src/tools/hotel_tools.py
import sqlite3
import os
from datetime import date, datetime
from typing import Optional, Union
from langchain_core.tools import tool

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # .../src/tools
_SRC_DIR = os.path.dirname(_CURRENT_DIR)                 # .../src
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)                # .../
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "db", "travel2.sqlite")
DB_PATH = os.getenv("DB_PATH", _DEFAULT_DB_PATH)

@tool
def search_hotels(
    location: Optional[str] = None,
    name: Optional[str] = None,
    price_tier: Optional[str] = None,
    checkin_date: Optional[Union[datetime, date]] = None,
    checkout_date: Optional[Union[datetime, date]] = None,
) -> list[dict]:
    """Search for hotels based on location, name, price tier, check-in date, and check-out date."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT * FROM hotels WHERE 1=1"
    params = []
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return [dict(zip([column[0] for column in cursor.description], row)) for row in results]

@tool
def book_hotel(hotel_id: int) -> str:
    """Book a hotel by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE hotels SET booked = 1 WHERE id = ?", (hotel_id,))
    conn.commit()
    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully booked."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."

@tool
def update_hotel(
    hotel_id: int,
    checkin_date: Optional[Union[datetime, date]] = None,
    checkout_date: Optional[Union[datetime, date]] = None,
) -> str:
    """Update a hotel's check-in and check-out dates by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if checkin_date:
        cursor.execute("UPDATE hotels SET checkin_date = ? WHERE id = ?", (checkin_date, hotel_id))
    if checkout_date:
        cursor.execute("UPDATE hotels SET checkout_date = ? WHERE id = ?", (checkout_date, hotel_id))
    conn.commit()
    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully updated."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."

@tool
def cancel_hotel(hotel_id: int) -> str:
    """Cancel a hotel by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE hotels SET booked = 0 WHERE id = ?", (hotel_id,))
    conn.commit()
    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully cancelled."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."