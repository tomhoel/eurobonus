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

async def automated_login(browser, email, password):
    # 1. Navigate to SAS Login
    url = "https://www.flysas.com/auth/login?ui_locales=en&returnTo=%2Fen"
    logger.info(f"Navigating to {url}")
    page = await browser.get(url)
    
    # Wait for the page to load more fully before selecting
    await page.sleep(3)
    
    # Wait for the email field
    logger.info("Waiting for email input field...")
    try:
        # Sometimes select triggers a race condition if the page is mid-load. 
        # Using a loop for more robust selection.
        email_field = None
        for _ in range(10):
            try:
                email_field = await page.select('input[name="username"]', timeout=5)
                if email_field: break
            except:
                await page.sleep(1)
                
        if not email_field:
            logger.warning("Email field not found, checking if already logged in...")
            if "sas.no" in page.url and "auth" not in page.url:
                logger.info("Already logged in.")
                return page
            else:
                raise Exception("Could not find login email field.")
        
        # Fill email
        await email_field.send_keys(email)
        logger.info("Email entered.")
        
        # Click Continue
        continue_btn = await page.select('button[type="submit"]')
        await continue_btn.click()
        logger.info("Clicking Continue...")
        
        # 2. Wait for password field
        logger.info("Waiting for password input field...")
        await page.sleep(2) # Small delay for transition
        
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
            logger.error(f"Password field not found. Current URL: {page.url}")
            inputs = await page.evaluate("Array.from(document.querySelectorAll('input')).map(i => ({type: i.type, name: i.name, id: i.id}))")
            logger.info(f"Available inputs: {inputs}")
            raise Exception("Could not find password input field.")
            
        await password_field.send_keys(password)
        logger.info("Password entered.")
        
        # Click Sign In
        signin_btn = await page.select('button[type="submit"]')
        await signin_btn.click()
        logger.info("Clicking Sign In...")
        
        # 3. Wait for redirect
        logger.info("Waiting for final landing page...")
        for _ in range(60): 
            if ("sas.no" in page.url or "flysas.com" in page.url) and "auth" not in page.url:
                logger.info(f"Successfully landed on: {page.url}")
                logger.info("Navigating to award flights page...")
                await page.get("https://www.sas.no/booking/award/flights")
                await page.sleep(5) 
                return page
            await page.sleep(1)
            
        logger.warning("Landing check timed out, but proceeding to capture.")
        return page
        
    except Exception as e:
        logger.error(f"Automated login failed: {e}")
        # Take a screenshot for debugging if possible (nodriver has limited screenshot support in some versions)
        # page.save_screenshot("login_error.png")
        raise

async def capture_session(automated=True):
    # Load credentials
    load_dotenv()
    email = os.getenv("SAS_EMAIL")
    password = os.getenv("SAS_PASSWORD")
    
    if automated and (not email or email == "your_email@example.com"):
        logger.error("SAS_EMAIL/SAS_PASSWORD not set in .env. Falling back to manual mode.")
        automated = False
    
    logger.info("Starting browser...")
    browser = await uc.start()
    
    try:
        if automated:
            page = await automated_login(browser, email, password)
        else:
            # Manual mode
            url = "https://www.sas.no/booking/award/flights"
            page = await browser.get(url)
            print("\n" + "="*50)
            print("MANUAL ACTION REQUIRED:")
            print("1. Log in to your account.")
            print("2. Navigate to the award results page.")
            print("3. Return here and press ENTER.")
            print("="*50 + "\n")
            await asyncio.get_event_loop().run_in_executor(None, input, "Press ENTER to capture...")

        logger.info("Capturing session data...")
        
        # Get cookies
        cookies = await browser.cookies.get_all()
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
        local_storage = await page.evaluate("JSON.stringify(localStorage)")
        local_storage_data = json.loads(local_storage)
        
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
