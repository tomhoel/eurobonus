#!/usr/bin/env python3
"""
SAS EuroBonus Award Monitor - Europe to Asia Routes
Monitors award seat availability and sends Telegram notifications.

Routes: Oslo, Paris, Copenhagen, Amsterdam → Thailand, Japan, China, Vietnam, Singapore
Only notifies when NEW tickets are released (not existing availability).

Usage:
    python sas_monitor.py --init-baseline  # First-time: establish baseline (no notifications)
    python sas_monitor.py                  # Run continuous monitoring
    python sas_monitor.py --once           # Run single check and exit
    python sas_monitor.py --test           # Test API connectivity
"""

import argparse
import hashlib
import json
import logging
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class Config:
    """Monitor configuration."""
    # API settings
    base_url: str = "https://www.sas.no/bff/award-finder/destinations/v1"
    market: str = "no-no"
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    cookies: str = ""
    
    # Timing
    poll_interval: int = 900  # 15 minutes
    request_delay: float = 2.0  # Delay between route checks
    
    # Telegram (set via environment or config file)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # Database
    db_path: str = "sas_monitor.db"
    
    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load config from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)


# Europe to Asia Routes Configuration
# Origins: Oslo, Paris, Copenhagen, Amsterdam
# Destinations: Thailand, Japan, China, Vietnam, Singapore
EUROPE_AIRPORTS = ["OSL", "CDG", "CPH", "AMS"]
ASIA_AIRPORTS = [
    "BKK",  # Bangkok, Thailand
    "NRT",  # Tokyo Narita, Japan
    "HND",  # Tokyo Haneda, Japan
    "KIX",  # Osaka, Japan
    "PVG",  # Shanghai, China
    "PEK",  # Beijing, China
    "SGN",  # Ho Chi Minh City, Vietnam
    "HAN",  # Hanoi, Vietnam
    "SIN",  # Singapore
]
CABIN_CLASSES = ["AG", "AP", "AB"]  # Economy, Premium, Business

# Legacy aliases for backwards compatibility
ORIGINS = EUROPE_AIRPORTS
DESTINATIONS = ASIA_AIRPORTS

# Generate all route combinations (both directions)
# Europe → Asia (36 routes) + Asia → Europe (36 routes) = 72 routes
DEFAULT_ROUTES = []

# Europe → Asia (outbound)
for origin in EUROPE_AIRPORTS:
    for dest in ASIA_AIRPORTS:
        DEFAULT_ROUTES.append({
            "origin": origin,
            "destination": dest,
            "cabin_classes": CABIN_CLASSES,
            "direction": "outbound"
        })

# Asia → Europe (return)
for origin in ASIA_AIRPORTS:
    for dest in EUROPE_AIRPORTS:
        DEFAULT_ROUTES.append({
            "origin": origin, 
            "destination": dest,
            "cabin_classes": CABIN_CLASSES,
            "direction": "return"
        })


# ============================================================================
# Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ============================================================================
# SAS Award Finder API Client
# ============================================================================

class SASAwardAPI:
    """Client for SAS Award Finder API."""
    
    CABIN_CODES = {"AG": "Economy", "AP": "Premium", "AB": "Business"}
    
    def __init__(self, config: Config):
        self.base_url = config.base_url
        self.market = config.market
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.user_agent,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        })
        if config.cookies:
            self.session.headers.update({"Cookie": config.cookies})
    
    def get_destinations(self, origin: str) -> list:
        """Get all available destinations from an origin."""
        return self._request(origin=origin, availability=False)
    
    def get_availability(
        self,
        origin: str,
        destination: str = "",
        month: str = "",
        passengers: int = 1,
        direct: bool = False,
        cabin_class: str = ""
    ) -> list:
        """
        Query award availability.
        
        Args:
            origin: IATA code (e.g., 'OSL')
            destination: IATA code or empty for all
            month: YYYYMM format or empty for all months
            passengers: Number of travelers
            direct: Filter for direct flights only
            cabin_class: AG/AP/AB or empty for all
            
        Returns:
            List of destination availability objects
        """
        return self._request(
            origin=origin,
            destination=destination,
            month=month,
            passengers=passengers,
            direct=direct,
            cabin_class=cabin_class,
            availability=True
        )
    
    def _request(
        self,
        origin: str,
        destination: str = "",
        month: str = "",
        passengers: int = 1,
        direct: bool = False,
        cabin_class: str = "",
        availability: bool = True
    ) -> list:
        """Make API request with retry and exponential backoff."""
        params = {
            "market": self.market,
            "origin": origin,
            "destinations": destination,
            "selectedMonth": month,
            "passengers": passengers,
            "direct": str(direct).lower(),
            "availability": str(availability).lower(),
            "selectedFlightClass": cabin_class,
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(f"Request timeout for {origin}->{destination}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request timeout for {origin}->{destination} after {max_retries} retries")
                    return []
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"API request failed: {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API request failed after {max_retries} retries: {e}")
                    return []
            except json.JSONDecodeError:
                logger.error("Invalid JSON response")
                return []
        return []


# ============================================================================
# Database
# ============================================================================

