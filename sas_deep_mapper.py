import asyncio
import json
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import nodriver as uc

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

async def automated_login(browser, email, password):
    url = "https://www.flysas.com/auth/login?ui_locales=en&returnTo=%2Fen"
    page = await browser.get(url)
    await page.sleep(5)
    
    email_field = await page.select('input[name="username"]', timeout=10)
    await email_field.send_keys(email)
    continue_btn = await page.select('button[type="submit"]')
    await continue_btn.click()
    
    await page.sleep(3)
    password_field = await page.select('input[type="password"]', timeout=10)
    await password_field.send_keys(password)
    signin_btn = await page.select('button[type="submit"]')
    await signin_btn.click()
    
    for _ in range(60): 
        if ("sas.no" in page.url or "flysas.com" in page.url) and "auth" not in page.url:
            return page
        await page.sleep(1)
    return page

async def deep_map():
    load_dotenv()
    email = os.getenv("SAS_EMAIL")
    password = os.getenv("SAS_PASSWORD")
    
    browser = await uc.start()
    apis_found = []

    def response_handler(event: uc.cdp.network.ResponseReceived):
        url = event.response.url
        if any(kw in url for kw in ["/api/", "/bff/", "eurobonus", "points", "profile"]):
            if "static" not in url and ".js" not in url and ".css" not in url:
                api_info = {
                    "url": url,
                    "method": "???", # ResponseReceived doesn't have method directly, but we can infer or use RequestWillBeSent
                    "status": event.response.status,
                    "mimeType": event.response.mime_type
                }
                apis_found.append(api_info)
                logger.info(f"✨ Catch: {url}")

    try:
        page = await automated_login(browser, email, password)
        await page.send(uc.cdp.network.enable())
        page.add_handler(uc.cdp.network.ResponseReceived, response_handler)

        logger.info("🚀 Starting deep dive into EuroBonus sections...")
        
        # Navigate to the main EuroBonus dashboard
        await page.get("https://www.sas.no/eurobonus/min-side/")
        await page.sleep(10)
        
        # Navigate to points activities (very interesting for users)
        await page.get("https://www.sas.no/eurobonus/min-side/aktiviteter/")
        await page.sleep(10)
        
        # Navigate to "Profile" details
        await page.get("https://www.sas.no/eurobonus/min-side/profil/")
        await page.sleep(10)

        # Navigate to "Upgrades"
        await page.get("https://www.sas.no/upgrade/")
        await page.sleep(10)

        # Filter and deduplicate
        unique_apis = {a['url']: a for a in apis_found}.values()
        
        with open("sas_detailed_api_map.json", "w") as f:
            json.dump(list(unique_apis), f, indent=4)
            
        logger.info(f"✅ Deep map saved to sas_detailed_api_map.json. Caught {len(unique_apis)} endpoints.")

    finally:
        browser.stop()

if __name__ == "__main__":
    asyncio.run(deep_map())
