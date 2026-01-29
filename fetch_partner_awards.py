#!/usr/bin/env python3
"""
SAS SkyTeam Partner Award Search

Searches for SkyTeam partner award flights (Air France, KLM, Delta, etc.)
using EuroBonus points. Requires EuroBonus login.

API Endpoint: https://www.sas.no/award-api/flights

Usage:
    python fetch_partner_awards.py -o OSL -d TYO --date 2026-02-03
    python fetch_partner_awards.py -o CPH -d NYC --date 2026-03-15 --visible
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

# Default credentials (can be overridden via args)
DEFAULT_EMAIL = "tomhoel96@gmail.com"
DEFAULT_PASSWORD = "Jalla96man!"


async def login_and_fetch_partner_awards(
    origin: str = "OSL",
    destination: str = "TYO", 
    date: str = "2026-02-03",
    email: str = DEFAULT_EMAIL,
    password: str = DEFAULT_PASSWORD,
    headless: bool = True,
    save_json: bool = True
) -> dict:
    """
    Log in to SAS EuroBonus and fetch SkyTeam partner award availability.
    
    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        date: Departure date in YYYY-MM-DD format
        email: EuroBonus login email
        password: EuroBonus password
        headless: Run browser without visible window
        save_json: Save response to JSON file
    
    Returns:
        API response with partner award flights
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        raise

    async with async_playwright() as p:
        logger.info(f"Launching {'headless' if headless else 'visible'} browser...")
        
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="no-NO",
            timezone_id="Europe/Oslo",
        )
        
        page = await context.new_page()
        
        # Step 1: Navigate to partner bonus page (triggers login)
        logger.info("Navigating to partner bonus page...")
        await page.goto(
            "https://www.sas.no/eurobonus/poeng/bruke/partnerbonusreiser/",
            wait_until="domcontentloaded",
            timeout=30000
        )
        await page.wait_for_timeout(2000)
        
        # Step 2: Click login button if present
        logger.info("Looking for login button...")
        try:
            login_button = await page.wait_for_selector(
                'button:has-text("Logg inn"), a:has-text("Logg inn"), [data-testid="login-button"]',
                timeout=5000
            )
            if login_button:
                await login_button.click()
                await page.wait_for_timeout(2000)
        except:
            logger.info("No login button found, may already be on login page")
        
        # Step 3: Handle login form
        logger.info("Logging in...")
        try:
            # Wait for email field
            email_field = await page.wait_for_selector(
                'input[type="email"], input[name="email"], input[id="email"], input[placeholder*="e-post"]',
                timeout=10000
            )
            await email_field.fill(email)
            await page.wait_for_timeout(500)
            
            # Click continue/next if separate steps
            try:
                continue_btn = await page.wait_for_selector(
                    'button:has-text("Fortsett"), button:has-text("Continue"), button[type="submit"]',
                    timeout=3000
                )
                await continue_btn.click()
                await page.wait_for_timeout(1500)
            except:
                pass
            
            # Fill password
            password_field = await page.wait_for_selector(
                'input[type="password"], input[name="password"]',
                timeout=10000
            )
            await password_field.fill(password)
            await page.wait_for_timeout(500)
            
            # Submit login
            submit_btn = await page.wait_for_selector(
                'button:has-text("Logg inn"), button:has-text("Log in"), button[type="submit"]',
                timeout=5000
            )
            await submit_btn.click()
            
            logger.info("Waiting for login to complete...")
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            logger.warning(f"Login form handling: {e}")
        
        # Step 4: Navigate to partner award search
        logger.info("Navigating to partner award search...")
        search_url = f"https://www.sas.no/booking/award/flights?origin={origin}&destination={destination}&outboundDate={date}&tripType=one-way&adults=1"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        
        # Step 5: Make API call from browser context
        api_url = f"https://www.sas.no/award-api/flights?origin={origin}&destination={destination}&outboundDate={date}&tripType=one-way&selectedCouponCodes=&adults=1&children=0&infants=0&youths=0"
        
        logger.info(f"Fetching partner awards: {origin} → {destination} on {date}...")
        
        result = await page.evaluate(f"""
            async () => {{
                try {{
                    const response = await fetch('{api_url}');
                    if (!response.ok) {{
                        return {{ error: `HTTP ${{response.status}}`, status: response.status }};
                    }}
                    const data = await response.json();
                    return {{ success: true, data: data }};
                }} catch (e) {{
                    return {{ error: e.toString() }};
                }}
            }}
        """)
        
        await browser.close()
        
        if result.get("error"):
            logger.error(f"API error: {result['error']}")
            return {}
        
        data = result.get("data", {})
        
        # Save to JSON file
        if save_json and data:
            json_file = Path(f"partner_awards_{origin}_{destination}_{date}.json")
            json_file.write_text(json.dumps(data, indent=2, default=str))
            logger.info(f"Saved raw JSON to {json_file}")
        
        # Parse and display results
        display_partner_awards(data, origin, destination)
        
        return data


