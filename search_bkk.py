from sas_search_api import SASSearchEngine
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

def main():
    engine = SASSearchEngine(cookies_file="sas_session.json")
    
    origins = ["CPH", "OSL", "AMS", "CDG", "LHR"]
    destination = "BKK"
    date = "2026-05-15"
    
    logger.info(f"Searching for partner awards to {destination} on {date} from various origins...")
    
    for origin in origins:
        logger.info(f"--- Checking {origin} -> {destination} ---")
        try:
            data = engine.get_partner_awards(origin, destination, date)
            flights = data.get("outboundFlights", [])
            
            if not flights:
                logger.info(f"No flights found for {origin}.")
                continue
                
            for flight in flights:
                segments = flight.get("segments", [])
                airports = []
                for s in segments:
                    dep = s.get("departureAirport", {})
                    airports.append(dep.get("code") if isinstance(dep, dict) else str(dep))
                if segments:
                    arr = segments[-1].get("arrivalAirport", {})
                    airports.append(arr.get("code") if isinstance(arr, dict) else str(arr))
                
                route = " -> ".join(airports)
                
                cabins = flight.get("cabins", [])
                for cabin in cabins:
                    cabin_class = cabin.get("cabin", "Unknown")
                    points = cabin.get("price", {}).get("points")
                    seats = cabin.get("availableSeats", 0)
                    if points:
                        print(f"✅ {origin} -> {destination} | {cabin_class.upper()}: {points:,} pts | {route} ({seats} seats)")
        except Exception as e:
            logger.error(f"Error checking {origin}: {e}")

if __name__ == "__main__":
    main()
