#!/usr/bin/env python3
"""
Migration script to add direction column to ticket_summary table.

This script:
1. Creates a backup of the existing ticket_summary table
2. Creates a new ticket_summary table with direction column
3. Migrates existing data (defaulting direction to 'outbound')
4. Drops the old table

Usage:
    python migrate_add_direction.py
    python migrate_add_direction.py --db-path custom_path.db
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def migrate_database(db_path: str):
    """Add direction column to ticket_summary table."""

    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        sys.exit(1)

    print(f"Starting migration for: {db_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='ticket_summary'
        """)
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            print("✓ Table 'ticket_summary' does not exist yet - no migration needed")
            print("  The table will be created with the direction column when the monitor runs")
            return

        # Check if migration is needed
        cursor.execute("PRAGMA table_info(ticket_summary)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'direction' in columns:
            print("✓ Migration already applied - 'direction' column exists")
            return

        print("\n1. Creating backup table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_summary_backup AS
            SELECT * FROM ticket_summary
        """)

        # Get count of records
        cursor.execute("SELECT COUNT(*) FROM ticket_summary")
        record_count = cursor.fetchone()[0]
        print(f"   Backed up {record_count} records")

        print("\n2. Creating new ticket_summary table with direction column...")
        cursor.execute("DROP TABLE IF EXISTS ticket_summary")
        cursor.execute("""
            CREATE TABLE ticket_summary (
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                cabin_class TEXT NOT NULL,
                direction TEXT NOT NULL,
                max_issued INTEGER NOT NULL,
                currently_available INTEGER NOT NULL,
                total_booked INTEGER NOT NULL,
                first_seen_at TIMESTAMP NOT NULL,
                last_updated_at TIMESTAMP NOT NULL,
                last_decrease_at TIMESTAMP,
                booking_velocity REAL DEFAULT 0.0,
                PRIMARY KEY (origin, destination, date, cabin_class, direction)
            )
        """)

        print("\n3. Migrating data from backup...")
        print("   Note: All existing records will be assigned direction='outbound'")
        print("   After migration completes, run the monitor to populate inbound data")

        cursor.execute("""
            INSERT INTO ticket_summary
            (origin, destination, date, cabin_class, direction,
             max_issued, currently_available, total_booked,
             first_seen_at, last_updated_at, last_decrease_at, booking_velocity)
            SELECT
                origin, destination, date, cabin_class, 'outbound',
                max_issued, currently_available, total_booked,
                first_seen_at, last_updated_at, last_decrease_at, booking_velocity
            FROM ticket_summary_backup
        """)

        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM ticket_summary")
        new_count = cursor.fetchone()[0]
        print(f"   Migrated {new_count} records")

        if new_count != record_count:
            raise Exception(f"Record count mismatch! Original: {record_count}, New: {new_count}")

        print("\n4. Recreating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticket_summary_route
            ON ticket_summary(origin, destination)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticket_summary_velocity
            ON ticket_summary(booking_velocity DESC)
        """)

        print("\n5. Dropping backup table...")
        cursor.execute("DROP TABLE ticket_summary_backup")

        conn.commit()

        print("\n✓ Migration completed successfully!")
        print(f"\nSummary:")
        print(f"  - Migrated {new_count} records")
        print(f"  - All existing records set to direction='outbound'")
        print(f"  - Primary key now includes direction")
        print(f"\nNext steps:")
        print(f"  1. Run the monitor to populate inbound flight data")
        print(f"  2. Check /catalogue in Telegram to see direction-separated data")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("Rolling back changes...")
        conn.rollback()

        # Try to restore from backup if it exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='ticket_summary_backup'
        """)
        if cursor.fetchone():
            print("Restoring from backup...")
            cursor.execute("DROP TABLE IF EXISTS ticket_summary")
            cursor.execute("""
                CREATE TABLE ticket_summary AS
                SELECT * FROM ticket_summary_backup
            """)
            cursor.execute("DROP TABLE ticket_summary_backup")
            conn.commit()
            print("Restored original table from backup")

        sys.exit(1)

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate ticket_summary table to include direction column",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_add_direction.py
  python migrate_add_direction.py --db-path /path/to/sas_monitor.db

Note: This script will:
  - Create a backup before migration
  - Set all existing records to direction='outbound'
  - Require the monitor to run again to populate 'inbound' data
        """
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="sas_monitor.db",
        help="Path to SQLite database file (default: sas_monitor.db)"
    )

    args = parser.parse_args()

    migrate_database(args.db_path)


if __name__ == "__main__":
    main()
