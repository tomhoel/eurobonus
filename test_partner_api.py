import requests
import json
import logging
from sas_session_manager import SASSessionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

def test_partner_search():
    # Load session
    manager = SASSessionManager()
    cookies = manager.get_cookie_dict()
    
    if not cookies:
        logger.error("No cookies found in sas_session.json. Please run capture_session.py first.")
        return

    # Partner API URL (based on user request)
    url = "https://www.sas.no/award-api/flights"
    params = {
        "origin": "CPH",
        "destination": "TYO",
        "outboundDate": "2026-02-03",
        "tripType": "one-way",
        "selectedCouponCodes": "",
        "adults": 1,
        "children": 0,
        "infants": 0,
        "youths": 0
    }
    
    headers = {
        "User-Agent": manager.get_user_agent(),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "no-NO,no;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.sas.no/booking/award/flights",
        "sas-user-session-id": cookies.get("session_id", ""),
        "channel": "WEB",
        "pos": "NO",
    }
    
    logger.info(f"Searching partner awards: {params['origin']} -> {params['destination']} on {params['outboundDate']}...")
    
    try:
        response = requests.get(url, params=params, cookies=cookies, headers=headers, timeout=30)
        
        if response.status_code == 200:
            logger.info("✅ Successfully fetched partner awards!")
            data = response.json()
            
            # Save for inspection
            with open("partner_api_response.json", "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Saved response to partner_api_response.json")
            
            # Simple summary
            flights = data.get("outboundFlights", [])
            logger.info(f"Found {len(flights)} flight options.")
            
        else:
            logger.error(f"❌ Failed to fetch partner awards. Status: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            
    except Exception as e:
        logger.error(f"Error during API request: {e}")

if __name__ == "__main__":
    test_partner_search()
