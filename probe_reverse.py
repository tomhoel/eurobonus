import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def probe_reverse_search():
    # Attempting to query with empty origin
    url = "https://www.sas.no/bff/award-finder/destinations/v1"
    
    # 1. Empty origin
    params_empty = {
        "market": "no-no",
        "origin": "",
        "destinations": "BKK",
        "passengers": "1"
    }
    
    # 2. Origin as the destination (doesn't make sense but testing API flexibility)
    params_bkk = {
        "market": "no-no",
        "origin": "BKK",
        "destinations": "",
        "passengers": "1"
    }

    logger.info("Testing Empty Origin...")
    try:
        res = requests.get(url, params=params_empty, timeout=10)
        logger.info(f"Empty Origin Status: {res.status_code}")
        if res.status_code == 200:
            logger.info("✅ SUCCESS! Empty origin works. Sample keys: " + str(list(res.json()[0].keys()) if res.json() else "Empty list"))
    except Exception as e:
        logger.error(f"Failed: {e}")

    logger.info("\nTesting BKK as Origin (Discovery)...")
    try:
        res = requests.get(url, params=params_bkk, timeout=10)
        logger.info(f"BKK Origin Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            logger.info(f"✅ SUCCESS! Found {len(data)} routes leaving BKK.")
    except Exception as e:
        logger.error(f"Failed: {e}")

if __name__ == "__main__":
    probe_reverse_search()
