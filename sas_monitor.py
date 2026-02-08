#!/usr/bin/env python3
"""
SAS EuroBonus Award Monitor - 2.0 (Overhaul)

A two-tiered monitoring system:
1.  Tier 1 (Cache Warmer): Scans the Calendar API (`destinations/v1`) hourly for broad availability.
2.  Tier 2 (Real-Time Verify): Checks the Routes API (`routes/v1`) frequently for specific subscribed searches that Tier 1 flagged.

This design minimizes heavy API usage while ensuring fast alerts for subscribed users.
"""

import os
import sys
import time
import json
import logging
import sqlite3
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

from sas_search_api import SASSearchEngine, FlightOffer, AvailabilityDate, RouteInfo

# ============================================================================
# Logging
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/sas_monitor.log")
    ]
)
logger = logging.getLogger("SASMonitor")

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class Config:
    """Monitor configuration."""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""  # Default/Admin chat ID (optional)
    db_path: str = "sas_monitor.db"
    cookies: str = ""
    
    # Timing
    tier1_interval: int = 3600    # 1 hour (Cache Warmer)
    tier2_interval: int = 900     # 15 minutes (Real-time check)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load from environment variables."""
        return cls(
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            db_path=os.environ.get("DB_PATH", "sas_monitor.db"),
            cookies=os.environ.get("SAS_COOKIES", "")
        )

    def load_session(self, session_path: str = "sas_session.json"):
        """Load cookies from sas_session.json if available."""
        try:
            if Path(session_path).exists():
                with open(session_path) as f:
                    data = json.load(f)
                
                cookies_list = data.get("cookies", [])
                cookie_strings = []
                for c in cookies_list:
                    if isinstance(c, dict) and "name" in c and "value" in c:
                        cookie_strings.append(f"{c['name']}={c['value']}")
                
                if cookie_strings:
                    self.cookies = "; ".join(cookie_strings)
                    return True
        except Exception as e:
            logger.warning(f"Could not load session from {session_path}: {e}")
        return False

# ============================================================================
# Database Manager
# ============================================================================

