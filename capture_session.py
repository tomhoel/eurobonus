import asyncio
import json
import os
import logging
import random
from pathlib import Path
from dotenv import load_dotenv
import nodriver as uc
from nodriver import cdp

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

async def handle_turnstile(page):
    """Attempts to detect and solve Cloudflare Turnstile."""
    try:
        # Give it a moment to appear
        await asyncio.sleep(2)
        
        # Look for the turnstile iframe container
        # Note: selectors might need adjustment based on specific implementation
        turnstile = await page.find("iframe", timeout=5)
        
        if turnstile:
            # Check if it looks like a turnstile/captcha frame
            # This is heuristic; we might check src or other attributes
            # For now, we assume if an iframe appears during login flow it might be it.
            logger.info("Potential Turnstile/iframe detected.")
            
            # Nodriver often handles turnstile automatically if it's standard.
            # But we can try to click specialized elements if needed.
            # Let's see if we find a checkbox inside.
            
            # The 'click' on the iframe element itself sometimes works for these widgets
            # as they capture the event.
            await turnstile.click()
            logger.info("Clicked on potential Turnstile iframe.")
            await asyncio.sleep(2)
            
    except Exception as e:
        # It's fine if we don't find it
        pass

async def automated_login(browser, email, password):
    # 1. Navigate to SAS Login
    url = "https://www.flysas.com/auth/login?ui_locales=en&returnTo=%2Fen"
    logger.info(f"Navigating to {url}")
    page = await browser.get(url)
    
    # Wait for initial load - crucial for off-screen stability
    await asyncio.sleep(2)
    await page.wait_for("input[name='username']", timeout=15)
    logger.info("Email field found.")
    
    # Check for turnstile early
    await handle_turnstile(page)
    await asyncio.sleep(0.5)

    # Email Entry - Slow and Deliberate
    email_field = await page.select("input[name='username']")
    await email_field.click() # Ensure focus
    await element_slow_type(email_field, email)
    logger.info("Email entered (slow mode).")
    
    await asyncio.sleep(0.5)
    
    # Click Continue
    continue_btn = await page.select("button[type='submit']")
    await continue_btn.click()
    logger.info("Clicking Continue...")
    
    # 2. Wait for password field
    logger.info("Waiting for password input field...")
    try:
        await page.wait_for("input[type='password']", timeout=10)
        await asyncio.sleep(1) # Extra stability
    except:
        logger.warning("Password field timed out. Checking for Turnstile again...")
        await handle_turnstile(page)
        await page.wait_for("input[type='password']", timeout=10)
    
    # Password Entry - Slow and Deliberate
    password_field = await page.select("input[type='password']")
    await password_field.click()
    await element_slow_type(password_field, password)
    logger.info("Password entered.")
    
    # Click Sign In
    signin_btn = await page.select("button[type='submit']")
    await signin_btn.click()
    logger.info("Clicking Sign In...")
    
    # 3. Wait for redirect
    logger.info("Waiting for final landing page...")
    for _ in range(120): 
        if ("sas.no" in page.url or "flysas.com" in page.url) and "auth" not in page.url:
            logger.info(f"Successfully landed on: {page.url}")
            break
        await asyncio.sleep(0.5)
        
    logger.info("Ensuring session on award page...")
    # Navigate to award finder directly 
    await page.get("https://www.sas.no/award-finder")
    await asyncio.sleep(3) 
    return page

async def element_slow_type(element, text):
    """Types text into an element one character at a time with delays."""
    await element.clear_input()
    await asyncio.sleep(0.2)
    for char in text:
        await element.send_keys(char)
        await asyncio.sleep(random.uniform(0.05, 0.15))

async def capture_session(automated=True):
    # Load credentials
    load_dotenv()
    email = os.getenv("SAS_EMAIL")
    password = os.getenv("SAS_PASSWORD")
    
    if automated and (not email or email == "your_email@example.com"):
        logger.error("SAS_EMAIL/SAS_PASSWORD not set in .env.")
        automated = False
    
    logger.info("Starting browser (nodriver)...")
    
    # Configure browser to be robust (headed required for full auth tokens on Profile API)
    browser = await uc.start(
        headless=False,
        browser_args=[
            "--no-sandbox", 
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled", # Helps evade detection
            "--window-size=1920,1080",
            "--window-position=2000,0", # Move off-screen attempts to minimize impact
            "--disable-gpu"
        ],
        sandbox=False
    )
    
    try:
        if automated:
            page = await automated_login(browser, email, password)
        else:
            page = await browser.get("https://www.sas.no/booking/award/flights")
            print("Press ENTER in console to capture...")
            await asyncio.get_event_loop().run_in_executor(None, input)

        logger.info("Capturing session data...")
        
        # Get cookies
        try:
             cookies = await browser.cookies.get_all()
        except:
             cookies = []

        cookies_list = []
        for cookie in cookies:
            cookie_dict = cookie.to_dict() if hasattr(cookie, 'to_dict') else vars(cookie)
            sanitized_cookie = {}
            for k, v in cookie_dict.items():
                if isinstance(v, (str, int, float, bool, type(None))):
                    sanitized_cookie[k] = v
                else:
                    sanitized_cookie[k] = str(v)
            cookies_list.append(sanitized_cookie)
            
        # Get local storage
        try:
            ls_data = await page.evaluate("JSON.stringify(localStorage)")
            if ls_data:
                local_storage_data = json.loads(ls_data)
            else:
                 local_storage_data = {}
        except Exception as e:
            logger.warning(f"Could not capture local storage: {e}")
            local_storage_data = {}
            
        if not local_storage_data:
             logger.warning("Captured local storage is empty!")
            
        session_data = {
            "cookies": cookies_list,
            "local_storage": local_storage_data,
            "url": page.url
        }
        
        output_file = "sas_session.json"
        with open(output_file, "w") as f:
            json.dump(session_data, f, indent=4)
        
        logger.info(f"✅ Session data saved to {output_file}")
        
    finally:
        browser.stop()

if __name__ == "__main__":
    import sys
    is_automated = "--manual" not in sys.argv
    asyncio.run(capture_session(automated=is_automated))
