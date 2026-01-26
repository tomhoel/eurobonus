#!/usr/bin/env python3
import requests
import sys

def test_token(token):
    """
    Tests a SAS customer-token by attempting to fetch basic user profile info.
    """
    # Note: The exact endpoint might vary, but this is a common one for profile info
    url = "https://www.sas.no/bff/profile/v1/customer"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    print(f"Testing token against: {url}")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("✅ Success! Token is valid.")
            print("Profile Info:", response.json().get("firstName", "Unknown User"))
            return True
        elif response.status_code == 401:
            print("❌ Unauthorized: The token is invalid or expired.")
        else:
            print(f"❓ Unexpected status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"🔥 Error: {e}")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_session.py <YOUR_BEARER_TOKEN>")
        sys.exit(1)
    
    test_token(sys.argv[1])
