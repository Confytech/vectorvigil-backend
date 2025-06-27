import sqlite3
import os

# Make sure the instance directory exists
os.makedirs('instance', exist_ok=True)

# Connect to the database
conn = sqlite3.connect('instance/vectorvigil.db')
c = conn.cursor()

# Create the predictions table with location support
c.execute('''
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rainfall REAL,
    temperature REAL,
    humidity REAL,
    latitude REAL,
    longitude REAL,
    prediction INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("✅ Database initialized with predictions table including location fields.")