def display_partner_awards(data: dict, origin: str, destination: str):
    """Parse and display partner award results."""
    
    outbound = data.get("outboundFlights", [])
    if not outbound:
        # Try alternative structure
        outbound = data.get("flights", [])
    
    if not outbound:
        print("\n❌ No partner award flights found")
        print("   This route may not have SkyTeam partner availability")
        return
    
    print(f"\n✅ Found {len(outbound)} partner award flight(s):\n")
    
    for flight in outbound:
        if not isinstance(flight, dict):
            continue
        
        # Extract flight info
        departure = flight.get("departureDateTime", flight.get("departure", ""))[:16]
        arrival = flight.get("arrivalDateTime", flight.get("arrival", ""))[:16]
        
        # Get segments/legs
        segments = flight.get("segments", flight.get("legs", []))
        connections = len(segments) - 1 if segments else 0
        
        # Get carriers
        carriers = set()
        for seg in segments:
            if isinstance(seg, dict):
                carrier = seg.get("carrier", seg.get("operatingCarrier", ""))
                if carrier:
                    carriers.add(carrier)
        carrier_str = ", ".join(carriers) if carriers else "Unknown"
        
        # Get duration
        duration = flight.get("totalDuration", flight.get("duration", ""))
        
        # Get pricing per cabin
        cabins = flight.get("cabins", flight.get("products", []))
        
        print(f"  ✈️  {departure} → {arrival}")
        print(f"      {connections} stop(s) | {duration} | Operated by: {carrier_str}")
        
        # Display pricing by cabin
        if isinstance(cabins, list):
            for cabin in cabins:
                if isinstance(cabin, dict):
                    cabin_name = cabin.get("cabinClass", cabin.get("name", ""))
                    points = cabin.get("points", cabin.get("price", {}).get("points", 0))
                    if points:
                        print(f"      {cabin_name}: {points:,} pts")
        elif isinstance(cabins, dict):
            for cabin_name, cabin_data in cabins.items():
                if isinstance(cabin_data, dict):
                    points = cabin_data.get("points", 0)
                    if points:
                        print(f"      {cabin_name}: {points:,} pts")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Search SkyTeam partner award flights using EuroBonus points"
    )
    parser.add_argument("-o", "--origin", default="OSL", help="Origin airport code")
    parser.add_argument("-d", "--destination", default="TYO", help="Destination airport code")
    parser.add_argument("--date", default="2026-02-03", help="Departure date (YYYY-MM-DD)")
    parser.add_argument("--email", default=DEFAULT_EMAIL, help="EuroBonus login email")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="EuroBonus password")
    parser.add_argument("--visible", action="store_true", help="Show browser window")
    parser.add_argument("--no-save", action="store_true", help="Don't save JSON response")
    
    args = parser.parse_args()
    
    try:
        data = asyncio.run(login_and_fetch_partner_awards(
            origin=args.origin,
            destination=args.destination,
            date=args.date,
            email=args.email,
            password=args.password,
            headless=not args.visible,
            save_json=not args.no_save
        ))
        
        if not data:
            print("\n❌ Failed to fetch partner awards")
            print("   Try running with --visible to see what's happening")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
