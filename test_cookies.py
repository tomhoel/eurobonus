#!/usr/bin/env python3
import requests
import sys

def test_cookies(cookie_string):
    """
    Tests the provided cookie string by attempting to fetch the SAS profile.
    """
    url = "https://www.sas.no/bff/profile/v1/customer"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Cookie": cookie_string
    }
    
    print(f"Testing cookies against: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            profile = response.json()
            name = profile.get("customer", {}).get("firstName", "User")
            points = profile.get("eurobonus", {}).get("totalPoints", "unknown")
            print(f"✅ Success! Logged in as: {name}")
            print(f"Points balance: {points}")
            return True
        elif response.status_code == 401:
            print("❌ Unauthorized: The cookies are invalid or expired.")
        else:
            print(f"❓ Unexpected status code: {response.status_code}")
            # print(response.text)
    except Exception as e:
        print(f"🔥 Error: {e}")
    
    return False

if __name__ == "__main__":
    # We read from stdin to avoid shell argument length limits
    cookie_data = sys.stdin.read().strip()
    test_cookies(cookie_data)
