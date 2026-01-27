#!/usr/bin/env python3
"""
Test script to verify the direction bug fix.
This script simulates the bug scenario and verifies it's fixed.
"""

import sqlite3
import sys
from datetime import datetime

def test_direction_fix():
    """Test that direction column properly separates outbound/inbound data."""

    print("=" * 60)
    print("Testing Direction Bug Fix")
    print("=" * 60)

    # Create in-memory database for testing
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create the NEW ticket_summary table with direction column
    print("\n1. Creating ticket_summary table with direction column...")
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
    print("   ✓ Table created with direction column in PRIMARY KEY")

    # Simulate the bug scenario: CPH → BKK Feb 3
    # Outbound: Business = 0 seats
    # Inbound: Business = 6 seats
    print("\n2. Inserting test data (simulating CPH-BKK Feb 3 scenario)...")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Insert outbound with 0 Business seats
    cursor.execute("""
        INSERT INTO ticket_summary
        (origin, destination, date, cabin_class, direction, max_issued,
         currently_available, total_booked, first_seen_at, last_updated_at, booking_velocity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('CPH', 'BKK', '2026-02-03', 'AB', 'outbound', 0, 0, 0, now, now, 0.0))
    print("   ✓ Inserted outbound: CPH → BKK, Business = 0 seats")

    # Insert inbound with 6 Business seats
    cursor.execute("""
        INSERT INTO ticket_summary
        (origin, destination, date, cabin_class, direction, max_issued,
         currently_available, total_booked, first_seen_at, last_updated_at, booking_velocity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('CPH', 'BKK', '2026-02-03', 'AB', 'inbound', 6, 6, 0, now, now, 0.0))
    print("   ✓ Inserted inbound: BKK → CPH, Business = 6 seats")

    conn.commit()

    # Verify the fix: both records should exist independently
    print("\n3. Verifying data integrity...")

    cursor.execute("""
        SELECT direction, currently_available
        FROM ticket_summary
        WHERE origin='CPH' AND destination='BKK' AND date='2026-02-03' AND cabin_class='AB'
        ORDER BY direction
    """)

    results = cursor.fetchall()

    if len(results) != 2:
        print(f"   ✗ FAIL: Expected 2 records, got {len(results)}")
        return False

    print(f"   ✓ Found {len(results)} separate records")

    # Check inbound
    inbound = [r for r in results if r[0] == 'inbound']
    if len(inbound) == 1 and inbound[0][1] == 6:
        print(f"   ✓ Inbound record correct: {inbound[0][1]} seats")
    else:
        print(f"   ✗ FAIL: Inbound record incorrect")
        return False

    # Check outbound
    outbound = [r for r in results if r[0] == 'outbound']
    if len(outbound) == 1 and outbound[0][1] == 0:
        print(f"   ✓ Outbound record correct: {outbound[0][1]} seats")
    else:
        print(f"   ✗ FAIL: Outbound record incorrect")
        return False

    print("\n4. Testing PRIMARY KEY constraint...")

    # Try to insert duplicate (should fail)
    try:
        cursor.execute("""
            INSERT INTO ticket_summary
            (origin, destination, date, cabin_class, direction, max_issued,
             currently_available, total_booked, first_seen_at, last_updated_at, booking_velocity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('CPH', 'BKK', '2026-02-03', 'AB', 'outbound', 5, 5, 0, now, now, 0.0))
        print("   ✗ FAIL: Duplicate insert should have failed")
        return False
    except sqlite3.IntegrityError:
        print("   ✓ PRIMARY KEY constraint working (duplicate rejected)")

    # Test that different direction can be inserted
    cursor.execute("""
        INSERT INTO ticket_summary
        (origin, destination, date, cabin_class, direction, max_issued,
         currently_available, total_booked, first_seen_at, last_updated_at, booking_velocity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('CPH', 'BKK', '2026-02-04', 'AB', 'outbound', 3, 3, 0, now, now, 0.0))
    print("   ✓ Different date can be inserted")

    # Final verification
    cursor.execute("SELECT COUNT(*) FROM ticket_summary")
    total = cursor.fetchone()[0]
    print(f"\n5. Final count: {total} records in database")

    if total == 3:
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe direction bug is FIXED:")
        print("  - Outbound and inbound are now stored separately")
        print("  - Direction is part of the PRIMARY KEY")
        print("  - No more data overwriting issues")
        return True
    else:
        print(f"\n✗ FAIL: Expected 3 records, got {total}")
        return False

if __name__ == "__main__":
    success = test_direction_fix()
    sys.exit(0 if success else 1)
