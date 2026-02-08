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
            logger.info(f"Landed on {page.url}")
            return page
        await page.sleep(1)
    return page

async def probe_apis():
    load_dotenv()
    email = os.getenv("SAS_EMAIL")
    password = os.getenv("SAS_PASSWORD")
    
    browser = await uc.start()
    probe_results = {}

    try:
        page = await automated_login(browser, email, password)
        # Ensure we are on flysas.com for BFF calls
        if "flysas.com" not in page.url:
            await page.get("https://www.flysas.com/en")
            await page.sleep(5)

        candidates = [
            "https://www.flysas.com/bff/profile/profiles/v1",
            "https://www.flysas.com/bff/profile/profiles/profile-button/v2",
            "https://www.flysas.com/bff/profile/eurobonus/account-info/v1",
            "https://www.flysas.com/bff/profile/eurobonus/is-eurobonus-member/v1",
            "https://www.flysas.com/bff/profile/eurobonus/points/v1",
            "https://www.flysas.com/bff/profile/eurobonus/transactions/v1",
            "https://www.flysas.com/bff/profile/eurobonus/member-details/v1",
            "https://www.flysas.com/bff/bookings/v1/trips"
        ]

        logger.info("🧪 Probing...")
        
        for url in candidates:
            logger.info(f"Probing: {url}")
            try:
                # Using a more robust evaluate
                result = await page.evaluate(f"""
                    (async () => {{
                        try {{
                            const res = await fetch('{url}');
                            return {{ status: res.status, ok: res.ok }};
                        }} catch (e) {{
                            return {{ error: e.toString() }};
                        }}
                    }})()
                """)
                if result:
                    probe_results[url] = result
                    logger.info(f"Result for {url}: {result}")
                else:
                    logger.warning(f"No result returned for {url}")
            except Exception as e:
                logger.error(f"Error evaluating {url}: {e}")

        with open("sas_probed_apis.json", "w") as f:
            json.dump(probe_results, f, indent=4)
            
        successes = [u for u, r in probe_results.items() if r.get("status") == 200]
        logger.info(f"DONE. Found {len(successes)} successful endpoints.")

    finally:
        browser.stop()

if __name__ == "__main__":
    asyncio.run(probe_apis())