class AvailabilityDatabase:
    """SQLite database for storing availability data."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
        # Enable WAL mode for concurrent access from monitor + bot
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=30000")
        self._init_tables()
    
    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                cabin_class TEXT NOT NULL,
                seats_available INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_route_date
            ON availability(origin, destination, date, cabin_class);

            CREATE TABLE IF NOT EXISTS known_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baseline_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                cabin_class TEXT NOT NULL,
                seats_available INTEGER NOT NULL,
                UNIQUE(origin, destination, date, cabin_class)
            );

            CREATE INDEX IF NOT EXISTS idx_known_route
            ON known_tickets(origin, destination, date, cabin_class);

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                cabin_class TEXT NOT NULL,
                seats INTEGER NOT NULL,
                message TEXT,
                notification_hash TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_notification_hash
            ON notifications(notification_hash, sent_at);

            CREATE TABLE IF NOT EXISTS ticket_summary (
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
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_summary_route
            ON ticket_summary(origin, destination);

            CREATE INDEX IF NOT EXISTS idx_ticket_summary_velocity
            ON ticket_summary(booking_velocity DESC);

            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active INTEGER DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_subscribers_active
            ON subscribers(active);

            CREATE TABLE IF NOT EXISTS ticket_sales_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                cabin_class TEXT NOT NULL,
                first_seen_at TIMESTAMP NOT NULL,
                sold_out_at TIMESTAMP NOT NULL,
                duration_hours REAL NOT NULL,
                max_seats INTEGER NOT NULL,
                avg_velocity REAL DEFAULT 0.0
            );

            CREATE INDEX IF NOT EXISTS idx_sales_history_duration
            ON ticket_sales_history(duration_hours ASC);

            CREATE INDEX IF NOT EXISTS idx_sales_history_velocity
            ON ticket_sales_history(avg_velocity DESC);

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
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_notification
            ON ticket_notification_log(origin, destination, date, cabin_class, notification_type);

            CREATE TABLE IF NOT EXISTS seat_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                cabin_class TEXT NOT NULL,
                direction TEXT DEFAULT 'outbound',
                previous_seats INTEGER NOT NULL,
                new_seats INTEGER NOT NULL,
                change_amount INTEGER NOT NULL,
                change_type TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_seat_changes_route
            ON seat_changes(origin, destination, date, cabin_class);

            CREATE INDEX IF NOT EXISTS idx_seat_changes_time
            ON seat_changes(changed_at DESC);
        """)
        self.conn.commit()
    
    def store_availability(self, origin: str, destination: str, 
                          date: str, cabin_class: str, seats: int):
        """Store current availability snapshot."""
        self.conn.execute(
            """INSERT INTO availability 
               (origin, destination, date, cabin_class, seats_available)
               VALUES (?, ?, ?, ?, ?)""",
            (origin, destination, date, cabin_class, seats)
        )
        self.conn.commit()
    
    def get_previous_availability(self, origin: str, destination: str,
                                  date: str, cabin_class: str) -> Optional[int]:
        """Get most recent availability for a route/date/class."""
        cursor = self.conn.execute(
            """SELECT seats_available FROM availability
               WHERE origin=? AND destination=? AND date=? AND cabin_class=?
               ORDER BY scraped_at DESC LIMIT 1""",
            (origin, destination, date, cabin_class)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    
    def log_notification(self, origin: str, destination: str, date: str,
                        cabin_class: str, seats: int, message: str,
                        notification_hash: str = None):
        """Log sent notification with optional hash for deduplication."""
        self.conn.execute(
            """INSERT INTO notifications
               (origin, destination, date, cabin_class, seats, message, notification_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (origin, destination, date, cabin_class, seats, message, notification_hash)
        )
        self.conn.commit()

    def was_recently_notified(self, message_hash: str, hours: int = 24) -> bool:
        """Check if a notification with this hash was sent recently."""
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.conn.execute(
            """SELECT COUNT(*) FROM notifications
               WHERE notification_hash = ? AND sent_at > ?""",
            (message_hash, cutoff_time)
        )
        return cursor.fetchone()[0] > 0

    def was_ticket_notified_recently(self, origin: str, destination: str,
                                     date: str, cabin: str,
                                     notification_type: str, hours: int = 24) -> bool:
        """Check if this specific ticket was notified about recently."""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.conn.execute(
            """SELECT COUNT(*) FROM ticket_notification_log
               WHERE origin=? AND destination=? AND date=? AND cabin_class=?
               AND notification_type=? AND notified_at > ?""",
            (origin, destination, date, cabin, notification_type, cutoff)
        )
        return cursor.fetchone()[0] > 0

    def log_ticket_notification(self, origin: str, destination: str,
                                date: str, cabin: str,
                                notification_type: str, seats_value: int):
        """Log that a notification was sent for this ticket."""
        try:
            self.conn.execute(
                """INSERT INTO ticket_notification_log
                   (origin, destination, date, cabin_class, notification_type, seats_value)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (origin, destination, date, cabin, notification_type, seats_value)
            )
            self.conn.commit()
        except Exception as e:
            # If duplicate (same ticket notified in same second), ignore
            if "UNIQUE constraint failed" not in str(e):
                logger.warning(f"Failed to log ticket notification: {e}")

    def store_baseline(self, origin: str, destination: str,
                      date: str, cabin_class: str, seats: int):
        """Store baseline ticket (for --init-baseline mode)."""
        self.conn.execute(
            """INSERT OR REPLACE INTO known_tickets
               (origin, destination, date, cabin_class, seats_available, baseline_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (origin, destination, date, cabin_class, seats)
        )
        self.conn.commit()

    def is_baseline_ticket(self, origin: str, destination: str,
                          date: str, cabin_class: str) -> bool:
        """Check if this ticket existed in the baseline."""
        cursor = self.conn.execute(
            """SELECT 1 FROM known_tickets
               WHERE origin=? AND destination=? AND date=? AND cabin_class=?""",
            (origin, destination, date, cabin_class)
        )
        return cursor.fetchone() is not None

    def get_baseline_count(self) -> int:
        """Get count of baseline tickets stored."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM known_tickets")
        return cursor.fetchone()[0]

    def get_ticket_summary(self, origin: str, destination: str,
                          date: str, cabin_class: str, direction: str = None) -> Optional[dict]:
        """Get ticket summary for a specific route/date/cabin/direction."""
        if direction:
            cursor = self.conn.execute(
                """SELECT max_issued, currently_available, total_booked,
                          first_seen_at, last_updated_at, last_decrease_at, booking_velocity
                   FROM ticket_summary
                   WHERE origin=? AND destination=? AND date=? AND cabin_class=? AND direction=?""",
                (origin, destination, date, cabin_class, direction)
            )
        else:
            # Legacy fallback: if no direction specified, try to get any matching record
            cursor = self.conn.execute(
                """SELECT max_issued, currently_available, total_booked,
                          first_seen_at, last_updated_at, last_decrease_at, booking_velocity
                   FROM ticket_summary
                   WHERE origin=? AND destination=? AND date=? AND cabin_class=?
                   LIMIT 1""",
                (origin, destination, date, cabin_class)
            )
        row = cursor.fetchone()
        if row:
            return {
                "max_issued": row[0],
                "currently_available": row[1],
                "total_booked": row[2],
                "first_seen_at": row[3],
                "last_updated_at": row[4],
                "last_decrease_at": row[5],
                "booking_velocity": row[6]
            }
        return None

    def upsert_ticket_summary(self, origin: str, destination: str, date: str,
                             cabin_class: str, current_seats: int,
                             previous_summary: Optional[dict] = None, direction: str = "outbound"):
        """Insert or update ticket summary with current availability."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.conn.cursor()
        
        try:
            if previous_summary is None:
                # First time seeing this ticket
                cursor.execute(
                    """INSERT INTO ticket_summary
                       (origin, destination, date, cabin_class, direction, max_issued,
                        currently_available, total_booked, first_seen_at,
                        last_updated_at, booking_velocity)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (origin, destination, date, cabin_class, direction, current_seats,
                     current_seats, 0, now, now, 0.0)
                )
            else:
                # Update existing
                new_max = max(previous_summary["max_issued"], current_seats)
                total_booked = new_max - current_seats

                # Calculate velocity if seats decreased
                velocity = previous_summary.get("booking_velocity", 0.0)
                last_decrease_at = previous_summary.get("last_decrease_at")

                if current_seats < previous_summary["currently_available"]:
                    # Seats decreased - calculate booking velocity
                    seats_booked = previous_summary["currently_available"] - current_seats
                    if last_decrease_at:
                        try:
                            last_dec_dt = datetime.strptime(last_decrease_at, "%Y-%m-%d %H:%M:%S")
                            now_dt = datetime.utcnow()
                            time_diff_hours = (now_dt - last_dec_dt).total_seconds() / 3600
                            # Guard against div-by-zero (minimum 3.6 seconds)
                            if time_diff_hours > 0.001:
                                velocity = seats_booked / time_diff_hours
                        except:
                            pass
                    last_decrease_at = now

                cursor.execute(
                    """UPDATE ticket_summary
                       SET max_issued=?, currently_available=?, total_booked=?,
                           last_updated_at=?, last_decrease_at=?, booking_velocity=?
                       WHERE origin=? AND destination=? AND date=? AND cabin_class=? AND direction=?""",
                    (new_max, current_seats, total_booked, now, last_decrease_at,
                     velocity, origin, destination, date, cabin_class, direction)
                )

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Transaction failed in upsert_ticket_summary: {e}")
            raise

    def get_notification_history(self, limit: int = 50, offset: int = 0,
                                 filter_type: str = "all") -> list:
        """
        Get notification history with pagination and filtering.

        Args:
            limit: Number of results to return (default 50)
            offset: Starting position (for pagination)
            filter_type: 'all', 'new', 'vanished', 'increase', 'decrease'

        Returns:
            List of tuples: (id, sent_at, origin, destination, date,
                            cabin_class, seats, message_preview)
        """
        # Base query
        query = """
            SELECT id, sent_at, origin, destination, date,
                   cabin_class, seats, substr(message, 1, 150) as message_preview
            FROM notifications
            WHERE 1=1
        """
        params = []

        # Apply filter based on notification type
        # We detect type from the message content
        if filter_type == "new":
            query += " AND message LIKE '%NEW TICKETS%'"
        elif filter_type == "vanished":
            query += " AND message LIKE '%TICKETS GONE%'"
        elif filter_type == "increase":
            query += " AND message LIKE '%SEATS BEING BOOKED%' AND message NOT LIKE '%GONE%'"
        elif filter_type == "decrease":
            query += " AND message LIKE '%SEATS BEING BOOKED%'"

        # Sort by most recent first
        query += " ORDER BY sent_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(query, params)
        return cursor.fetchall()

    def get_notification_count(self, filter_type: str = "all") -> int:
        """Get total count of notifications for pagination."""
        query = "SELECT COUNT(*) FROM notifications WHERE 1=1"

        if filter_type == "new":
            query += " AND message LIKE '%NEW TICKETS%'"
        elif filter_type == "vanished":
            query += " AND message LIKE '%TICKETS GONE%'"
        elif filter_type == "increase":
            query += " AND message LIKE '%SEATS BEING BOOKED%' AND message NOT LIKE '%GONE%'"
        elif filter_type == "decrease":
            query += " AND message LIKE '%SEATS BEING BOOKED%'"

        cursor = self.conn.execute(query)
        return cursor.fetchone()[0]

    def get_all_tracked_tickets(self, origin: Optional[str] = None,
                                destination: Optional[str] = None,
                                month: Optional[str] = None) -> list:
        """
        Get all tracked tickets from ticket_summary table.
        Returns list of tuples: (origin, destination, date, cabin_class, direction,
                                 max_issued, currently_available, total_booked,
                                 first_seen_at, booking_velocity)
        """
        query = """SELECT origin, destination, date, cabin_class, direction, max_issued,
                          currently_available, total_booked, first_seen_at, booking_velocity
                   FROM ticket_summary
                   WHERE 1=1"""
        params = []

        if origin:
            query += " AND origin=?"
            params.append(origin)
        if destination:
            query += " AND destination=?"
            params.append(destination)
        if month:
            query += " AND date LIKE ?"
            params.append(f"{month}%")

        query += " ORDER BY origin, destination, date, cabin_class, direction"

        cursor = self.conn.execute(query, params)
        return cursor.fetchall()

    def get_hot_tickets(self, limit: int = 15) -> list:
        """
        Get tickets with highest booking velocity.
        Returns list of tuples: (origin, destination, date, cabin_class, direction,
                                 currently_available, total_booked, booking_velocity)
        """
        cursor = self.conn.execute(
            """SELECT origin, destination, date, cabin_class, direction,
                      currently_available, total_booked, booking_velocity
               FROM ticket_summary
               WHERE booking_velocity > 0 AND currently_available > 0
               ORDER BY booking_velocity DESC
               LIMIT ?""",
            (limit,)
        )
        return cursor.fetchall()

    def log_seat_change(self, origin: str, destination: str, date: str,
                        cabin_class: str, previous_seats: int, new_seats: int,
                        direction: str = "outbound"):
        """Log a seat availability change for history tracking."""
        change_amount = new_seats - previous_seats
        if change_amount > 0:
            change_type = "increase"
        elif change_amount < 0:
            change_type = "decrease"
        else:
            return  # No change
        
        try:
            self.conn.execute(
                """INSERT INTO seat_changes 
                   (origin, destination, date, cabin_class, direction, previous_seats, 
                    new_seats, change_amount, change_type)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (origin, destination, date, cabin_class, direction, previous_seats, 
                 new_seats, change_amount, change_type)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log seat change: {e}")

    def get_recent_changes(self, origin: str = None, destination: str = None,
                           date: str = None, limit: int = 10) -> list:
        """
        Get recent seat changes for a route/date.
        Returns list of tuples: (changed_at, cabin_class, previous_seats, 
                                 new_seats, change_amount, change_type)
        """
        query = """SELECT changed_at, cabin_class, previous_seats, 
                          new_seats, change_amount, change_type
                   FROM seat_changes WHERE 1=1"""
        params = []
        
        if origin:
            query += " AND origin=?"
            params.append(origin)
        if destination:
            query += " AND destination=?"
            params.append(destination)
        if date:
            query += " AND date=?"
            params.append(date)
        
        query += " ORDER BY changed_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()

    def get_route_summary_with_changes(self, origin: str = None,
                                        destination: str = None) -> list:
        """
        Get ticket summary grouped by route with recent changes.
        Returns list of dicts with route info and change history.
        """
        # Get summaries
        query = """SELECT origin, destination, date, cabin_class, direction, max_issued,
                          currently_available, total_booked, first_seen_at
                   FROM ticket_summary WHERE 1=1"""
        params = []

        if origin:
            query += " AND origin=?"
            params.append(origin)
        if destination:
            query += " AND destination=?"
            params.append(destination)

        query += " ORDER BY origin, destination, date, cabin_class, direction"
        cursor = self.conn.execute(query, params)

        results = []
        for row in cursor.fetchall():
            ticket = {
                'origin': row[0],
                'destination': row[1],
                'date': row[2],
                'cabin_class': row[3],
                'direction': row[4],
                'max_issued': row[5],
                'currently_available': row[6],
                'total_booked': row[7],
                'first_seen_at': row[8],
                'changes': self.get_recent_changes(row[0], row[1], row[2], limit=5)
            }
            results.append(ticket)

        return results

    # Subscriber management methods
    def add_subscriber(self, chat_id: str, username: str = None, first_name: str = None) -> bool:
        """Add a new subscriber or reactivate existing one."""
        try:
            self.conn.execute(
                """INSERT INTO subscribers (chat_id, username, first_name, active)
                   VALUES (?, ?, ?, 1)
                   ON CONFLICT(chat_id) DO UPDATE SET
                   active=1, subscribed_at=CURRENT_TIMESTAMP""",
                (chat_id, username, first_name)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add subscriber: {e}")
            return False

    def remove_subscriber(self, chat_id: str) -> bool:
        """Deactivate a subscriber."""
        try:
            self.conn.execute(
                """UPDATE subscribers SET active=0 WHERE chat_id=?""",
                (chat_id,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to remove subscriber: {e}")
            return False

    def get_active_subscribers(self) -> list:
        """Get list of all active subscriber chat IDs."""
        cursor = self.conn.execute(
            """SELECT chat_id FROM subscribers WHERE active=1"""
        )
        return [row[0] for row in cursor.fetchall()]

    def is_subscribed(self, chat_id: str) -> bool:
        """Check if a chat_id is subscribed."""
        cursor = self.conn.execute(
            """SELECT active FROM subscribers WHERE chat_id=?""",
            (chat_id,)
        )
        row = cursor.fetchone()
        return row is not None and row[0] == 1

    def get_subscriber_count(self) -> int:
        """Get count of active subscribers."""
        cursor = self.conn.execute(
            """SELECT COUNT(*) FROM subscribers WHERE active=1"""
        )
        return cursor.fetchone()[0]

    # Sales history tracking
    def record_ticket_sold_out(self, origin: str, destination: str, date: str,
                               cabin_class: str, first_seen_at: str,
                               max_seats: int, avg_velocity: float):
        """Record when a ticket sells out completely."""
        sold_out_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate duration
        try:
            first_dt = datetime.strptime(first_seen_at, "%Y-%m-%d %H:%M:%S")
            sold_dt = datetime.strptime(sold_out_at, "%Y-%m-%d %H:%M:%S")
            duration_hours = (sold_dt - first_dt).total_seconds() / 3600
        except:
            duration_hours = 0.0

        self.conn.execute(
            """INSERT INTO ticket_sales_history
               (origin, destination, date, cabin_class, first_seen_at,
                sold_out_at, duration_hours, max_seats, avg_velocity)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (origin, destination, date, cabin_class, first_seen_at,
             sold_out_at, duration_hours, max_seats, avg_velocity)
        )
        self.conn.commit()

    def get_fastest_selling_tickets(self, limit: int = 15) -> list:
        """
        Get tickets that sold out fastest.
        Returns list of tuples: (origin, destination, date, cabin_class,
                                 duration_hours, max_seats, avg_velocity, sold_out_at)
        """
        cursor = self.conn.execute(
            """SELECT origin, destination, date, cabin_class,
                      duration_hours, max_seats, avg_velocity, sold_out_at
               FROM ticket_sales_history
               ORDER BY duration_hours ASC
               LIMIT ?""",
            (limit,)
        )
        return cursor.fetchall()

    def get_release_history(self, origin: str, destination: str, limit: int = 20) -> list:
        """
        Get the first-seen time for tickets on a route.
        Returns list of (date, cabin_class, seats, first_seen)
        """
        cursor = self.conn.execute(
            """SELECT date, cabin_class, seats_available, MIN(scraped_at) as first_seen
               FROM availability
               WHERE origin=? AND destination=?
               GROUP BY date, cabin_class
               ORDER BY first_seen DESC
               LIMIT ?""",
            (origin, destination, limit)
        )
        return cursor.fetchall()

    def get_best_bets(self, limit: int = 15) -> list:
        """
        Get routes with the highest current business class availability.
        Returns list of (origin, destination, date, seats)
        """
        # Get the latest availability snapshot for each route/date/class
        cursor = self.conn.execute(
            """SELECT origin, destination, date, seats_available
               FROM availability a
               WHERE cabin_class = 'AB' AND seats_available > 0
               AND scraped_at = (
                   SELECT MAX(scraped_at) FROM availability 
                   WHERE origin=a.origin AND destination=a.destination 
                   AND date=a.date AND cabin_class=a.cabin_class
               )
               ORDER BY seats_available DESC, date ASC
               LIMIT ?""",
            (limit,)
        )
        return cursor.fetchall()

    def get_stats(self) -> dict:
        """Get database statistics for status dashboard."""
        stats = {}

        # Total records
        cursor = self.conn.execute("SELECT COUNT(*) FROM availability")
        stats["total_records"] = cursor.fetchone()[0]

        # Last scraped time
        cursor = self.conn.execute("SELECT MAX(scraped_at) FROM availability")
        stats["last_scraped"] = cursor.fetchone()[0]

        # Unique routes
        cursor = self.conn.execute(
            "SELECT COUNT(DISTINCT origin || '-' || destination) FROM availability"
        )
        stats["unique_routes"] = cursor.fetchone()[0]

        # Baseline count
        cursor = self.conn.execute("SELECT COUNT(*) FROM known_tickets")
        stats["baseline_tickets"] = cursor.fetchone()[0]

        # Tracked tickets count
        cursor = self.conn.execute("SELECT COUNT(*) FROM ticket_summary")
        stats["tracked_tickets"] = cursor.fetchone()[0]

        # Notifications sent
        cursor = self.conn.execute("SELECT COUNT(*) FROM notifications")
        stats["notifications_sent"] = cursor.fetchone()[0]

        return stats

    def close(self):
        self.conn.close()


