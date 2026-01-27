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
import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
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
ORIGINS = ["OSL", "CDG", "CPH", "AMS"]
DESTINATIONS = [
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

# Generate all 36 route combinations (4 origins × 9 destinations)
DEFAULT_ROUTES = [
    {"origin": origin, "destination": dest, "cabin_classes": CABIN_CLASSES}
    for origin in ORIGINS
    for dest in DESTINATIONS
]


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
        """Make API request."""
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
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            logger.error(f"Request timeout for {origin}->{destination}")
            return []
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return []
        except json.JSONDecodeError:
            logger.error("Invalid JSON response")
            return []


# ============================================================================
# Database
# ============================================================================

class AvailabilityDatabase:
    """SQLite database for storing availability data."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
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
                message TEXT
            );

            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL UNIQUE,
                username TEXT,
                first_name TEXT,
                notify_new INTEGER DEFAULT 1,
                notify_gone INTEGER DEFAULT 0,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_subscribers_chat_id
            ON subscribers(chat_id);

            CREATE TABLE IF NOT EXISTS discovered_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                cabin_class TEXT NOT NULL,
                seats_available INTEGER NOT NULL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(origin, destination, date, cabin_class)
            );

            CREATE INDEX IF NOT EXISTS idx_discovered_route
            ON discovered_tickets(origin, destination, date, cabin_class);

            CREATE TABLE IF NOT EXISTS vanished_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                cabin_class TEXT NOT NULL,
                last_seats INTEGER NOT NULL,
                discovered_at TIMESTAMP,
                vanished_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_seconds INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_vanished_route
            ON vanished_tickets(origin, destination, date);
        """)
        self.conn.commit()

        # Migration: add new columns to existing subscribers table if missing
        self._migrate_subscribers_table()

    def _migrate_subscribers_table(self):
        """Add new columns to subscribers table if they don't exist."""
        cursor = self.conn.execute("PRAGMA table_info(subscribers)")
        columns = [row[1] for row in cursor.fetchall()]

        if "notify_new" not in columns:
            self.conn.execute("ALTER TABLE subscribers ADD COLUMN notify_new INTEGER DEFAULT 1")
        if "notify_gone" not in columns:
            self.conn.execute("ALTER TABLE subscribers ADD COLUMN notify_gone INTEGER DEFAULT 0")
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
                        cabin_class: str, seats: int, message: str):
        """Log sent notification."""
        self.conn.execute(
            """INSERT INTO notifications
               (origin, destination, date, cabin_class, seats, message)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (origin, destination, date, cabin_class, seats, message)
        )
        self.conn.commit()

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
        
        # Notifications sent
        cursor = self.conn.execute("SELECT COUNT(*) FROM notifications")
        stats["notifications_sent"] = cursor.fetchone()[0]

        # Subscriber count
        cursor = self.conn.execute("SELECT COUNT(*) FROM subscribers")
        stats["subscriber_count"] = cursor.fetchone()[0]

        return stats

    def add_subscriber(self, chat_id: str, username: str = None, first_name: str = None,
                       notify_new: bool = True, notify_gone: bool = False) -> bool:
        """Add a subscriber. Returns True if newly added, False if already exists."""
        try:
            self.conn.execute(
                """INSERT INTO subscribers (chat_id, username, first_name, notify_new, notify_gone)
                   VALUES (?, ?, ?, ?, ?)""",
                (str(chat_id), username, first_name, int(notify_new), int(notify_gone))
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_subscriber(self, chat_id: str, notify_new: bool = None, notify_gone: bool = None,
                         username: str = None, first_name: str = None):
        """Update subscriber preferences."""
        updates = []
        params = []
        if notify_new is not None:
            updates.append("notify_new = ?")
            params.append(int(notify_new))
        if notify_gone is not None:
            updates.append("notify_gone = ?")
            params.append(int(notify_gone))
        if username is not None:
            updates.append("username = ?")
            params.append(username)
        if first_name is not None:
            updates.append("first_name = ?")
            params.append(first_name)

        if updates:
            params.append(str(chat_id))
            self.conn.execute(
                f"UPDATE subscribers SET {', '.join(updates)} WHERE chat_id = ?",
                params
            )
            self.conn.commit()

    def remove_subscriber(self, chat_id: str) -> bool:
        """Remove a subscriber. Returns True if removed, False if didn't exist."""
        cursor = self.conn.execute(
            "DELETE FROM subscribers WHERE chat_id = ?",
            (str(chat_id),)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_subscriber(self, chat_id: str) -> dict:
        """Get subscriber info including preferences."""
        cursor = self.conn.execute(
            "SELECT chat_id, username, first_name, notify_new, notify_gone, subscribed_at FROM subscribers WHERE chat_id = ?",
            (str(chat_id),)
        )
        row = cursor.fetchone()
        if row:
            return {
                "chat_id": row[0],
                "username": row[1],
                "first_name": row[2],
                "notify_new": bool(row[3]),
                "notify_gone": bool(row[4]),
                "subscribed_at": row[5]
            }
        return None

    def is_subscribed(self, chat_id: str) -> bool:
        """Check if a chat_id is subscribed to anything."""
        cursor = self.conn.execute(
            "SELECT 1 FROM subscribers WHERE chat_id = ? AND (notify_new = 1 OR notify_gone = 1)",
            (str(chat_id),)
        )
        return cursor.fetchone() is not None

    def get_subscribers_for_new(self) -> list:
        """Get chat_ids subscribed to new ticket alerts."""
        cursor = self.conn.execute("SELECT chat_id FROM subscribers WHERE notify_new = 1")
        return [row[0] for row in cursor.fetchall()]

    def get_subscribers_for_gone(self) -> list:
        """Get chat_ids subscribed to vanishing ticket alerts."""
        cursor = self.conn.execute("SELECT chat_id FROM subscribers WHERE notify_gone = 1")
        return [row[0] for row in cursor.fetchall()]

    def get_all_subscribers(self) -> list:
        """Get all subscriber chat_ids (for any notification type)."""
        cursor = self.conn.execute("SELECT chat_id FROM subscribers WHERE notify_new = 1 OR notify_gone = 1")
        return [row[0] for row in cursor.fetchall()]

    def get_subscribers_info(self) -> list:
        """Get subscriber info for admin display."""
        cursor = self.conn.execute(
            "SELECT chat_id, username, first_name, notify_new, notify_gone, subscribed_at FROM subscribers ORDER BY subscribed_at"
        )
        return cursor.fetchall()

    # Discovered tickets methods
    def track_discovered_ticket(self, origin: str, destination: str, date: str,
                                cabin_class: str, seats: int) -> bool:
        """Track when a ticket is first discovered. Returns True if new."""
        try:
            self.conn.execute(
                """INSERT INTO discovered_tickets (origin, destination, date, cabin_class, seats_available)
                   VALUES (?, ?, ?, ?, ?)""",
                (origin, destination, date, cabin_class, seats)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Already tracked
            return False

    def get_discovered_ticket(self, origin: str, destination: str, date: str,
                              cabin_class: str) -> dict:
        """Get discovery info for a ticket."""
        cursor = self.conn.execute(
            """SELECT discovered_at, seats_available FROM discovered_tickets
               WHERE origin = ? AND destination = ? AND date = ? AND cabin_class = ?""",
            (origin, destination, date, cabin_class)
        )
        row = cursor.fetchone()
        if row:
            return {"discovered_at": row[0], "seats": row[1]}
        return None

    def get_all_discovered_tickets(self, origin_filter: str = None,
                                   destination_filter: str = None) -> list:
        """Get all discovered tickets, optionally filtered."""
        query = """SELECT origin, destination, date, cabin_class, seats_available, discovered_at
                   FROM discovered_tickets WHERE 1=1"""
        params = []

        if origin_filter:
            query += " AND origin = ?"
            params.append(origin_filter)
        if destination_filter:
            query += " AND destination = ?"
            params.append(destination_filter)

        query += " ORDER BY origin, destination, date, cabin_class"
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()

    def get_unique_routes(self) -> list:
        """Get list of unique routes from discovered tickets."""
        cursor = self.conn.execute(
            "SELECT DISTINCT origin, destination FROM discovered_tickets ORDER BY origin, destination"
        )
        return cursor.fetchall()

    # Vanished tickets methods
    def record_vanished_ticket(self, origin: str, destination: str, date: str,
                               cabin_class: str, last_seats: int):
        """Record when a ticket vanishes."""
        # Get discovery time
        discovered = self.get_discovered_ticket(origin, destination, date, cabin_class)
        discovered_at = discovered["discovered_at"] if discovered else None

        # Calculate duration
        duration_seconds = None
        if discovered_at:
            try:
                from datetime import datetime
                disc_dt = datetime.strptime(discovered_at, "%Y-%m-%d %H:%M:%S")
                duration_seconds = int((datetime.now() - disc_dt).total_seconds())
            except:
                pass

        self.conn.execute(
            """INSERT INTO vanished_tickets
               (origin, destination, date, cabin_class, last_seats, discovered_at, duration_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (origin, destination, date, cabin_class, last_seats, discovered_at, duration_seconds)
        )
        self.conn.commit()

        # Remove from discovered tickets
        self.conn.execute(
            "DELETE FROM discovered_tickets WHERE origin = ? AND destination = ? AND date = ? AND cabin_class = ?",
            (origin, destination, date, cabin_class)
        )
        self.conn.commit()

        return {"discovered_at": discovered_at, "duration_seconds": duration_seconds}

    def get_vanished_tickets(self, limit: int = 50) -> list:
        """Get recent vanished tickets."""
        cursor = self.conn.execute(
            """SELECT origin, destination, date, cabin_class, last_seats,
                      discovered_at, vanished_at, duration_seconds
               FROM vanished_tickets
               ORDER BY vanished_at DESC
               LIMIT ?""",
            (limit,)
        )
        return cursor.fetchall()

    def get_vanished_stats(self) -> dict:
        """Get vanished tickets statistics."""
        stats = {}

        cursor = self.conn.execute("SELECT COUNT(*) FROM vanished_tickets")
        stats["total_vanished"] = cursor.fetchone()[0]

        cursor = self.conn.execute(
            "SELECT AVG(duration_seconds) FROM vanished_tickets WHERE duration_seconds IS NOT NULL"
        )
        avg = cursor.fetchone()[0]
        stats["avg_duration_seconds"] = int(avg) if avg else None

        # Fastest selling routes
        cursor = self.conn.execute(
            """SELECT origin, destination, COUNT(*) as count, AVG(duration_seconds) as avg_dur
               FROM vanished_tickets
               WHERE duration_seconds IS NOT NULL
               GROUP BY origin, destination
               ORDER BY avg_dur ASC
               LIMIT 5"""
        )
        stats["fastest_routes"] = cursor.fetchall()

        return stats

    def close(self):
        self.conn.close()


# ============================================================================
# Telegram Notifier
# ============================================================================

class TelegramNotifier:
    """Send notifications via Telegram bot."""

    def __init__(self, bot_token: str, chat_id: str, db_path: str = None):
        self.bot_token = bot_token
        self.chat_id = chat_id  # Admin chat_id (always receives notifications)
        self.db_path = db_path
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token and chat_id)

        if not self.enabled:
            logger.warning("Telegram notifications disabled (no token/chat_id)")

    def _send_to_chat(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to a specific chat."""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Telegram notification to {chat_id} failed: {e}")
            return False

    def send_message(self, text: str, parse_mode: str = "HTML",
                     notification_type: str = "new") -> bool:
        """Send a message to admin and subscribers based on notification type.

        Args:
            text: Message text
            parse_mode: Telegram parse mode
            notification_type: "new" for new tickets, "gone" for vanished tickets
        """
        if not self.enabled:
            logger.info(f"[DRY RUN] Would send: {text[:100]}...")
            return False

        # Collect all recipients: admin + appropriate subscribers
        recipients = set()
        recipients.add(self.chat_id)  # Admin always gets notifications

        # Get subscribers from database based on type
        if self.db_path:
            try:
                db = AvailabilityDatabase(self.db_path)
                if notification_type == "new":
                    subscribers = db.get_subscribers_for_new()
                elif notification_type == "gone":
                    subscribers = db.get_subscribers_for_gone()
                else:
                    subscribers = db.get_all_subscribers()
                recipients.update(subscribers)
                db.close()
            except Exception as e:
                logger.error(f"Failed to get subscribers: {e}")

        # Send to all recipients
        success_count = 0
        for chat_id in recipients:
            if self._send_to_chat(chat_id, text, parse_mode):
                success_count += 1

        logger.info(f"Telegram notification ({notification_type}) sent to {success_count}/{len(recipients)} recipients")
        return success_count > 0
    
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
        direction: str = "",
        discovered_at: str = None,
        duration_seconds: int = None
    ) -> str:
        """Format a vanishing alert message."""
        class_name = SASAwardAPI.CABIN_CODES.get(cabin_class, cabin_class)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        dest_display = f"{city_name} ({destination})" if city_name else destination
        direction_text = f" ({direction})" if direction else ""

        # Format duration
        duration_text = ""
        if duration_seconds is not None:
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            if hours > 0:
                duration_text = f"\n⏱️ Was available for: <b>{hours}h {minutes}m</b>"
            else:
                duration_text = f"\n⏱️ Was available for: <b>{minutes}m</b>"

        discovered_text = ""
        if discovered_at:
            discovered_text = f"\n🔍 Discovered: {discovered_at}"

        return f"""💨 <b>TICKET SOLD / GONE</b>

✈️ <b>{origin} → {dest_display}</b>{direction_text}
📅 Date: {date}
💺 {class_name}: was <b>{previous_seats}</b> seat(s){discovered_text}{duration_text}

🕐 Gone at: {timestamp}
⚠️ <i>Likely booked by someone!</i>"""


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
            config.telegram_chat_id,
            config.db_path
        )
        self.routes = routes or DEFAULT_ROUTES
        self.baseline_mode = baseline_mode
    
    def check_route(self, origin: str, destination: str, cabin_classes: list) -> int:
        """
        Check availability for a specific route.

        Returns:
            Number of alerts triggered (or baseline records stored)
        """
        logger.info(f"Checking {origin} → {destination} [{', '.join(cabin_classes)}]")

        data = self.api.get_availability(origin=origin, destination=destination)

        if not data:
            logger.debug(f"No data for {origin} → {destination}")
            return 0

        dest_data = data[0]
        city_name = dest_data.get("cityName", "")
        alerts = 0

        # Process outbound and inbound availability
        for direction in ["outbound", "inbound"]:
            for avail in dest_data.get("availability", {}).get(direction, []):
                date = avail["date"]

                for cabin in cabin_classes:
                    seats = avail.get(cabin, 0)
                    prev = self.db.get_previous_availability(origin, destination, date, cabin)

                    if self.baseline_mode:
                        # Baseline mode: store without notification
                        if seats > 0:
                            self.db.store_baseline(origin, destination, date, cabin, seats)
                            # Also track as discovered for duration tracking
                            self.db.track_discovered_ticket(origin, destination, date, cabin, seats)
                            alerts += 1
                    else:
                        # Check if this was in baseline
                        is_baseline = self.db.is_baseline_ticket(origin, destination, date, cabin)

                        if seats > 0:
                            # Check if new or increased
                            should_alert = False
                            if prev is None and not is_baseline:
                                # Truly new ticket (not in baseline)
                                should_alert = True
                                # Track discovery time
                                self.db.track_discovered_ticket(origin, destination, date, cabin, seats)
                            elif prev is not None and seats > prev:
                                # Seat increase
                                should_alert = True

                            if should_alert:
                                discovered_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                                msg = self.notifier.format_availability_alert(
                                    origin, destination, date, cabin,
                                    seats, prev, city_name,
                                    direction=direction,
                                    discovered_at=discovered_at
                                )
                                if self.notifier.send_message(msg, notification_type="new"):
                                    self.db.log_notification(
                                        origin, destination, date, cabin, seats, msg
                                    )
                                alerts += 1

                            # Always store current state
                            self.db.store_availability(origin, destination, date, cabin, seats)

                        elif seats == 0 and prev is not None and prev > 0:
                            # Seats vanished (was available, now gone)
                            # Record vanished ticket and get duration info
                            vanish_info = self.db.record_vanished_ticket(
                                origin, destination, date, cabin, prev
                            )

                            msg = self.notifier.format_vanishing_alert(
                                origin, destination, date, cabin,
                                prev, city_name, direction=direction,
                                discovered_at=vanish_info.get("discovered_at"),
                                duration_seconds=vanish_info.get("duration_seconds")
                            )
                            self.notifier.send_message(msg, notification_type="gone")
                            alerts += 1

                            # Store zero availability
                            self.db.store_availability(origin, destination, date, cabin, seats)

        return alerts
    
    def run_once(self) -> int:
        """Run a single check of all routes."""
        total_alerts = 0
        total_routes = len(self.routes)

        for idx, route in enumerate(self.routes, 1):
            try:
                logger.info(f"Route {idx}/{total_routes}: {route['origin']} → {route['destination']}")
                alerts = self.check_route(
                    route["origin"],
                    route["destination"],
                    route["cabin_classes"]
                )
                total_alerts += alerts
                time.sleep(self.config.request_delay)
            except Exception as e:
                logger.error(f"Error checking {route}: {e}")

        if self.baseline_mode:
            baseline_count = self.db.get_baseline_count()
            logger.info(f"Baseline initialization complete. {total_alerts} tickets stored.")
            logger.info(f"Total baseline tickets in database: {baseline_count}")
        else:
            logger.info(f"Check complete. {total_alerts} alerts triggered.")

        return total_alerts
    
    def run(self):
        """Main monitoring loop."""
        logger.info(f"Starting SAS Award Monitor")
        logger.info(f"Monitoring {len(self.routes)} Europe→Asia routes")
        logger.info(f"Poll interval: {self.config.poll_interval}s")

        expected_duration = len(self.routes) * self.config.request_delay
        logger.info(f"Expected check duration: ~{expected_duration:.0f}s ({expected_duration/60:.1f} min)")

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
