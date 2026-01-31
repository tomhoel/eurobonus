import logging
import json
from sas_search_api import SASSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

def main():
    engine = SASSearchEngine(cookies_file="sas_session.json")
    
    logger.info("Starting Comprehensive Account Health Check...")
    
    # 1. Test Base Profile (on flysas.com)
    logger.info("🧪 Testing Profile API...")
    try:
        res = engine.session.get("https://www.flysas.com/bff/profile/profiles/profile-button/v2")
        if res.status_code == 200:
            data = res.json()
            points = data.get("eb", {}).get("availablePoints", "Unknown")
            logger.info(f"✅ Profile API: SUCCESS. Points Balance: {points}")
        else:
            logger.warning(f"🛑 Profile API: FAILED ({res.status_code})")
    except Exception as e:
        logger.error(f"Profile API Error: {e}")

    # 2. Test Calendar API
    logger.info("🧪 Testing Calendar API...")
    try:
        dates = engine.get_available_dates("CPH", "NYC")
        if dates:
            logger.info(f"✅ Calendar API: SUCCESS. Found {len(dates)} dates.")
        else:
            logger.info("✅ Calendar API: SUCCESS (Empty results).")
    except Exception as e:
        logger.error(f"Calendar API Error: {e}")

    # 3. Test Standard SAS Offers API
    logger.info("🧪 Testing Standard SAS Offers API...")
    test_routes = [
        ("OSL", "CPH", "2026-03-01"),
        ("CPH", "BKK", "2026-02-11"),
        ("EWR", "CPH", "2026-04-10")
    ]
    
    for origin, dest, date in test_routes:
        try:
            logger.info(f"   Searching {origin} -> {dest} on {date}...")
            offers = engine.search_flights(origin, dest, date)
            if offers:
                logger.info(f"   ✅ SUCCESS. Found {len(offers)} offers.")
                for offer in offers[:2]:
                    logger.info(f"      - {offer.product_name}: {offer.points} pts, {offer.available_seats} seats")
                break # Found some, we're good
            else:
                logger.info(f"   ℹ️ No availability for {origin} -> {dest}")
        except Exception as e:
            logger.error(f"   ❌ Offers API Error ({origin}-{dest}): {e}")

if __name__ == "__main__":
    main()
