import sqlite3

conn = sqlite3.connect('sas_monitor.db')
cursor = conn.cursor()

print("=== Table Row Counts ===")
cursor.execute('SELECT COUNT(*) FROM ticket_summary')
print(f'ticket_summary rows: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM known_tickets')
print(f'known_tickets rows: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM availability_history')
print(f'availability_history rows: {cursor.fetchone()[0]}')

print("\n=== Sample from ticket_summary ===")
cursor.execute('SELECT * FROM ticket_summary LIMIT 3')
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print("⚠️ ticket_summary is EMPTY!")

conn.close()
