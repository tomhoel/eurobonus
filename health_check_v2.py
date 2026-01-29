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
            logger.info(f"✅ Profile API: SUCCESS. Points Balance: {data.get('pointsBalance', 'Unknown')}")
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

    # 3. Test Partner API (The sensitive one)
    logger.info("🧪 Testing Partner API (Real-time)...")
    try:
        data = engine.get_partner_awards("CPH", "NYC", "2026-03-01")
        if "outboundFlights" in data:
            logger.info("✅ Partner API: SUCCESS.")
        elif "error" in str(data) or "429" in str(data):
            logger.warning(f"🛑 Partner API: FLAGGED/FAILED. Response: {data}")
        else:
            logger.info(f"✅ Partner API: SUCCESS (Response received: {list(data.keys())})")
    except Exception as e:
        logger.error(f"Partner API Error: {e}")

if __name__ == "__main__":
    main()