class AvailabilityDatabase:
    """SQLite database for managing subscriptions and availability cache."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        
    def _create_tables(self):
        cur = self.conn.cursor()
        
        # Subscriptions: User wants alerts for Origin -> Dest in Cabin
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                cabin_filter TEXT, -- AG, AP, AB
                saver_only INTEGER DEFAULT 0, -- 1 = only bonus/saver tickets
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, origin, destination, cabin_filter, saver_only)
            )
        """)

        # Migration: Add saver_only column if it doesn't exist
        try:
            cur.execute("ALTER TABLE subscriptions ADD COLUMN saver_only INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Cached Availability (Tier 1): Found by Calendar Scan
        # Just stores "date X for OSL->BKK has Y seats in Z cabin"
        # Used as a signal for Tier 2 to verify.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cached_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL, -- YYYY-MM-DD
                cabin_class TEXT NOT NULL, -- AG, AP, AB
                seats INTEGER NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(origin, destination, date, cabin_class)
            )
        """)
        
        # Sent Notifications: Prevent spam
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sent_notifications (
                subscription_id INTEGER,
                flight_hash TEXT NOT NULL, -- Unique ID for specific flight/date combo
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(subscription_id) REFERENCES subscriptions(id)
            )
        """)
        
        self.conn.commit()

    # --- Subscriptions ---
    def add_subscription(self, chat_id: str, origin: str, dest: str, cabin: str = None, saver_only: bool = False) -> bool:
        try:
            self.conn.execute(
                "INSERT INTO subscriptions (chat_id, origin, destination, cabin_filter, saver_only) VALUES (?, ?, ?, ?, ?)",
                (chat_id, origin.upper(), dest.upper(), cabin.upper() if cabin else None, 1 if saver_only else 0)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Already exists

    def remove_subscription(self, sub_id: int, chat_id: str) -> bool:
        cur = self.conn.execute(
            "DELETE FROM subscriptions WHERE id = ? AND chat_id = ?",
            (sub_id, chat_id)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def get_subscriptions(self, chat_id: str = None) -> List[sqlite3.Row]:
        if chat_id:
            return self.conn.execute("SELECT * FROM subscriptions WHERE chat_id = ?", (chat_id,)).fetchall()
        return self.conn.execute("SELECT * FROM subscriptions").fetchall()

    def get_unique_routes(self) -> List[Tuple[str, str]]:
        """Get list of unique (origin, destination) pairs to scan."""
        return self.conn.execute("SELECT DISTINCT origin, destination FROM subscriptions").fetchall()

    # --- Cache (Tier 1) ---
    def update_cache(self, origin: str, dest: str, date: str, cabin: str, seats: int):
        self.conn.execute("""
            INSERT INTO cached_availability (origin, destination, date, cabin_class, seats, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(origin, destination, date, cabin_class) 
            DO UPDATE SET seats=excluded.seats, last_updated=CURRENT_TIMESTAMP
        """, (origin, dest, date, cabin, seats))
        self.conn.commit()

    def get_promising_dates(self, origin: str, dest: str, cabin_filter: str = None) -> List[str]:
        """Get dates from cache that match a subscription filter."""
        query = "SELECT date FROM cached_availability WHERE origin=? AND destination=? AND seats > 0"
        args = [origin, dest]
        
        if cabin_filter:
            # If user wants Business (AB), only check AB cache.
            # If user wants ANY, check all.
            query += " AND cabin_class=?"
            args.append(cabin_filter)
            
        cur = self.conn.execute(query, args)
        return [row[0] for row in cur.fetchall()]
        
    def clear_cache_for_route(self, origin: str, dest: str):
        """Clear cache before a fresh scan to remove stale dates."""
        self.conn.execute("DELETE FROM cached_availability WHERE origin=? AND destination=?", (origin, dest))
        self.conn.commit()

    # --- Notifications ---
    def is_notification_sent(self, sub_id: int, flight_hash: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM sent_notifications WHERE subscription_id=? AND flight_hash=?",
            (sub_id, flight_hash)
        )
        return cur.fetchone() is not None

    def log_notification(self, sub_id: int, flight_hash: str):
        self.conn.execute(
            "INSERT INTO sent_notifications (subscription_id, flight_hash) VALUES (?, ?)",
            (sub_id, flight_hash)
        )
        self.conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive stats for /status command."""
        # Subscription stats
        sub_count = self.conn.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
        route_count = self.conn.execute("SELECT COUNT(DISTINCT origin || destination) FROM subscriptions").fetchone()[0]
        routes = self.conn.execute("SELECT DISTINCT origin, destination FROM subscriptions LIMIT 5").fetchall()

        # Notification stats
        notif_today = self.conn.execute("""
            SELECT COUNT(*) FROM sent_notifications
            WHERE date(sent_at) = date('now')
        """).fetchone()[0]
        notif_week = self.conn.execute("""
            SELECT COUNT(*) FROM sent_notifications
            WHERE sent_at > datetime('now', '-7 days')
        """).fetchone()[0]

        # Cache stats
        cache_count = self.conn.execute("SELECT COUNT(*) FROM cached_availability WHERE seats > 0").fetchone()[0]
        seats_by_cabin = self.conn.execute("""
            SELECT cabin_class, SUM(seats) FROM cached_availability
            WHERE seats > 0
            GROUP BY cabin_class
        """).fetchall()
        last_update = self.conn.execute("SELECT MAX(last_updated) FROM cached_availability").fetchone()[0]

        return {
            "subscriptions": sub_count,
            "routes": route_count,
            "route_list": [(r["origin"], r["destination"]) for r in routes],
            "notifications_today": notif_today,
            "notifications_week": notif_week,
            "cached_dates": cache_count,
            "seats_by_cabin": dict(seats_by_cabin) if seats_by_cabin else {},
            "last_cache_update": last_update,
        }

    def get_best_deals(self, limit: int = 10, cabin_filter: str = None) -> List[Dict[str, Any]]:
        """Get routes with the most available award seats (hottest deals).
        
        Args:
            limit: Maximum number of deals to return
            cabin_filter: Optional cabin filter ('AG', 'AP', 'AB')
        
        Returns:
            List of dicts with route info, total seats, available dates count, and sample dates
        """
        # Build query based on cabin filter
        cabin_where = "AND cabin_class = ?" if cabin_filter else ""
        args = [cabin_filter] if cabin_filter else []
        
        # Get aggregated stats per route
        query = f"""
            SELECT 
                origin,
                destination,
                cabin_class,
                COUNT(*) as date_count,
                SUM(seats) as total_seats,
                MAX(seats) as max_seats,
                GROUP_CONCAT(date) as dates
            FROM cached_availability 
            WHERE seats > 0 {cabin_where}
            GROUP BY origin, destination, cabin_class
            ORDER BY total_seats DESC, date_count DESC
            LIMIT ?
        """
        args.append(limit)
        
        rows = self.conn.execute(query, args).fetchall()
        
        deals = []
        for row in rows:
            # Parse dates and get up to 5 upcoming ones
            all_dates = row["dates"].split(",") if row["dates"] else []
            upcoming_dates = []
            today = datetime.now().strftime("%Y-%m-%d")
            
            for d in sorted(all_dates):
                if d >= today:
                    upcoming_dates.append(d)
                    if len(upcoming_dates) >= 5:
                        break
            
            deals.append({
                "origin": row["origin"],
                "destination": row["destination"],
                "cabin": row["cabin_class"],
                "date_count": row["date_count"],
                "total_seats": row["total_seats"],
                "max_seats": row["max_seats"],
                "upcoming_dates": upcoming_dates
            })
        
        return deals

    def close(self):
        self.conn.close()

# ============================================================================
# Monitor Logic
# ============================================================================

class SASMonitor:
    def __init__(self, config: Config, session_file: str = "sas_session.json"):
        self.config = config
        self.session_file = session_file
        self.db = AvailabilityDatabase(config.db_path)
        self.api = SASSearchEngine(cookies_file=session_file)
        
        # Telegram Setup
        self.bot = None
        if config.telegram_bot_token:
            from telegram import Bot
            self.bot = Bot(token=config.telegram_bot_token)
        
    async def send_alert(self, chat_id: str, message: str):
        if self.bot:
            try:
                await self.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to send Telegram alert to {chat_id}: {e}")

    # --- Tier 1: Cache Warmer ---
    def run_tier1_scan(self):
        """Scan Calendar API for all subscribed routes."""
        logger.info("[TIER 1] Starting Cache Warmer Scan...")
        unique_routes = self.db.get_unique_routes()
        
        if not unique_routes:
            logger.info("[TIER 1] No subscriptions found. Skipping scan.")
            return

        for route in unique_routes:
            origin = route["origin"]
            dest = route["destination"]
            logger.info(f"[TIER 1] Scanning Calendar: {origin} -> {dest}")
            
            try:
                # 1. Clear old cache for this route to avoid stale data
                self.db.clear_cache_for_route(origin, dest)
                
                # 2. Fetch fresh calendar data (next 330 days approx)
                # Note: get_available_dates iterates properly internally
                dates = self.api.get_available_dates(origin, dest)
                
                count = 0
                for d in dates:
                    # Update cache for each cabin class
                    if d.business_seats > 0:
                        self.db.update_cache(origin, dest, d.date, "AB", d.business_seats)
                        count += 1
                    if d.premium_seats > 0:
                        self.db.update_cache(origin, dest, d.date, "AP", d.premium_seats)
                        count += 1
                    if d.economy_seats > 0:
                        self.db.update_cache(origin, dest, d.date, "AG", d.economy_seats)
                        count += 1
                
                logger.info(f"[TIER 1] Found {count} availability slots for {origin}->{dest}")
                time.sleep(2) # Politeness delay
                
            except Exception as e:
                logger.error(f"[TIER 1] Error scanning {origin}->{dest}: {e}")
        
        logger.info("[TIER 1] Scan complete.")

    # --- Tier 2: Real-Time Verify ---
    async def run_tier2_verify(self):
        """Verify cached dates against real-time API and alert subscribers."""
        logger.info("[TIER 2] Starting Real-Time Verification...")
        subscriptions = self.db.get_subscriptions()
        
        if not subscriptions:
            return

        for sub in subscriptions:
            sub_id = sub["id"]
            chat_id = sub["chat_id"]
            origin = sub["origin"]
            dest = sub["destination"]
            cabin = sub["cabin_filter"] # AG, AP, AB or None
            saver_only = sub["saver_only"] == 1 if "saver_only" in sub.keys() else False
            
            # 1. Check cache for promising dates
            promising_dates = self.db.get_promising_dates(origin, dest, cabin)
            if not promising_dates:
                continue

            logger.info(f"[TIER 2] Sub #{sub_id} ({origin}->{dest} {cabin or 'ALL'}): Checking {len(promising_dates)} potential dates")
            
            for date_str in promising_dates:
                # Unique hash for this specific check to prevent duplicate alerts
                flight_hash = hashlib.md5(f"{origin}{dest}{date_str}{cabin}".encode()).hexdigest()
                
                if self.db.is_notification_sent(sub_id, flight_hash):
                    # We already alerted this user about this date/cabin combo
                    # Note: Ideally we check if SEATS changed, but for now simple boolean "sent"
                    continue
                
                # 2. Verify with Real-Time API (Routes/Offers)
                # 2. Verify with Real-Time API (Routes/Offers)
                try:
                    offers = []
                    fallback_mode = False
                    
                    try:
                        # Try primary API (Offers) first
                        offers = self.api.search_flights(
                            origin, dest, date_str, 
                            cabin_filter=SASSearchEngine.CABIN_CODES.get(cabin) if cabin else None
                        )
                        if not offers:
                            fallback_mode = True
                    except Exception as e:
                        logger.warning(f"[TIER 2] Primary API failed for {origin}->{dest} on {date_str}: {e}. Trying fallback...")
                        fallback_mode = True
                        
                        # Fallback to Routes API (No pricing, but confirmation of seats)
                        routes = self.api.get_route_details(origin, dest, date_str)
                        for r in routes:
                            # Map RouteInfo to dummy FlightOffer
                            # We need to check if specific cabin has seats
                            seats_available = 0
                            cabin_cls = cabin or "BUSINESS" # Default assumption if checking generic
                            
                            # Map cabin to availability key (AG, AP, AB)
                            target_code = SASSearchEngine.CABIN_CODES.get(cabin, "AB") # Default to checking Business if unknown
                            if cabin:
                                seats_available = r.availability.get(target_code, 0)
                            else:
                                # If no filter, check any
                                seats_available = sum(r.availability.values())
                                
                            if seats_available > 0:
                                offers.append(FlightOffer(
                                    origin=origin,
                                    destination=dest,
                                    date=date_str,
                                    cabin_class=cabin if cabin else "UNKNOWN",
                                    product_name="Award Seat (Price N/A)",
                                    points=0,
                                    taxes=0.0,
                                    currency="?",
                                    available_seats=seats_available,
                                    booking_class="",
                                    total_duration_minutes=r.total_time,
                                    stops=r.num_flights - 1
                                ))

                    found_match = False
                    for offer in offers:
                        if cabin and not fallback_mode and offer.cabin_class != SASSearchEngine.CABIN_CODES.get(cabin):
                            continue

                        # Skip non-saver offers if subscription requires saver only
                        if saver_only and not offer.is_saver_award:
                            continue
                            
                        # Construct Alert Message
                        price_info = ""
                        if offer.points > 0:
                            price_nok = f"({offer.cash_price:,.0f} NOK)" if offer.cash_price else ""
                            price_info = f"💎 {offer.points:,} pts + {offer.taxes:,.0f} {offer.currency} {price_nok}\n"
                        else:
                            price_info = "💎 Points/Price unavailable (API restricted)\n"
                            
                        bonus_tag = "🌟 BONUS " if offer.is_saver_award else ""
                        msg = (
                            f"✈️ <b>New {bonus_tag}Award Alert!</b>\n\n"
                            f"<b>{offer.origin} → {offer.destination}</b>\n"
                            f"📅 {offer.date}\n"
                            f"💺 {offer.product_name} ({offer.available_seats} seats)\n"
                            f"{price_info}"
                            f"⏱ {offer.total_duration_hours:.1f}h ({offer.stops} stops)"
                        )
                        
                        await self.send_alert(chat_id, msg)
                        self.db.log_notification(sub_id, flight_hash)
                        found_match = True
                        logger.info(f"[TIER 2] Alert sent to {chat_id} for {origin}->{dest} on {date_str} (Fallback: {fallback_mode})")
                        break  # One alert per date, avoid spam
                    
                    if not found_match:
                        logger.info(f"[TIER 2] Phantom availability or mismatch for {date_str}")
                        
                    time.sleep(1.0) # Rate limit
                    
                except Exception as e:
                    logger.error(f"[TIER 2] Failed to verify {origin}->{dest} on {date_str}: {e}")

# ============================================================================
# Main Loop
# ============================================================================

def main():
    import asyncio

    # Load Config
    config = Config.from_env()

    # Session file path
    session_file = "sas_session.json"

    monitor = SASMonitor(config, session_file=session_file)

    logger.info("SAS Monitor 2.0 Started")
    logger.info(f"Tier 1 Interval: {config.tier1_interval}s")
    logger.info(f"Tier 2 Interval: {config.tier2_interval}s")

    last_tier1 = 0
    last_tier2 = 0
    last_session_reload = 0
    session_reload_interval = 1800  # Reload session every 30 minutes

    while True:
        now = time.time()

        # Reload session periodically (every 30 min instead of every tick)
        if now - last_session_reload > session_reload_interval:
            logger.info("Reloading session from file...")
            monitor.api = SASSearchEngine(cookies_file=session_file)
            last_session_reload = now

        # Tier 1: Cache Warmer
        if now - last_tier1 > config.tier1_interval:
            monitor.run_tier1_scan()
            last_tier1 = now

        # Tier 2: Notify
        if now - last_tier2 > config.tier2_interval:
            asyncio.run(monitor.run_tier2_verify())
            last_tier2 = now

        time.sleep(60) # Main loop tick

if __name__ == "__main__":
    main()
