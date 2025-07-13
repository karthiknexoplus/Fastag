import sqlite3
import os

db_path = os.path.join('instance', 'fastag.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Visitor categories
table1 = '''
CREATE TABLE IF NOT EXISTS visitor_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
'''
c.execute(table1)

# Visitors
table2 = '''
CREATE TABLE IF NOT EXISTS visitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mobile TEXT,
    beneficiary_id INTEGER,
    category_id INTEGER,
    entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    entry_image_path TEXT,
    exit_time DATETIME,
    exit_image_path TEXT,
    status TEXT DEFAULT 'in',
    FOREIGN KEY (beneficiary_id) REFERENCES kyc_users(id),
    FOREIGN KEY (category_id) REFERENCES visitor_categories(id)
)
'''
c.execute(table2)

conn.commit()
conn.close()
print("Visitor tables created.") 