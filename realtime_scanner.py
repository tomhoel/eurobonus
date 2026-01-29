import json
import logging
import time
import os
import random
from datetime import datetime, timedelta
from sas_search_api import SASSearchEngine

# Configure logging to show progress clearly
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler("scanner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealTimeScanner:
    def __init__(self, cookies_file="sas_session.json"):
        self.engine = SASSearchEngine(cookies_file=cookies_file)
        self.results_file = "scanned_tickets.json"
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.results_file):
            with open(self.results_file, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        with open(self.results_file, "w") as f:
            json.dump(self.cache, f, indent=4)

    def rotate_user_agent(self):
        """Proxy to rotate the internal engine's User-Agent."""
        self.engine.rotate_user_agent()

    def scan_range(self, origin, destination, start_date_str, days=30, silent=False):
        """
        Deep scan a range of dates using the REAL-TIME API.
        Returns a list of dates that have availability.
        """
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        
        if not silent:
            logger.info(f"🚀 STARTING DEEP SCAN: {origin} -> {destination}")
            logger.info(f"Scanning {days} days starting from {start_date_str}")
        
        found_dates = []
        
        for i in range(days):
            current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Skip if already scanned in the last hour to save rate hits
            key = f"{origin}-{destination}-{current_date}"
            if key in self.cache:
                last_ts = datetime.fromisoformat(self.cache[key]["last_scanned"])
                if (datetime.now() - last_ts).total_seconds() < 3600: # 1 hour TTL
                    continue

            # Rate limiting / Jitter
            if i > 0:
                time.sleep(random.uniform(8.0, 15.0))

            if not silent:
                logger.info(f"🔍 Probing {current_date}...")
            
            try:
                data = self.engine.get_partner_awards(origin, destination, current_date)
                flights = f_list = data.get("outboundFlights", [])
                
                # Update cache
                self.cache[key] = {
                    "last_scanned": datetime.now().isoformat(),
                    "flights": self._simplify_flights(f_list)
                }
                
                if f_list:
                    found_dates.append(current_date)
                    if not silent:
                        logger.info(f"   ✅ FOUND {len(f_list)} options")
                
                self._save_cache()

            except Exception as e:
                if "429" in str(e):
                    logger.error("🛑 RATE LIMITED. Pausing...")
                    return found_dates
                if not silent:
                    logger.error(f"Error on {current_date}: {e}")

        return found_dates

    def _simplify_flights(self, flights):
        """Extract only the essential info for the overview."""
        simple = []
        for f in flights:
            segments = f.get("segments", [])
            route = " -> ".join([s['departureAirport']['code'] for s in segments] + [segments[-1]['arrivalAirport']['code']])
            
            pricing = {}
            for cabin in f.get("cabins", []):
                name = cabin.get("cabin", "UNKNOWN")
                pts = cabin.get("price", {}).get("points", 0)
                seats = cabin.get("availableSeats", 0)
                if pts:
                    pricing[name] = {"points": pts, "seats": seats}
            
            simple.append({
                "route": route,
                "segments": len(segments),
                "pricing": pricing
            })
        return simple

    def print_summary(self):
        """Prints a human-readable overview of all cached real-time findings."""
        print("\n" + "="*80)
        print(f"{'DATE':<12} | {'ROUTE':<25} | {'CABIN':<10} | {'POINTS':<10} | {'SEATS':<5}")
        print("-" * 80)
        
        sorted_keys = sorted(self.cache.keys())
        for key in sorted_keys:
            data = self.cache[key]
            date = key.split("-")[-1]
            if not data["flights"]:
                continue
                
            for f in data["flights"]:
                for cabin, price in f["pricing"].items():
                    print(f"{date:<12} | {f['route']:<25} | {cabin:<10} | {price['points']:<10,} | {price['seats']:<5}")
        print("="*80 + "\n")

if __name__ == "__main__":
    scanner = RealTimeScanner()
    # Test with Feb 11th range
    scanner.scan_range("CPH", "BKK", "2026-02-10", days=5)
    scanner.print_summary()
