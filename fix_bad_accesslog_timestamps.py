#!/usr/bin/env python3
import sqlite3
import re
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'fastag.db')

# Regex for valid timestamp formats
VALID_PATTERNS = [
    re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'),  # YYYY-MM-DD HH:MM:SS
    re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'),   # YYYY-MM-DDTHH:MM:SS
    re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'),  # YYYY-MM-DDTHH:MM:SSZ
]

def is_valid_timestamp(ts):
    if not ts:
        return False
    for pat in VALID_PATTERNS:
        if pat.match(ts):
            return True
    return False

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, timestamp FROM access_logs")
    bad_rows = [(row[0], row[1]) for row in c.fetchall() if not is_valid_timestamp(row[1])]
    if not bad_rows:
        print("No bad timestamps found in access_logs.")
        return
    print(f"Found {len(bad_rows)} bad timestamp(s) in access_logs:")
    for row_id, ts in bad_rows:
        print(f"  id={row_id}, timestamp='{ts}'")
    # Non-interactive: just delete bad rows
    for row_id, ts in bad_rows:
        print(f"Deleting row id={row_id} with bad timestamp '{ts}'...")
        c.execute("DELETE FROM access_logs WHERE id = ?", (row_id,))
    conn.commit()
    print(f"Deleted {len(bad_rows)} bad row(s) from access_logs.")
    conn.close()

if __name__ == "__main__":
    main() 