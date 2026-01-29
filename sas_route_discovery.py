import json
import logging
import time
import random
from sas_search_api import SASSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

class SASRouteDiscovery:
    def __init__(self, cookies_file="sas_session.json"):
        self.engine = SASSearchEngine(cookies_file=cookies_file)
        self.output_file = "sas_route_map.json"
        
        # Primary hubs to discover routes from
        self.primary_origins = ["OSL", "ARN", "CPH", "BGO", "SVG", "TRD", "EWR", "LAX", "SFO", "ORD", "MIA", "BKK", "HND", "CDG", "LHR"]

    def discover_all_routes(self, limit=100):
        """
        Recursively discovers all connected routes in the SAS network.
        Starts with hubs and follows every new destination discovered.
        """
        route_map = {}
        to_probe = list(self.primary_origins)
        probed = set()
        all_unique_airports = set()
        
        logger.info(f"🚀 Starting RECURSIVE discovery...")
        
        while to_probe and len(probed) < limit:
            origin = to_probe.pop(0)
            if origin in probed:
                continue
                
            logger.info(f"🔍 [{len(probed)+1}/{limit}] Probing: {origin} (Queue: {len(to_probe)})")
            
            try:
                url = f"{self.engine.DESTINATIONS_URL}?market=no-no&origin={origin}&passengers=1&availability=false"
                res = self.engine.session.get(url, timeout=20)
                res.raise_for_status()
                
                dest_list = res.json()
                destinations = []
                
                for item in dest_list:
                    code = item.get("iataCode") or item.get("airportCode")
                    if code:
                        destinations.append({
                            "code": code,
                            "name": item.get("cityName", ""),
                            "country": item.get("countryName", "")
                        })
                        all_unique_airports.add(code)
                        # Add new discovery to queue if not probed
                        if code not in probed and code not in to_probe:
                            to_probe.append(code)
                
                route_map[origin] = destinations
                probed.add(origin)
                logger.info(f"   ✅ Found {len(destinations)} destinations. Total unique: {len(all_unique_airports)}")
                
                # Discovery is light, but we still jitter
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                logger.error(f"   ❌ Failed to fetch from {origin}: {e}")
                probed.add(origin) # Don't retry failures in this loop

        # Save the map
        final_data = {
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "origins_probed": len(route_map),
            "total_unique_destinations": len(all_unique_airports),
            "routes": route_map
        }
        
        with open(self.output_file, "w") as f:
            json.dump(final_data, f, indent=4)
            
        logger.info(f"✅ Route map saved to {self.output_file}")
        return final_data

    def get_route_pairs(self):
        """Returns a flat list of (origin, destination) tuples."""
        try:
            with open(self.output_file, "r") as f:
                data = json.load(f)
            
            pairs = []
            for origin, destinations in data["routes"].items():
                for dest in destinations:
                    pairs.append((origin, dest["code"]))
            return pairs
        except FileNotFoundError:
            return []

if __name__ == "__main__":
    import sys
    use_auth = "--no-auth" not in sys.argv
    
    cookies = "sas_session.json" if use_auth else None
    discovery = SASRouteDiscovery(cookies_file=cookies)
    
    discovery.discover_all_routes()
