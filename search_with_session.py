import json
import logging
from sas_search_api import SASSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

def main():
    # Initialize engine with the captured session JSON
    # This automatically loads cookies and session headers
    engine = SASSearchEngine(cookies_file="sas_session.json")
    
    origin = "CPH"
    destination = "TYO"
    date = "2026-02-03"
    
    logger.info(f"Searching partner awards using SASSearchEngine: {origin} -> {destination} on {date}")
    
    # Use the new partner award method
    try:
        data = engine.get_partner_awards(origin, destination, date)
        
        flights = data.get("outboundFlights", [])
        if not flights:
            logger.info("No flights found for this date/route.")
            return
            
        logger.info(f"✅ Found {len(flights)} flight options:")
        
        for flight in flights:
            segments = flight.get("segments", [])
            # In this API, airports are dicts: {"code": "CPH", "name": "..."}
            airports = []
            for s in segments:
                dep = s.get("departureAirport", {})
                airports.append(dep.get("code") if isinstance(dep, dict) else str(dep))
            
            if segments:
                arr = segments[-1].get("arrivalAirport", {})
                airports.append(arr.get("code") if isinstance(arr, dict) else str(arr))
            
            route = " -> ".join(airports)
            
            # Extract points (structure in partner API: cabins is a list)
            cabins = flight.get("cabins", [])
            for cabin_data in cabins:
                cabin_class = cabin_data.get("cabin", "Unknown")
                price = cabin_data.get("price", {})
                points = price.get("points")
                if points:
                    logger.info(f"  {cabin_class.upper()}: {points:,} pts | {route}")
    except Exception as e:
        logger.error(f"Search failed: {e}")

if __name__ == "__main__":
    main()
