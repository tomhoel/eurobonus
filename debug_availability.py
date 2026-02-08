import json
import logging
from sas_search_api import SASSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

def compare_availability():
    engine = SASSearchEngine(cookies_file="sas_session.json")
    origin = "CPH"
    destination = "BKK"
    date = "2026-02-11"

    logger.info(f"--- COMPARISON FOR {origin} -> {destination} ON {date} ---")

    # 1. Check cached Calendar API (via destinations/v1)
    # We simulate what the calendar sees
    logger.info("Checking Cached Calendar API...")
    calendar_url = f"https://www.sas.no/bff/award-finder/destinations/v1?market=no-no&origin={origin}&destinations={destination}&passengers=1&availability=true"
    # We use engine.session to benefit from cookies
    try:
        res = engine.session.get(calendar_url)
        data = res.json()
        month_data = [d for d in data[0]['availability']['outbound'] if d['date'] == date]
        if month_data:
            logger.info(f"📅 Calendar says for {date}: {month_data[0]}")
        else:
            logger.info(f"❌ Calendar shows NOTHING for {date}")
    except Exception as e:
        logger.error(f"Calendar check failed: {e}")

    # 2. Check Real-Time Partner API (award-api)
    logger.info("\nChecking Real-Time Partner API...")
    try:
        partner_data = engine.get_partner_awards(origin, destination, date)
        flights = partner_data.get("outboundFlights", [])
        if flights:
            logger.info(f"✅ Real-Time Partner API found {len(flights)} flight options!")
            for f in flights:
                route = " -> ".join([s['departureAirport']['code'] for s in f['segments']] + [f['segments'][-1]['arrivalAirport']['code']])
                logger.info(f"   Flight: {route}")
        else:
            logger.info("❌ Real-Time Partner API found nothing.")
    except Exception as e:
        logger.error(f"Partner API check failed: {e}")

if __name__ == "__main__":
    compare_availability()
