import logging
import json
from sas_search_api import SASSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

def test_endpoint(name, url, session, is_post=False):
    logger.info(f"🧪 Testing {name}...")
    try:
        if is_post:
            response = session.post(url, timeout=15)
        else:
            response = session.get(url, timeout=15)
        
        status = response.status_code
        if status == 200:
            logger.info(f"✅ {name}: SUCCESS (200)")
            return True
        elif status == 429:
            logger.warning(f"🛑 {name}: FLAG DETECTED (429 - Too Many Requests)")
        elif status == 403:
            logger.warning(f"🛑 {name}: FLAG DETECTED (403 - Forbidden/Cloudflare)")
        else:
            logger.warning(f"⚠️ {name}: UNEXPECTED STATUS ({status})")
    except Exception as e:
        logger.error(f"❌ {name}: REQUEST FAILED ({e})")
    return False

def main():
    engine = SASSearchEngine(cookies_file="sas_session.json")
    session = engine.session
    
    # Test cases: one small request for each major endpoint category
    tests = [
        ("Calendar API", "GET", "https://www.sas.no/bff/award-finder/destinations/v1?market=no-no&origin=OSL&destinations=CPH&passengers=1&availability=true"),
        ("Routes API", "GET", "https://www.sas.no/bff/award-finder/routes/v1?market=no-no&origin=OSL&destination=CPH&departureDate=2026-03-01"),
        ("Partner API", "GET", "https://www.sas.no/award-api/flights?origin=CPH&destination=NYC&outboundDate=2026-03-01&tripType=one-way&adults=1"),
        ("Profile API", "GET", "https://www.flysas.com/bff/profile/profiles/profile-button/v2"),
        ("Session Validate", "POST", "https://www.sas.no/api/session/validate")
    ]
    
    logger.info("Starting Account Health Check...")
    results = {}
    for name, method, url in tests:
        if method == "POST":
            results[name] = test_endpoint(name, url, session, is_post=True)
        else:
            results[name] = test_endpoint(name, url, session)
    
    success_count = sum(1 for r in results.values() if r)
    logger.info("="*50)
    if success_count == len(tests):
        logger.info("🎉 HEALTH CHECK PASSED: Account looks healthy!")
    elif success_count == 0:
        logger.error("🛑 ALL APIS FAILED: Account or Session is likely blocked.")
    else:
        logger.warning(f"⚠️ PARTIAL FAILURE: {success_count}/{len(tests)} APIs functional.")
    logger.info("="*50)

if __name__ == "__main__":
    main()
