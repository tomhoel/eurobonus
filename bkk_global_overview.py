import json
import logging
import time
import random
from datetime import datetime
from sas_search_api import SASSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

class BKKGlobalScanner:
    def __init__(self, route_map_file="sas_route_map.json"):
        # Use no-auth for now to avoid using the flagged session
        self.engine = SASSearchEngine() 
        self.route_map_file = route_map_file
        self.findings = []

    def get_origins_for_bkk(self):
        """Finds all origins that fly to BKK from the saved route map."""
        try:
            with open(self.route_map_file, "r") as f:
                data = json.load(f)
            
            origins = []
            for origin, destinations in data.get("routes", {}).items():
                if any(d['code'] == 'BKK' for d in destinations):
                    origins.append(origin)
            
            return origins
        except Exception as e:
            logger.error(f"Error loading route map: {e}")
            return []

    def scan_all_to_bkk(self, target_year="2026"):
        origins = self.get_origins_for_bkk()
        logger.info(f"📍 Found {len(origins)} potential origins flying TO Bangkok.")
        
        for origin in origins:
            logger.info(f"🔍 Probing calendar for {origin} -> BKK...")
            
            try:
                # get_availability_calendar returns a list of destination objects
                # destinations="BKK" filters it at the API level
                data = self.engine.get_availability_calendar(origin=origin, destination="BKK")
                
                if not data:
                    continue
                
                # The data structure is a list with one item for BKK
                bkk_data = data[0] if data else {}
                availability = bkk_data.get("availability", {}).get("outbound", [])
                
                for day in availability:
                    if day['date'].startswith(target_year):
                        # Only keep if there is at least one seat in any class
                        if day.get('AG', 0) > 0 or day.get('AP', 0) > 0 or day.get('AB', 0) > 0:
                            self.findings.append({
                                "origin": origin,
                                "date": day['date'],
                                "AG": day.get('AG', 0),
                                "AP": day.get('AP', 0),
                                "AB": day.get('AB', 0)
                            })
                
                # Safety delay between origins
                time.sleep(random.uniform(3.0, 6.0))
                
            except Exception as e:
                logger.error(f"   ❌ Failed to probe {origin}: {e}")

    def print_summary(self):
        if not self.findings:
            print("\n❌ No award availability found for Bangkok in 2026 via the Calendar API.")
            return

        print("\n" + "="*70)
        print(f"{'DATE':<12} | {'ORIGIN':<10} | {'ECON (AG)':<10} | {'PLUS (AP)':<10} | {'BIZ (AB)':<10}")
        print("-" * 70)
        
        # Sort by date, then origin
        sorted_findings = sorted(self.findings, key=lambda x: (x['date'], x['origin']))
        
        for f in sorted_findings:
            print(f"{f['date']:<12} | {f['origin']:<10} | {f['AG']:<10} | {f['AP']:<10} | {f['AB']:<10}")
        
        print("="*70)
        print(f"Total findings: {len(self.findings)}")
        print("NOTE: This data is CACHED DAILY. High-value seats (Business) should be verified with the real-time API.")

if __name__ == "__main__":
    scanner = BKKGlobalScanner()
    logger.info("🚀 Starting 2026 Global Bangkok Search (Cached Calendar)...")
    scanner.scan_all_to_bkk()
    scanner.print_summary()
