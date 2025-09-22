# src/tools/car_rental_tools.py
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
def search_car_rentals(
    location: Optional[str] = None,
    name: Optional[str] = None,
    price_tier: Optional[str] = None,
    start_date: Optional[Union[datetime, date]] = None,
    end_date: Optional[Union[datetime, date]] = None,
) -> list[dict]:
    """Search for car rentals based on location, name, price tier, start date, and end date."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT * FROM car_rentals WHERE 1=1"
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
def book_car_rental(rental_id: int) -> str:
    """Book a car rental by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE car_rentals SET booked = 1 WHERE id = ?", (rental_id,))
    conn.commit()
    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully booked."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."

@tool
def update_car_rental(
    rental_id: int,
    start_date: Optional[Union[datetime, date]] = None,
    end_date: Optional[Union[datetime, date]] = None,
) -> str:
    """Update a car rental's start and end dates by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if start_date:
        cursor.execute("UPDATE car_rentals SET start_date = ? WHERE id = ?", (start_date, rental_id))
    if end_date:
        cursor.execute("UPDATE car_rentals SET end_date = ? WHERE id = ?", (end_date, rental_id))
    conn.commit()
    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully updated."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."

@tool
def cancel_car_rental(rental_id: int) -> str:
    """Cancel a car rental by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE car_rentals SET booked = 0 WHERE id = ?", (rental_id,))
    conn.commit()
    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully cancelled."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."