import json
import logging
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from sas_search_api import SASSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

def fetch_date(engine, origin, destination, date):
    """Fetch availability for a single date with 429 awareness."""
    try:
        data = engine.get_partner_awards(origin, destination, date)
        if not data or "outboundFlights" not in data:
            return []
            
        flights = data.get("outboundFlights", [])
        results = []
        
        for flight in flights:
            segments = flight.get("segments", [])
            airports = []
            carriers = set()
            for s in segments:
                dep = s.get("departureAirport", {})
                airports.append(dep.get("code") if isinstance(dep, dict) else str(dep))
                carrier = s.get("operatingCarrier", {}).get("name") or s.get("marketingCarrier", {}).get("name")
                if carrier: carriers.add(carrier)
            
            if segments:
                arr = segments[-1].get("arrivalAirport", {})
                airports.append(arr.get("code") if isinstance(arr, dict) else str(arr))
            
            route = " -> ".join(airports)
            carrier_str = ", ".join(carriers)
            
            cabins = flight.get("cabins", [])
            for cabin_data in cabins:
                cabin_class = cabin_data.get("cabin", "Unknown")
                price = cabin_data.get("price", {})
                points = price.get("points")
                if points:
                    results.append({
                        "date": date,
                        "route": route,
                        "carriers": carrier_str,
                        "cabin": cabin_class.upper(),
                        "points": points,
                        "seats": cabin_data.get("availableSeats", 0)
                    })
        return results
    except Exception as e:
        if "429" in str(e):
            logger.warning(f"Rate limited (429) on {date}. Signal for long pause.")
            return "429"
        logger.error(f"Failed to fetch {date}: {e}")
        return []

def main():
    engine = SASSearchEngine(cookies_file="sas_session.json")
    origin = "CPH"
    destination = "BKK"
    
    start_date = datetime(2026, 4, 1)
    end_date = datetime(2026, 6, 30)
    
    dates = []
    curr = start_date
    while curr <= end_date:
        dates.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
        
    logger.info(f"Starting CAUTIOUS Q2 search for {origin} -> {destination} ({len(dates)} days)")
    
    all_results = []
    import random
    
    for i, date in enumerate(dates):
        day_results = fetch_date(engine, origin, destination, date)
        
        if day_results == "429":
            logger.info("🛑 429 Detected. Cooling down for 120 seconds...")
            time.sleep(120)
            # Retry once after cooling down
            day_results = fetch_date(engine, origin, destination, date)
            if day_results == "429":
                logger.error("Still 429 after cooldown. Skipping this date.")
                day_results = []
        
        if day_results:
            all_results.extend(day_results)
            for res in day_results:
                logger.info(f"✨ FOUND: {res['date']} | {res['cabin']}: {res['points']:,} pts | {res['route']} ({res['carriers']})")
        else:
            logger.info(f"Checked {date}: No flights.")
            
        # Very conservative delay: 15 seconds + jitter
        delay = 15.0 + random.random() * 5
        if i < len(dates) - 1:
            time.sleep(delay)
            if (i + 1) % 5 == 0:
                logger.info(f"Progress: {i+1}/{len(dates)} days...")


    # Final summary
    logger.info("="*50)
    logger.info(f"SEARCH COMPLETE for {origin} -> {destination}")
    logger.info(f"Checked {len(dates)} days, found {len(all_results)} flight options.")
    logger.info("="*50)
    
    if all_results:
        # Sort by points then date
        all_results.sort(key=lambda x: (x['points'], x['date']))
        
        # Save to file
        output_file = "bkk_2026_awards.json"
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=4)
        logger.info(f"Detailed results saved to {output_file}")
        
        # Print top 20 best deals
        logger.info("Top 20 availability (by points):")
        for res in all_results[:20]:
            print(f"{res['date']} | {res['cabin']:<10} | {res['points']:,} pts | {res['route']} | {res['seats']} seats")
    else:
        logger.info("No partner awards found for this route in 2026.")


if __name__ == "__main__":
    main()
