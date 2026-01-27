import sqlite3

conn = sqlite3.connect('data/sas_monitor.db')
cursor = conn.cursor()

print("=== CPH Routes in database ===")
cursor.execute("SELECT origin, destination, COUNT(*) FROM ticket_summary WHERE origin='CPH' GROUP BY origin, destination")
for row in cursor.fetchall():
    print(f"{row[0]} -> {row[1]}: {row[2]} tickets")

print("\n=== All Routes Summary ===")
cursor.execute("SELECT origin, destination, COUNT(*) FROM ticket_summary GROUP BY origin, destination")
all_routes = cursor.fetchall()
print(f"Total unique routes: {len(all_routes)}")
for row in all_routes:
    print(f"{row[0]} -> {row[1]}: {row[2]} tickets")

conn.close()
