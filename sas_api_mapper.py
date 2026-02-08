import asyncio
import json
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import nodriver as uc

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

# Re-use the login logic from capture_session.py
async def automated_login(browser, email, password):
    url = "https://www.flysas.com/auth/login?ui_locales=en&returnTo=%2Fen"
    logger.info(f"Navigating to {url}")
    page = await browser.get(url)
    await page.sleep(3)
    
    logger.info("Waiting for email input field...")
    email_field = None
    for _ in range(10):
        try:
            email_field = await page.select('input[name="username"]', timeout=5)
            if email_field: break
        except:
            await page.sleep(1)
            
    if not email_field:
        if "sas.no" in page.url and "auth" not in page.url:
            logger.info("Already logged in.")
            return page
        raise Exception("Could not find login email field.")
    
    await email_field.send_keys(email)
    continue_btn = await page.select('button[type="submit"]')
    await continue_btn.click()
    
    logger.info("Waiting for password input field...")
    await page.sleep(2)
    password_field = None
    for _ in range(10):
        try:
            password_field = await page.select('input[type="password"]', timeout=5)
            if not password_field:
                password_field = await page.select('input[name="password"]', timeout=5)
            if password_field: break
        except:
            await page.sleep(1)
            
    if not password_field:
        raise Exception("Could not find password input field.")
    
    await password_field.send_keys(password)
    signin_btn = await page.select('button[type="submit"]')
    await signin_btn.click()
    
    logger.info("Waiting for redirect...")
    for _ in range(60): 
        if ("sas.no" in page.url or "flysas.com" in page.url) and "auth" not in page.url:
            logger.info(f"Successfully landed on: {page.url}")
            return page
        await page.sleep(1)
    
    return page

async def map_apis():
    load_dotenv()
    email = os.getenv("SAS_EMAIL")
    password = os.getenv("SAS_PASSWORD")
    
    if not email or not password:
        logger.error("SAS_EMAIL/SAS_PASSWORD not set in .env")
        return

    logger.info("Starting browser for API mapping...")
    browser = await uc.start()
    
    # Store unique APIs found
    apis_found = {}

    def request_handler(event: uc.cdp.network.RequestWillBeSent):
        url = event.request.url
        # Filter for interesting API calls
        if any(keyword in url for keyword in ["/api/", "/bff/", "/bff-api/", "flysas.com"]):
            if url not in apis_found:
                # Store URL and method
                apis_found[url] = event.request.method
                logger.info(f"📍 New API caught: [{event.request.method}] {url}")

    try:
        page = await automated_login(browser, email, password)
        
        # Start listening to network requests on the landing page
        # Note: In nodriver, we need to enable network domain and add handler
        await page.send(uc.cdp.network.enable())
        page.add_handler(uc.cdp.network.RequestWillBeSent, request_handler)

        target_pages = [
            "https://www.sas.no/eurobonus/min-side/",      # Profile / Points
            "https://www.sas.no/eurobonus/min-side/aktiviteter/", # Activities
            "https://www.sas.no/manage-booking/",          # Manage Booking
            "https://www.sas.no/upgrade/",                 # Upgrades
            "https://www.sas.no/eurobonus/poeng/bruke/partnerbonusreiser/" # Partner search
        ]

        for url in target_pages:
            logger.info(f"🕵️ Mapping page: {url}")
            await page.get(url)
            await page.sleep(5) # Wait for backend calls to trigger
            
        # Summary
        logger.info("Finished mapping. Unique APIs found:")
        for url, method in sorted(apis_found.items()):
            print(f"[{method}] {url}")

        # Save to file
        with open("sas_api_map.json", "w") as f:
            json.dump(apis_found, f, indent=4)
        logger.info("✅ API map saved to sas_api_map.json")

    finally:
        browser.stop()

if __name__ == "__main__":
    asyncio.run(map_apis())
