import sqlite3

conn = sqlite3.connect('data/sas_monitor.db')

# Create the table
conn.execute("""
    CREATE TABLE IF NOT EXISTS ticket_notification_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        date TEXT NOT NULL,
        cabin_class TEXT NOT NULL,
        notification_type TEXT NOT NULL,
        seats_value INTEGER,
        notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(origin, destination, date, cabin_class, notification_type, notified_at)
    )
""")

# Create the index
conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_ticket_notification
    ON ticket_notification_log(origin, destination, date, cabin_class, notification_type)
""")

conn.commit()
print("✅ Table created successfully!")
conn.close()