# ============================================================================
# Telegram Notifier
# ============================================================================

class TelegramNotifier:
    """Send notifications via Telegram bot."""

    def __init__(self, bot_token: str, chat_id: str = None):
        self.bot_token = bot_token
        self.chat_id = chat_id  # Legacy single chat_id (optional)
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token)

        if not self.enabled:
            logger.warning("Telegram notifications disabled (no token)")

    def send_message(self, text: str, chat_id: str = None, parse_mode: str = "HTML") -> bool:
        """Send a message to a specific chat or the configured default chat."""
        if not self.enabled:
            logger.info(f"[DRY RUN] Would send: {text[:100]}...")
            return False

        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            logger.warning("No chat_id specified for message")
            return False

        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": target_chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Telegram notification failed for chat {target_chat_id}: {e}")
            return False

    def broadcast_message(self, text: str, subscribers: list, parse_mode: str = "HTML") -> int:
        """
        Broadcast a message to multiple subscribers.
        Returns count of successful sends.
        """
        if not self.enabled:
            logger.info(f"[DRY RUN] Would broadcast to {len(subscribers)} subscribers")
            return 0

        success_count = 0
        for chat_id in subscribers:
            if self.send_message(text, chat_id=chat_id, parse_mode=parse_mode):
                success_count += 1
                time.sleep(0.05)  # Small delay to avoid rate limits

        logger.info(f"Broadcast sent to {success_count}/{len(subscribers)} subscribers")
        return success_count
    
    def format_availability_alert(
        self,
        origin: str,
        destination: str,
        date: str,
        cabin_class: str,
        seats: int,
        previous_seats: Optional[int],
        city_name: str = "",
        direction: str = "",
        discovered_at: str = ""
    ) -> str:
        """Format an availability alert message."""
        class_name = SASAwardAPI.CABIN_CODES.get(cabin_class, cabin_class)

        # Generate timestamp if not provided
        if not discovered_at:
            discovered_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Determine status
        if previous_seats is None:
            status_line = "🆕 <b>NEW RELEASE</b>"
        else:
            status_line = f"📈 <b>+{seats - previous_seats} more seats</b>"

        # Booking link
        booking_url = f"https://www.sas.no/award-finder?origin={origin}"

        dest_display = f"{destination}"
        if city_name:
            dest_display = f"{city_name} ({destination})"

        direction_text = f" ({direction})" if direction else ""

        return f"""🎫 <b>NEW BONUS TICKET RELEASED!</b>

✈️ <b>{origin} → {dest_display}</b>{direction_text}
📅 Date: {date}
💺 {class_name}: <b>{seats}</b> seat(s)

🕐 Found: {discovered_at}
{status_line}

<a href="{booking_url}">🔗 Book now on SAS</a>"""

    def format_vanishing_alert(
        self,
        origin: str,
        destination: str,
        date: str,
        cabin_class: str,
        previous_seats: int,
        city_name: str = "",
        direction: str = ""
    ) -> str:
        """Format a vanishing alert message."""
        class_name = SASAwardAPI.CABIN_CODES.get(cabin_class, cabin_class)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        dest_display = f"{city_name} ({destination})" if city_name else destination
        direction_text = f" ({direction})" if direction else ""

        return f"""💨 <b>TICKET VANISHED / BOOKED</b>

✈️ <b>{origin} → {dest_display}</b>{direction_text}
📅 Date: {date}
💺 {class_name}: was <b>{previous_seats}</b> seat(s)

🕐 Detected: {timestamp}
⚠️ <i>These seats are no longer available.</i>"""


