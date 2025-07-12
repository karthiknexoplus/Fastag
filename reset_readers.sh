#!/bin/bash

# Script to reset the readers table and add two readers with IDs 1 and 2
DB_PATH="instance/fastag.db"

# Prompt for details or use defaults
read -p "Enter Reader 1 IP [192.168.1.101]: " R1_IP
R1_IP=${R1_IP:-192.168.1.101}
read -p "Enter Reader 1 Lane ID [1]: " R1_LANE
R1_LANE=${R1_LANE:-1}
read -p "Enter Reader 1 Type [entry]: " R1_TYPE
R1_TYPE=${R1_TYPE:-entry}

read -p "Enter Reader 2 IP [192.168.1.102]: " R2_IP
R2_IP=${R2_IP:-192.168.1.102}
read -p "Enter Reader 2 Lane ID [2]: " R2_LANE
R2_LANE=${R2_LANE:-2}
read -p "Enter Reader 2 Type [exit]: " R2_TYPE
R2_TYPE=${R2_TYPE:-exit}

if [ ! -f "$DB_PATH" ]; then
  echo "❌ Database not found at $DB_PATH."
  exit 1
fi

sqlite3 "$DB_PATH" <<EOF
DELETE FROM readers;
DELETE FROM sqlite_sequence WHERE name='readers';
INSERT INTO readers (reader_ip, lane_id, type) VALUES ('$R1_IP', $R1_LANE, '$R1_TYPE');
INSERT INTO readers (reader_ip, lane_id, type) VALUES ('$R2_IP', $R2_LANE, '$R2_TYPE');
EOF

echo "✅ Readers table reset. Current readers:"
sqlite3 "$DB_PATH" "SELECT id, reader_ip, lane_id, type FROM readers;" 