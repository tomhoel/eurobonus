import asyncio
import os
import logging
import json
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

async def capture_responses():
    load_dotenv()
    email = os.getenv("SAS_EMAIL")
    password = os.getenv("SAS_PASSWORD")
    
    browser = await uc.start()
    
    # Map to store response bodies
    responses = {}

    async def response_handler(event: uc.cdp.network.ResponseReceived):
        url = event.response.url
        if "bff" in url and "static" not in url:
            try:
                # Get response body using CDP
                body = await browser.send(uc.cdp.network.get_response_body(event.request_id))
                responses[url] = body[0] # body is a tuple (content, base64Encoded)
                logger.info(f"✅ Captured body for: {url}")
            except Exception as e:
                logger.debug(f"Could not capture body for {url}: {e}")

    try:
        page = await automated_login(browser, email, password)
        await page.send(uc.cdp.network.enable())
        page.add_handler(uc.cdp.network.ResponseReceived, response_handler)

        logger.info("Navigating to explore APIs...")
        
        # Navigate to a page that triggers many BFF calls
        await page.get("https://www.flysas.com/en")
        await page.sleep(10)
        
        await page.get("https://www.sas.no/eurobonus/min-side/")
        await page.sleep(10)

        # Save results
        with open("sas_api_responses.json", "w") as f:
            json.dump(responses, f, indent=4)
        
        logger.info(f"DONE. Captured {len(responses)} response bodies.")
        for url in responses.keys():
            print(f"CAPTURED: {url}")

    finally:
        browser.stop()

if __name__ == "__main__":
    asyncio.run(capture_responses())
