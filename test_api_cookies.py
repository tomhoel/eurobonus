#!/usr/bin/env python3
import requests
import sys

def test_availability(cookie_string):
    """
    Tests the provided cookie string by attempting to fetch award availability.
    """
    url = "https://www.sas.no/bff/award-finder/destinations/v1"
    params = {
        "market": "no-no",
        "origin": "OSL",
        "destinations": "JFK",
        "passengers": 1,
        "direct": "false",
        "availability": "true"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Cookie": cookie_string
    }
    
    print(f"Testing availability check with cookies...")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print("✅ Success! API returned data.")
                return True
            else:
                print("⚠️ API returned 200 but empty data.")
        elif response.status_code == 403:
            print("❌ Forbidden: You might still be blocked by Cloudflare or the session is invalid.")
        else:
            print(f"❓ Response: {response.text[:200]}")
    except Exception as e:
        print(f"🔥 Error: {e}")
    
    return False

if __name__ == "__main__":
    cookie_data = sys.stdin.read().strip()
    test_availability(cookie_data)
