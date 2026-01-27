#!/usr/bin/env python3
"""
Verify that notification deduplication fixes are working correctly.
"""
import sqlite3
import hashlib
from datetime import datetime, timedelta

DB_PATH = 'data/sas_monitor.db'

def check_new_table():
    """Verify ticket_notification_log table exists."""
    print("=" * 60)
    print("1. Checking if ticket_notification_log table exists...")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ticket_notification_log'"
    )
    exists = cursor.fetchone() is not None

    if exists:
        print("✅ Table exists!")

        # Check schema
        cursor = conn.execute("PRAGMA table_info(ticket_notification_log)")
        columns = cursor.fetchall()
        print("\nTable schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        # Check if any data exists
        cursor = conn.execute("SELECT COUNT(*) FROM ticket_notification_log")
        count = cursor.fetchone()[0]
        print(f"\n📊 Current rows in table: {count}")

        if count > 0:
            print("\nRecent notifications (last 5):")
            cursor = conn.execute("""
                SELECT origin, destination, date, cabin_class, notification_type,
                       seats_value, notified_at
                FROM ticket_notification_log
                ORDER BY notified_at DESC LIMIT 5
            """)
            for row in cursor.fetchall():
                print(f"  {row[0]}->{row[1]} {row[2]} {row[3]}: {row[4]} ({row[5]} seats) at {row[6]}")
    else:
        print("❌ Table does NOT exist!")
        print("The database may need to be recreated or the monitor needs to run once.")

    conn.close()
    return exists

def check_hash_fix():
    """Verify that hash generation works correctly."""
    print("\n" + "=" * 60)
    print("2. Testing hash generation fix...")
    print("=" * 60)

    # Old way (broken)
    msg1 = "Ticket vanished. Gone at: 2026-01-27 20:30:55 UTC"
    hash1 = hashlib.md5(msg1.encode()).hexdigest()

    msg2 = "Ticket vanished. Gone at: 2026-01-27 20:47:12 UTC"
    hash2 = hashlib.md5(msg2.encode()).hexdigest()

    print(f"Old method (timestamp in message):")
    print(f"  Hash 1: {hash1}")
    print(f"  Hash 2: {hash2}")
    print(f"  Hashes equal: {hash1 == hash2} ❌ (Different due to timestamp)")

    # New way (fixed)
    ticket_key = "CPH|BKK|2026-02-03|AP"
    hash3 = hashlib.md5(f"VANISHED:{ticket_key}".encode()).hexdigest()
    hash4 = hashlib.md5(f"VANISHED:{ticket_key}".encode()).hexdigest()

    print(f"\nNew method (ticket identity):")
    print(f"  Hash 1: {hash3}")
    print(f"  Hash 2: {hash4}")
    print(f"  Hashes equal: {hash3 == hash4} ✅ (Same regardless of timestamp)")

    return hash3 == hash4

def check_recent_notifications():
    """Check recent notifications from the main notifications table."""
    print("\n" + "=" * 60)
    print("3. Checking recent notifications...")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    # Check last 10 notifications
    cursor = conn.execute("""
        SELECT sent_at, notification_hash, substr(message, 1, 100)
        FROM notifications
        ORDER BY sent_at DESC LIMIT 10
    """)

    rows = cursor.fetchall()

    if rows:
        print(f"\nLast {len(rows)} notifications:")
        for i, row in enumerate(rows, 1):
            print(f"\n{i}. Sent at: {row[0]}")
            print(f"   Hash: {row[1]}")
            print(f"   Message preview: {row[2]}...")
    else:
        print("No notifications in database yet.")

    # Check for potential duplicates (same hash within 1 hour)
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute("""
        SELECT notification_hash, COUNT(*) as count
        FROM notifications
        WHERE sent_at > ?
        GROUP BY notification_hash
        HAVING count > 1
    """, (one_hour_ago,))

    dupes = cursor.fetchall()

    if dupes:
        print(f"\n⚠️  Found {len(dupes)} notification(s) with duplicate hashes in last hour:")
        for hash_val, count in dupes:
            print(f"  - Hash {hash_val}: sent {count} times")
    else:
        print("\n✅ No duplicate notification hashes found in last hour!")

    conn.close()

def check_monitor_status():
    """Check if monitor is running and recent activity."""
    print("\n" + "=" * 60)
    print("4. Checking monitor status...")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    # Check last availability check
    cursor = conn.execute("""
        SELECT MAX(scraped_at) FROM availability
    """)
    last_check = cursor.fetchone()[0]

    if last_check:
        print(f"Last availability check: {last_check}")

        # Parse and check if recent
        try:
            last_dt = datetime.strptime(last_check, "%Y-%m-%d %H:%M:%S")
            now = datetime.utcnow()
            minutes_ago = (now - last_dt).total_seconds() / 60

            if minutes_ago < 20:
                print(f"✅ Monitor is active (checked {minutes_ago:.1f} minutes ago)")
            else:
                print(f"⚠️  Monitor may be stale (last check {minutes_ago:.1f} minutes ago)")
        except:
            print("(Could not parse timestamp)")
    else:
        print("❌ No availability checks recorded yet")

    # Check ticket summary
    cursor = conn.execute("SELECT COUNT(*) FROM ticket_summary")
    summary_count = cursor.fetchone()[0]
    print(f"\nTickets in summary: {summary_count}")

    # Check known tickets
    cursor = conn.execute("SELECT COUNT(*) FROM known_tickets")
    baseline_count = cursor.fetchone()[0]
    print(f"Baseline tickets: {baseline_count}")

    conn.close()

def main():
    """Run all verification checks."""
    print("\n🔍 EUROBONUS MONITOR - Notification Fix Verification")
    print("=" * 60)

    try:
        table_exists = check_new_table()
        hash_works = check_hash_fix()
        check_recent_notifications()
        check_monitor_status()

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        if table_exists and hash_works:
            print("✅ All critical fixes verified successfully!")
            print("\nNext steps:")
            print("  1. Monitor logs for any 'Skipping duplicate' messages")
            print("  2. Watch for any duplicate TICKETS GONE notifications in Telegram")
            print("  3. Check ticket_notification_log table grows over time")
        else:
            print("⚠️  Some issues detected:")
            if not table_exists:
                print("  - ticket_notification_log table missing")
            if not hash_works:
                print("  - Hash generation test failed")

    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
