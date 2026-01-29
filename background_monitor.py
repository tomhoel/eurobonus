import time
import os
import random
import logging
from datetime import datetime, timedelta
from realtime_scanner import RealTimeScanner

# Setup persistent logging for the background process
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler("monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

ALERT_FILE = "availability_alerts.txt"

def log_alert(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ALERT_FILE, "a") as f:
        f.write(f"[{timestamp}] ALERT: {message}\n")
    logger.info(f"🚨 ALERT LOGGED: {message}")

def run_monitor():
    scanner = RealTimeScanner()
    
    # Configuration: Routes to monitor and how deep to scan
    routes = [
        {"origin": "CPH", "destination": "BKK", "days": 60},
        {"origin": "OSL", "destination": "BKK", "days": 60},
        {"origin": "CPH", "destination": "TYO", "days": 60},
    ]
    
    # We keep track of what we've already alerted on in the current session
    # to avoid spamming the alert file.
    known_availability = set()

    logger.info("Starting Background Monitor (Loop: 4 hours)...")
    
    while True:
        try:
            start_scan_ts = datetime.now().strftime("%Y-%m-%d")
            
            for route in routes:
                origin = route["origin"]
                dest = route["destination"]
                days = route["days"]
                
                logger.info(f"Scanning {origin} -> {dest}...")
                
                # Proactively rotate User-Agent for each new route scan
                scanner.rotate_user_agent()
                
                found_dates = scanner.scan_range(origin, dest, start_scan_ts, days=days, silent=True)
                
                for d in found_dates:
                    alert_key = f"{origin}-{dest}-{d}"
                    if alert_key not in known_availability:
                        flights = scanner.cache.get(alert_key, {}).get("flights", [])
                        if flights:
                            route_str = flights[0]['route']
                            log_alert(f"NEW SEATS FOUND! {d} | {origin}->{dest} | Route: {route_str}")
                        known_availability.add(alert_key)
                
                # Significantly increased pause between routes (3-5 minutes)
                pause = 180 + random.randint(0, 120)
                logger.info(f"Route scan finished. Waiting {pause}s before next route...")
                time.sleep(pause)
            
            # Increased sleep to 8 hours for a much slower profile
            logger.info("Full scan cycle complete. Sleeping for 8 hours...")
            time.sleep(8 * 3600)
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            time.sleep(600) # Wait 10 mins on crash and retry

if __name__ == "__main__":
    # Create the alert file if it doesn't exist
    if not os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "w") as f:
            f.write("=== SAS REAL-TIME AVAILABILITY ALERTS ===\n")
    
    run_monitor()
