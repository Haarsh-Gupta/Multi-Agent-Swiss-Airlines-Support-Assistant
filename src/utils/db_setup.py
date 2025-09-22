# src/utils/db_setup.py
import os
import shutil
import sqlite3
import pandas as pd
import requests
import pytz
from datetime import datetime
import streamlit as st

# --- Path Correction ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_CURRENT_DIR)
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)
DB_DIR = os.path.join(_PROJECT_ROOT, "db")

@st.cache_resource
def setup_database():
    """Downloads, backs up, and updates the SQLite database inside the root 'db' folder."""
    db_url = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
    local_file = "travel2.sqlite"
    backup_file = "travel2.backup.sqlite"
    
    os.makedirs(DB_DIR, exist_ok=True) 
    
    local_path = os.path.join(DB_DIR, local_file)
    backup_path = os.path.join(DB_DIR, backup_file)

    if not os.path.exists(local_path):
        with st.spinner(f"Database not found. Downloading to {local_path}..."):
            response = requests.get(db_url)
            response.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(response.content)
            shutil.copy(local_path, backup_path)
            st.success("Database download and backup complete.")
    
    return _update_dates(local_path, backup_path)

def _update_dates(db_path, backup_path):
    """Updates flight and booking dates in the database to be current."""
    shutil.copy(backup_path, db_path)
    conn = sqlite3.connect(db_path)
    
    try:
        tables_df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
        tables = tables_df["name"].tolist()
        tdf = {t: pd.read_sql(f"SELECT * FROM {t}", conn) for t in tables}

        if "flights" in tdf and not tdf["flights"].empty:
            # FIX: Convert actual_departure to datetime, coercing errors to NaT
            departures = pd.to_datetime(tdf["flights"]["actual_departure"], errors='coerce')
            
            # Now, find the maximum valid datetime, which will be ignored if all are NaT
            example_time = departures.max()
            
            if pd.notna(example_time):
                current_time = pd.to_datetime("now").tz_localize(example_time.tz)
                time_diff = current_time - example_time

                # Apply the fix to other date columns as well for robustness
                tdf["bookings"]["book_date"] = (
                    pd.to_datetime(tdf["bookings"]["book_date"], errors='coerce', utc=True) + time_diff
                )

                datetime_columns = ["scheduled_departure", "scheduled_arrival", "actual_departure", "actual_arrival"]
                for column in datetime_columns:
                    # Coerce errors here too to handle any bad data
                    tdf["flights"][column] = (
                        pd.to_datetime(tdf["flights"][column], errors='coerce') + time_diff
                    )

                for table_name, df in tdf.items():
                    df.to_sql(table_name, conn, if_exists="replace", index=False)
                
                conn.commit()
    finally:
        conn.close()
        
    return db_path