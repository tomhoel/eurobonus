#!/usr/bin/env python3
"""
SAS Cookie Fetcher

Uses Playwright to emulate a real browser and fetch fresh session cookies
for the SAS offers API (which requires Cloudflare bypass).

Usage:
    python fetch_cookies.py              # Headless mode
    python fetch_cookies.py --visible    # Show browser window
    python fetch_cookies.py --output cookies.txt
"""

import argparse
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)


async def fetch_sas_cookies(headless: bool = True, output_file: str = "cookies.txt") -> str:
    """
    Launch a browser, navigate to SAS.no, and extract session cookies.
    
    Args:
        headless: Run browser without visible window
        output_file: Path to save cookies
        
    Returns:
        Cookie string ready for API requests
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
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )
        
        # Create context with realistic browser fingerprint
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="no-NO",
            timezone_id="Europe/Oslo",
        )
        
        page = await context.new_page()
        
        # First visit homepage to establish session
        logger.info("Navigating to SAS.no homepage...")
        try:
            await page.goto("https://www.sas.no/", wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            logger.warning(f"Homepage load warning: {e}")
        
        # Wait for initial cookies
        await page.wait_for_timeout(3000)
        
        # Now visit a simpler page to get more cookies
        logger.info("Loading award search page...")
        try:
            await page.goto(
                "https://www.sas.no/eurobonus/",
                wait_until="domcontentloaded",
                timeout=30000
            )
        except Exception as e:
            logger.warning(f"EuroBonus page warning: {e}")
        
        await page.wait_for_timeout(3000)
        
        # Try the booking page (but don't wait for full load)
        logger.info("Loading booking page...")
        try:
            await page.goto(
                "https://www.sas.no/book/flights/?search=OW_OSL-BKK-20260301_a1c0i0y0&view=upsell&bookingFlow=points",
                wait_until="commit",  # Just wait for initial response
                timeout=30000
            )
            # Give it a few seconds to set cookies
            await page.wait_for_timeout(8000)
        except Exception as e:
            logger.warning(f"Booking page warning: {e}")
        
        # Get all cookies
        cookies = await context.cookies()
        
        await browser.close()
        
        if not cookies:
            logger.error("No cookies were captured")
            return ""
        
        # Format cookies as a single string
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
        # Save to file
        output_path = Path(output_file)
        output_path.write_text(cookie_str + "\n")
        
        logger.info(f"✅ Saved {len(cookies)} cookies to {output_path}")
        logger.info(f"   Cookie names: {', '.join(c['name'] for c in cookies[:5])}...")
        
        return cookie_str


def main():
    parser = argparse.ArgumentParser(description="Fetch fresh SAS cookies using browser automation")
    parser.add_argument("--visible", action="store_true", help="Show browser window")
    parser.add_argument("--output", "-o", default="cookies.txt", help="Output file path")
    parser.add_argument("--fetch-offers", action="store_true", 
                       help="Fetch flight offers directly from browser (bypasses Cloudflare)")
    parser.add_argument("--origin", default="OSL", help="Origin airport (with --fetch-offers)")
    parser.add_argument("--destination", default="BKK", help="Destination airport (with --fetch-offers)")
    parser.add_argument("--date", default="20260205", help="Date YYYYMMDD (with --fetch-offers)")
    args = parser.parse_args()
    
    if args.fetch_offers:
        # Fetch offers directly from browser context
        asyncio.run(fetch_offers_via_browser(
            origin=args.origin,
            destination=args.destination,
            date=args.date,
            headless=not args.visible
        ))
        return 0
    
    try:
        cookie_str = asyncio.run(fetch_sas_cookies(
            headless=not args.visible,
            output_file=args.output
        ))
        
        if cookie_str:
            print(f"\n🍪 Cookie string preview (first 200 chars):\n{cookie_str[:200]}...")
            print(f"\n✅ Cookies saved to {args.output}")
            print("   You can now use: python sas_search_api.py --cookies cookies.txt")
        else:
            print("\n❌ Failed to capture cookies")
            return 1
            
    except ImportError:
        print("\n❌ Playwright not installed. Run these commands:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


async def fetch_offers_via_browser(
    origin: str = "OSL",
    destination: str = "BKK",
    date: str = "20260205",
    headless: bool = True
) -> dict:
    """
    Fetch flight offers by making the API call from within the browser.
    This bypasses Cloudflare since the call comes from a real browser session.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed")
        raise
    
    async with async_playwright() as p:
        logger.info(f"Launching browser to fetch offers...")
        
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="no-NO",
        )
        
        page = await context.new_page()
        
        # First establish session by visiting homepage
        logger.info("Establishing session...")
        await page.goto("https://www.sas.no/", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Now make the API call from within the browser
        api_url = f"https://www.sas.no/api/offers/flights?from={origin}&to={destination}&outDate={date}&adt=1&chd=0&inf=0&yth=0&bookingFlow=points&pos=no&channel=web&displayType=upsell"
        
        logger.info(f"Fetching offers: {origin} → {destination} on {date}...")
        
        # Execute fetch from within the browser context
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
        outbound = data.get("outboundFlights", {})
        
        # Save raw JSON for debugging
        import json
        from pathlib import Path
        json_output = Path("last_offers_response.json")
        json_output.write_text(json.dumps(data, indent=2, default=str))
        logger.info(f"Saved raw JSON to {json_output}")
        
        if not outbound:
            print("\n❌ No flights found")
            return data
        
        print(f"\n✅ Found {len(outbound)} flight option(s):\n")
        
        for flight_id, flight in outbound.items():
            if not isinstance(flight, dict):
                continue
                
            segments = flight.get("segments", [])
            
            # Build route string - airports are dicts with 'code' key
            try:
                if segments and isinstance(segments, list):
                    airports = []
                    for s in segments:
                        if isinstance(s, dict):
                            dep_airport = s.get("departureAirport", {})
                            if isinstance(dep_airport, dict):
                                airports.append(dep_airport.get("code", "?"))
                            else:
                                airports.append(str(dep_airport)[:3])
                    # Add final destination
                    if segments and isinstance(segments[-1], dict):
                        arr_airport = segments[-1].get("arrivalAirport", {})
                        if isinstance(arr_airport, dict):
                            airports.append(arr_airport.get("code", destination))
                        else:
                            airports.append(str(arr_airport)[:3] if arr_airport else destination)
                    route = " → ".join(airports) if airports else destination
                else:
                    route = destination
            except Exception:
                route = destination
            
            # Get flight times
            start_time = flight.get("startTimeInLocal", "")[:16] if flight.get("startTimeInLocal") else ""
            end_time = flight.get("endTimeInLocal", "")[:16] if flight.get("endTimeInLocal") else ""
            stops = flight.get("stops", 0)
            
            # Cabins is a nested dict: cabins[CLASS][PRODUCT_TYPE].products[ID].price
            cabins = flight.get("cabins", {})
            
            if not cabins or not isinstance(cabins, dict):
                # No cabins data - just show route info
                print(f"  Route: {route} | Stops: {stops}")
                print(f"       Times: {start_time} → {end_time}")
                print()
                continue
            
            # Traverse: cabins -> CABIN_CLASS -> PRODUCT_TYPE -> products -> PRODUCT_ID
            for cabin_class, cabin_products in cabins.items():
                if not isinstance(cabin_products, dict):
                    continue
                    
                for product_type, product_data in cabin_products.items():
                    if not isinstance(product_data, dict):
                        continue
                    
                    products = product_data.get("products", {})
                    if not isinstance(products, dict):
                        continue
                    
                    for product_id, product in products.items():
                        if not isinstance(product, dict):
                            continue
                        
                        price = product.get("price", {})
                        if not isinstance(price, dict):
                            continue
                        
                        points = price.get("points", 0)
                        tax = price.get("totalTax", 0)
                        
                        if points:
                            product_name = product.get("productName", product_type)
                            print(f"  {cabin_class}: {points:,} pts + {tax:.0f} NOK")
                            print(f"       {product_name} | {route}")
                            print()
                            break  # Only show one product per cabin type
                    break  # Only show first product type per cabin
        
        return data


if __name__ == "__main__":
    exit(main())