# ============================================================================
# Main Monitor
# ============================================================================

class SASAwardMonitor:
    """Main monitoring orchestrator."""

    def __init__(self, config: Config, routes: list = None, baseline_mode: bool = False):
        self.config = config
        self.api = SASAwardAPI(config)
        self.db = AvailabilityDatabase(config.db_path)
        self.notifier = TelegramNotifier(
            config.telegram_bot_token,
            config.telegram_chat_id
        )
        self.routes = routes or DEFAULT_ROUTES
        self.baseline_mode = baseline_mode
    
    def check_route(self, origin: str, destination: str, cabin_classes: list) -> dict:
        """
        Check availability for a specific route.

        Returns:
            Dictionary with changes: {
                'new_tickets': [...],
                'seat_increases': [...],
                'seat_decreases': [...],
                'vanished': [...]
            }
        """
        logger.info(f"Checking {origin} → {destination} [{', '.join(cabin_classes)}]")

        changes = {
            'new_tickets': [],
            'seat_increases': [],
            'seat_decreases': [],
            'vanished': []
        }

        data = self.api.get_availability(origin=origin, destination=destination)

        if not data:
            logger.debug(f"No data for {origin} → {destination}")
            return changes

        dest_data = data[0]
        city_name = dest_data.get("cityName", "")

        # Process outbound and inbound availability
        for direction in ["outbound", "inbound"]:
            for avail in dest_data.get("availability", {}).get(direction, []):
                date = avail["date"]

                for cabin in cabin_classes:
                    seats = avail.get(cabin, 0)

                    if self.baseline_mode:
                        # Baseline mode: store without notification AND populate analytics
                        if seats > 0:
                            # Store in known_tickets (for change detection)
                            self.db.store_baseline(origin, destination, date, cabin, seats)

                            # Populate ticket_summary (for analytics/catalogue)
                            self.db.upsert_ticket_summary(
                                origin, destination, date, cabin, seats, None, direction
                            )

                            # Store initial availability snapshot
                            self.db.store_availability(
                                origin, destination, date, cabin, seats
                            )
                    else:
                        # Normal mode: detect changes
                        prev = self.db.get_previous_availability(
                            origin, destination, date, cabin
                        )

                        # Check if this was in baseline
                        is_baseline = self.db.is_baseline_ticket(
                            origin, destination, date, cabin
                        )

                        # Get ticket summary for historical tracking
                        summary = self.db.get_ticket_summary(origin, destination, date, cabin, direction)

                        if seats > 0:
                            # Detect type of change
                            if prev is None and not is_baseline:
                                # Truly new ticket (not in baseline) - check if we already notified
                                if not self.db.was_ticket_notified_recently(
                                    origin, destination, date, cabin, 'new', hours=24
                                ):
                                    changes['new_tickets'].append({
                                        'origin': origin,
                                        'destination': destination,
                                        'city_name': city_name,
                                        'date': date,
                                        'cabin': cabin,
                                        'seats': seats,
                                        'direction': direction
                                    })
                                    self.db.log_ticket_notification(
                                        origin, destination, date, cabin, 'new', seats
                                    )
                            elif prev is not None and seats > prev:
                                # Seat increase - check if we already notified
                                if not self.db.was_ticket_notified_recently(
                                    origin, destination, date, cabin, 'increase', hours=24
                                ):
                                    changes['seat_increases'].append({
                                        'origin': origin,
                                        'destination': destination,
                                        'city_name': city_name,
                                        'date': date,
                                        'cabin': cabin,
                                        'seats': seats,
                                        'previous_seats': prev,
                                        'direction': direction
                                    })
                                    self.db.log_ticket_notification(
                                        origin, destination, date, cabin, 'increase', seats
                                    )
                                    # Log the change for history
                                    self.db.log_seat_change(
                                        origin, destination, date, cabin, prev, seats
                                    )
                            elif prev is not None and seats < prev:
                                # Seat decrease (but not gone)
                                changes['seat_decreases'].append({
                                    'origin': origin,
                                    'destination': destination,
                                    'city_name': city_name,
                                    'date': date,
                                    'cabin': cabin,
                                    'seats': seats,
                                    'previous_seats': prev,
                                    'direction': direction
                                })
                                # Log the change for history
                                self.db.log_seat_change(
                                    origin, destination, date, cabin, prev, seats
                                )

                            # Update ticket summary
                            self.db.upsert_ticket_summary(
                                origin, destination, date, cabin, seats, summary, direction
                            )

                            # Store current availability snapshot
                            self.db.store_availability(
                                origin, destination, date, cabin, seats
                            )

                        elif prev is not None and prev > 0 and seats == 0:
                            # Ticket vanished - check if we already notified about this specific ticket
                            if not self.db.was_ticket_notified_recently(
                                origin, destination, date, cabin, 'vanished', hours=24
                            ):
                                changes['vanished'].append({
                                    'origin': origin,
                                    'destination': destination,
                                    'city_name': city_name,
                                    'date': date,
                                    'cabin': cabin,
                                    'previous_seats': prev,
                                    'direction': direction
                                })

                                # Log the notification intent (actual send happens later)
                                self.db.log_ticket_notification(
                                    origin, destination, date, cabin, 'vanished', prev
                                )
                                # Log the change for history
                                self.db.log_seat_change(
                                    origin, destination, date, cabin, prev, 0
                                )
                            else:
                                logger.info(f"Skipping duplicate vanished notification: {origin}->{destination} {date} {cabin}")

                            # Update ticket summary for vanished (always update, even if not notifying)
                            self.db.upsert_ticket_summary(
                                origin, destination, date, cabin, 0, summary, direction
                            )

                            # Store availability snapshot for sold-out state
                            # This ensures prev=0 on next check, preventing stale data issues
                            self.db.store_availability(
                                origin, destination, date, cabin, 0
                            )

                        elif seats == 0 and summary is not None:
                            # Seats are 0 but we have a summary (prev might be None due to
                            # availability table being empty). Update summary to reflect sold out.
                            if summary["currently_available"] > 0:
                                logger.info(f"Correcting stale data: {origin}->{destination} {date} {cabin} {direction} was {summary['currently_available']}, now 0")
                                self.db.upsert_ticket_summary(
                                    origin, destination, date, cabin, 0, summary, direction
                                )
                            # Store availability snapshot
                            self.db.store_availability(
                                origin, destination, date, cabin, 0
                            )

        return changes
    
    def send_consolidated_notifications(self, changes: dict) -> int:
        """
        Send consolidated notifications for all changes to all subscribers.
        Returns number of notifications sent.
        """
        notifications_sent = 0

        # Check if anything changed
        has_changes = any(changes.values())
        if not has_changes:
            logger.info("No changes detected - no notifications sent")
            return 0

        # Get all active subscribers
        subscribers = self.db.get_active_subscribers()
        if not subscribers:
            logger.info("No active subscribers - notifications not sent")
            return 0

        logger.info(f"Broadcasting to {len(subscribers)} subscriber(s)")

        # 1. Send NEW TICKETS and INCREASES message (combined)
        if changes['new_tickets'] or changes['seat_increases']:
            msg = self.format_new_tickets_message(
                changes['new_tickets'],
                changes['seat_increases']
            )

            # Compute hash from ticket identities, not message content (fixes timestamp issue)
            ticket_keys = []
            for t in changes['new_tickets'] + changes['seat_increases']:
                ticket_keys.append(f"{t['origin']}|{t['destination']}|{t['date']}|{t['cabin']}")
            msg_hash = hashlib.md5(('NEW:' + '|'.join(sorted(ticket_keys))).encode()).hexdigest()

            if not self.db.was_recently_notified(msg_hash, hours=24):
                sent_count = self.notifier.broadcast_message(msg, subscribers)
                if sent_count > 0:
                    self.db.log_notification("", "", "", "", 0, msg, msg_hash)
                    notifications_sent += 1
                    logger.info(f"Broadcast new tickets to {sent_count} subscribers ({len(changes['new_tickets'])} new, {len(changes['seat_increases'])} increases)")
                    logger.info(f"Notification hash: {msg_hash}")

        # 2. Send DECREASES message
        if changes['seat_decreases']:
            msg = self.format_decreases_message(changes['seat_decreases'])

            # Compute hash from ticket identities, not message content (fixes timestamp issue)
            ticket_keys = [
                f"{t['origin']}|{t['destination']}|{t['date']}|{t['cabin']}"
                for t in changes['seat_decreases']
            ]
            msg_hash = hashlib.md5(('DECREASE:' + '|'.join(sorted(ticket_keys))).encode()).hexdigest()

            if not self.db.was_recently_notified(msg_hash, hours=24):
                sent_count = self.notifier.broadcast_message(msg, subscribers)
                if sent_count > 0:
                    self.db.log_notification("", "", "", "", 0, msg, msg_hash)
                    notifications_sent += 1
                    logger.info(f"Broadcast decreases to {sent_count} subscribers ({len(changes['seat_decreases'])} tickets)")
                    logger.info(f"Notification hash: {msg_hash}")

        # 3. Send VANISHED message (also record in sales history)
        if changes['vanished']:
            msg = self.format_vanished_message(changes['vanished'])

            # Compute hash from ticket identities, not message content (fixes timestamp issue)
            ticket_keys = [
                f"{t['origin']}|{t['destination']}|{t['date']}|{t['cabin']}"
                for t in changes['vanished']
            ]
            msg_hash = hashlib.md5(('VANISHED:' + '|'.join(sorted(ticket_keys))).encode()).hexdigest()

            if not self.db.was_recently_notified(msg_hash, hours=24):
                sent_count = self.notifier.broadcast_message(msg, subscribers)
                if sent_count > 0:
                    self.db.log_notification("", "", "", "", 0, msg, msg_hash)
                    notifications_sent += 1
                    logger.info(f"Broadcast vanished to {sent_count} subscribers ({len(changes['vanished'])} tickets)")
                    logger.info(f"Notification hash: {msg_hash}")

            # Record sales history for each vanished ticket
            for ticket in changes['vanished']:
                summary = self.db.get_ticket_summary(
                    ticket['origin'], ticket['destination'],
                    ticket['date'], ticket['cabin'], ticket.get('direction', 'outbound')
                )
                if summary:
                    self.db.record_ticket_sold_out(
                        ticket['origin'], ticket['destination'],
                        ticket['date'], ticket['cabin'],
                        summary['first_seen_at'],
                        summary['max_issued'],
                        summary.get('booking_velocity', 0.0)
                    )

        return notifications_sent

    def format_new_tickets_message(self, new_tickets: list, increases: list) -> str:
        """Format consolidated message for new tickets and seat increases."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Group by route
        by_route = {}
        for ticket in new_tickets + increases:
            route_key = (ticket['origin'], ticket['destination'], ticket['city_name'])
            if route_key not in by_route:
                by_route[route_key] = []
            by_route[route_key].append(ticket)

        # Count unique routes and total tickets
        num_routes = len(by_route)
        num_tickets = len(new_tickets) + len(increases)

        msg = f"🎉 <b>NEW TICKETS FOUND ({num_routes} route(s), {num_tickets} ticket(s))</b>\n\n"

        for (origin, destination, city_name), tickets in sorted(by_route.items()):
            dest_display = f"{city_name} ({destination})" if city_name else destination
            msg += f"✈️ <b>{origin} → {dest_display}</b>\n"

            # Group by date
            by_date = {}
            for t in tickets:
                if t['date'] not in by_date:
                    by_date[t['date']] = []
                by_date[t['date']].append(t)

            for date in sorted(by_date.keys()):
                date_tickets = by_date[date]
                seat_parts = []
                for t in date_tickets:
                    class_name = SASAwardAPI.CABIN_CODES.get(t['cabin'], t['cabin'])
                    if t in increases:
                        diff = t['seats'] - t['previous_seats']
                        seat_parts.append(f"{class_name} {t['seats']} (+{diff})")
                    else:
                        seat_parts.append(f"{class_name} {t['seats']}")

                msg += f"📅 {date}: {', '.join(seat_parts)}\n"

            msg += "\n"

        msg += f"🕐 Discovered: {timestamp}\n"
        msg += '<a href="https://www.sas.no/award-finder">🔗 Book now on SAS</a>'

        return msg

    def format_decreases_message(self, decreases: list) -> str:
        """Format consolidated message for seat decreases."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Group by route
        by_route = {}
        for ticket in decreases:
            route_key = (ticket['origin'], ticket['destination'], ticket['city_name'])
            if route_key not in by_route:
                by_route[route_key] = []
            by_route[route_key].append(ticket)

        num_routes = len(by_route)
        num_tickets = len(decreases)

        msg = f"📉 <b>SEATS BEING BOOKED ({num_routes} route(s), {num_tickets} ticket(s))</b>\n\n"

        for (origin, destination, city_name), tickets in sorted(by_route.items()):
            dest_display = f"{city_name} ({destination})" if city_name else destination
            msg += f"✈️ <b>{origin} → {dest_display}</b>\n"

            for t in sorted(tickets, key=lambda x: x['date']):
                class_name = SASAwardAPI.CABIN_CODES.get(t['cabin'], t['cabin'])
                diff = t['previous_seats'] - t['seats']
                msg += f"📅 {t['date']}: {class_name} {t['previous_seats']}→{t['seats']} (-{diff})\n"

                # Add velocity indicator if available
                summary = self.db.get_ticket_summary(
                    t['origin'], t['destination'], t['date'], t['cabin'], t.get('direction', 'outbound')
                )
                if summary and summary['booking_velocity'] > 0:
                    velocity = summary['booking_velocity']
                    if velocity >= 1.5:
                        emoji = "🔥🔥🔥"
                    elif velocity >= 1.0:
                        emoji = "🔥🔥"
                    elif velocity >= 0.5:
                        emoji = "🔥"
                    else:
                        emoji = ""
                    if emoji:
                        msg += f"⚡ Velocity: {velocity:.1f} seats/hour {emoji}\n"

            msg += "\n"

        msg += f"🕐 Changes detected: {timestamp}"

        return msg

    def format_vanished_message(self, vanished: list) -> str:
        """Format consolidated message for vanished tickets."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Group by route
        by_route = {}
        for ticket in vanished:
            route_key = (ticket['origin'], ticket['destination'], ticket['city_name'])
            if route_key not in by_route:
                by_route[route_key] = []
            by_route[route_key].append(ticket)

        num_routes = len(by_route)
        num_tickets = len(vanished)

        msg = f"💨 <b>TICKETS GONE ({num_routes} route(s), {num_tickets} ticket(s))</b>\n\n"

        for (origin, destination, city_name), tickets in sorted(by_route.items()):
            dest_display = f"{city_name} ({destination})" if city_name else destination
            msg += f"✈️ <b>{origin} → {dest_display}</b>\n"

            for t in sorted(tickets, key=lambda x: x['date']):
                class_name = SASAwardAPI.CABIN_CODES.get(t['cabin'], t['cabin'])
                msg += f"📅 {t['date']}: {class_name} SOLD OUT\n"
                msg += f"📊 Was {t['previous_seats']} seat(s) → All booked!\n"

            msg += "\n"

        msg += f"🕐 Gone at: {timestamp}\n"
        msg += "⚠️ Likely booked by travelers"

        return msg

    def run_once(self, parallel: bool = True, max_workers: int = 4) -> int:
        """
        Run a single check of all routes.
        
        Args:
            parallel: If True, use parallel queries (faster)
            max_workers: Number of concurrent API requests
        """
        total_routes = len(self.routes)
        start_time = time.time()

        if self.baseline_mode:
            # Baseline mode - sequential to avoid rate limiting
            total_stored = 0
            for idx, route in enumerate(self.routes, 1):
                try:
                    logger.info(f"Route {idx}/{total_routes}: {route['origin']} → {route['destination']}")
                    self.check_route(
                        route["origin"],
                        route["destination"],
                        route["cabin_classes"]
                    )
                    time.sleep(self.config.request_delay)
                except Exception as e:
                    logger.error(f"Error checking {route}: {e}")

            baseline_count = self.db.get_baseline_count()
            logger.info(f"Baseline initialization complete.")
            logger.info(f"Total baseline tickets in database: {baseline_count}")
            return baseline_count

        # Normal mode - collect all changes
        all_changes = {
            'new_tickets': [],
            'seat_increases': [],
            'seat_decreases': [],
            'vanished': []
        }

        def check_single_route(route_info):
            """Worker function for parallel execution."""
            idx, route = route_info
            try:
                return self.check_route(
                    route["origin"],
                    route["destination"],
                    route["cabin_classes"]
                )
            except Exception as e:
                logger.error(f"Error checking {route['origin']}→{route['destination']}: {e}")
                return {'new_tickets': [], 'seat_increases': [], 
                        'seat_decreases': [], 'vanished': []}

        if parallel and total_routes > 1:
            # Parallel execution
            logger.info(f"Checking {total_routes} routes in parallel (workers={max_workers})...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all routes
                futures = {
                    executor.submit(check_single_route, (idx, route)): route
                    for idx, route in enumerate(self.routes, 1)
                }
                
                # Collect results as they complete
                completed = 0
                for future in as_completed(futures):
                    route = futures[future]
                    completed += 1
                    try:
                        route_changes = future.result()
                        all_changes['new_tickets'].extend(route_changes['new_tickets'])
                        all_changes['seat_increases'].extend(route_changes['seat_increases'])
                        all_changes['seat_decreases'].extend(route_changes['seat_decreases'])
                        all_changes['vanished'].extend(route_changes['vanished'])
                        
                        if completed % 10 == 0:
                            logger.info(f"Progress: {completed}/{total_routes} routes checked")
                    except Exception as e:
                        logger.error(f"Error processing {route}: {e}")
        else:
            # Sequential execution (for baseline or single route)
            for idx, route in enumerate(self.routes, 1):
                try:
                    logger.info(f"Route {idx}/{total_routes}: {route['origin']} → {route['destination']}")
                    route_changes = self.check_route(
                        route["origin"],
                        route["destination"],
                        route["cabin_classes"]
                    )

                    # Collect changes
                    all_changes['new_tickets'].extend(route_changes['new_tickets'])
                    all_changes['seat_increases'].extend(route_changes['seat_increases'])
                    all_changes['seat_decreases'].extend(route_changes['seat_decreases'])
                    all_changes['vanished'].extend(route_changes['vanished'])

                    time.sleep(self.config.request_delay)
                except Exception as e:
                    logger.error(f"Error checking {route}: {e}")

        # Send consolidated notifications
        notifications_sent = self.send_consolidated_notifications(all_changes)

        elapsed = time.time() - start_time
        logger.info(f"Check complete. {notifications_sent} notification(s) sent.")
        logger.info(f"Check completed in {elapsed:.1f}s")
        return notifications_sent
    
    def run(self):
        """Main monitoring loop."""
        logger.info(f"Starting SAS Award Monitor")
        logger.info(f"Monitoring {len(self.routes)} routes (Europe↔Asia bidirectional)")
        logger.info(f"Poll interval: {self.config.poll_interval}s")
        logger.info(f"Parallel queries enabled (4 workers)")

        while True:
            try:
                start_time = time.time()
                self.run_once()
                elapsed = time.time() - start_time

                logger.info(f"Check completed in {elapsed:.1f}s")
                logger.info(f"Sleeping {self.config.poll_interval}s until next check...")
                time.sleep(self.config.poll_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Backoff on error

        self.db.close()
    
    def test_connectivity(self) -> bool:
        """Test API connectivity."""
        logger.info("Testing API connectivity...")
        
        data = self.api.get_destinations("OSL")
        if data:
            logger.info(f"✓ API working. Found {len(data)} destinations from OSL")
            
            # Show sample business class destinations
            biz = [d["airportCode"] for d in data if "AB" in d.get("flightClasses", [])]
            logger.info(f"✓ {len(biz)} destinations with Business class")
            return True
        else:
            logger.error("✗ API request failed")
            return False


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="SAS EuroBonus Award Seat Monitor - Europe to Asia Routes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sas_monitor.py --init-baseline    # First-time setup (no notifications)
  python sas_monitor.py                    # Run continuous monitoring
  python sas_monitor.py --once             # Run single check
  python sas_monitor.py --test             # Test API connectivity
  python sas_monitor.py --config my.json   # Use custom config file

Environment variables:
  TELEGRAM_BOT_TOKEN    Telegram bot token from @BotFather
  TELEGRAM_CHAT_ID      Your Telegram chat ID
        """
    )

    parser.add_argument("--once", action="store_true",
                       help="Run single check and exit")
    parser.add_argument("--test", action="store_true",
                       help="Test API connectivity and exit")
    parser.add_argument("--init-baseline", action="store_true",
                       help="Initialize baseline without sending notifications")
    parser.add_argument("--config", type=str,
                       help="Path to JSON config file")
    parser.add_argument("--cookies", type=str,
                       help="SAS session cookie string")
    parser.add_argument("--interval", type=int, default=900,
                       help="Poll interval in seconds (default: 900)")
    
    args = parser.parse_args()
    
    # Load config
    if args.config and Path(args.config).exists():
        config = Config.from_file(args.config)
        if args.cookies:
            config.cookies = args.cookies
    else:
        import os
        config = Config(
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            poll_interval=args.interval,
            cookies=args.cookies or ""
        )
    
    # Initialize monitor with baseline mode if requested
    monitor = SASAwardMonitor(config, baseline_mode=args.init_baseline)

    if args.test:
        success = monitor.test_connectivity()
        exit(0 if success else 1)
    elif args.init_baseline:
        logger.info("BASELINE INITIALIZATION MODE - No notifications will be sent")
        logger.info(f"Populating database with current availability for {len(monitor.routes)} routes")
        monitor.run_once()
        logger.info("Baseline complete. Future runs will alert on NEW availability only.")
    elif args.once:
        monitor.run_once()
    else:
        monitor.run()


if __name__ == "__main__":
    main()
