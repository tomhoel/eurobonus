import sqlite3

conn = sqlite3.connect('data/sas_monitor.db')

# Check if table exists
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ticket_notification_log'")
result = cursor.fetchone()
print('Table exists:', result is not None)

if result:
    print('Table name:', result[0])
    cursor = conn.execute('PRAGMA table_info(ticket_notification_log)')
    print('Columns:', [row[1] for row in cursor.fetchall()])

# Show all tables
print('\nAll tables in database:')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for row in cursor.fetchall():
    print(' -', row[0])

conn.close()
