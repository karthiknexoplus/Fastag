#!/bin/bash

# Script to reset the IDs of the first two readers to 1 and 2, without deleting other data
DB_PATH="instance/fastag.db"

if [ ! -f "$DB_PATH" ]; then
  echo "❌ Database not found at $DB_PATH."
  exit 1
fi

# Get the current IDs of the first two readers (ordered by id)
IDS=($(sqlite3 "$DB_PATH" "SELECT id FROM readers ORDER BY id ASC LIMIT 2;"))

if [ ${#IDS[@]} -lt 2 ]; then
  echo "❌ Less than two readers found in the database."
  exit 1
fi

FIRST_ID=${IDS[0]}
SECOND_ID=${IDS[1]}

# If either is already 1 or 2, temporarily set to a high unused value to avoid unique constraint errors
if [ "$FIRST_ID" = "1" ] || [ "$FIRST_ID" = "2" ]; then
  sqlite3 "$DB_PATH" "UPDATE readers SET id = 1001 WHERE id = $FIRST_ID;"
  FIRST_ID=1001
fi
if [ "$SECOND_ID" = "1" ] || [ "$SECOND_ID" = "2" ]; then
  sqlite3 "$DB_PATH" "UPDATE readers SET id = 1002 WHERE id = $SECOND_ID;"
  SECOND_ID=1002
fi

# Now set the IDs to 1 and 2
sqlite3 "$DB_PATH" "UPDATE readers SET id = 1 WHERE id = $FIRST_ID;"
sqlite3 "$DB_PATH" "UPDATE readers SET id = 2 WHERE id = $SECOND_ID;"

echo "✅ Reader IDs reset. Current readers:"
sqlite3 "$DB_PATH" "SELECT id, reader_ip, mac_address, lane_id, type FROM readers ORDER BY id;" 