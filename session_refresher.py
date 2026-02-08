#!/usr/bin/env python3
"""
Smart Session Refresher

Checks session validity before refreshing. Only runs capture_session.py when:
1. Session file doesn't exist
2. Session is expired or expiring within 6 hours
3. Session file is corrupted/unreadable

Default check interval: 48 hours (can be overridden with CHECK_INTERVAL env var)
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s"
)
logger = logging.getLogger("SessionRefresher")

SESSION_FILE = "sas_session.json"
EXPIRY_BUFFER_HOURS = 6  # Refresh if expiring within this many hours
DEFAULT_CHECK_INTERVAL = 48 * 3600  # 48 hours in seconds


def get_session_expiry() -> float:
    """
    Returns the earliest auth cookie expiry timestamp, or 0 if session is invalid.
    """
    if not Path(SESSION_FILE).exists():
        logger.warning(f"Session file {SESSION_FILE} not found")
        return 0

    try:
        with open(SESSION_FILE) as f:
            data = json.load(f)

        cookies = data.get("cookies", [])
        if not cookies:
            logger.warning("No cookies in session file")
            return 0

        # Find auth0 cookie expiry (the critical one)
        for cookie in cookies:
            if cookie.get("name") == "auth0":
                expires = cookie.get("expires", 0)
                if expires:
                    return float(expires)

        # Fallback: check session_id exists
        has_session = any(c.get("name") == "session_id" for c in cookies)
        if not has_session:
            logger.warning("No session_id cookie found")
            return 0

        # If we have session_id but no auth0 expiry, assume it's valid for now
        # Return a future timestamp (24 hours from now)
        return time.time() + 86400

    except Exception as e:
        logger.error(f"Error reading session file: {e}")
        return 0


def is_session_valid() -> bool:
    """
    Check if the current session is valid and not expiring soon.
    """
    expiry = get_session_expiry()
    if expiry == 0:
        return False

    now = time.time()
    buffer_seconds = EXPIRY_BUFFER_HOURS * 3600

    if expiry < now:
        logger.info("Session has expired")
        return False

    if expiry < now + buffer_seconds:
        remaining_hours = (expiry - now) / 3600
        logger.info(f"Session expiring in {remaining_hours:.1f} hours (within buffer)")
        return False

    remaining_hours = (expiry - now) / 3600
    expiry_dt = datetime.fromtimestamp(expiry, tz=timezone.utc)
    logger.info(f"Session valid until {expiry_dt} ({remaining_hours:.1f} hours remaining)")
    return True


def run_capture():
    """
    Run the capture_session.py script.
    """
    logger.info("Running session capture...")

    # Use xvfb-run for headless browser support
    cmd = [
        "xvfb-run",
        "--server-args=-screen 0 1920x1080x24",
        sys.executable,
        "capture_session.py"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            logger.info("Session capture completed successfully")
            return True
        else:
            logger.error(f"Session capture failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Session capture timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Error running capture: {e}")
        return False


def main():
    check_interval = int(os.getenv("CHECK_INTERVAL", DEFAULT_CHECK_INTERVAL))
    logger.info(f"Session Refresher started (check interval: {check_interval/3600:.1f} hours)")

    while True:
        if is_session_valid():
            logger.info("Session is valid, skipping refresh")
        else:
            logger.info("Session invalid or expiring soon, refreshing...")
            success = run_capture()

            if success:
                # Verify the new session is valid
                if is_session_valid():
                    logger.info("New session verified successfully")
                else:
                    logger.warning("New session may have issues, will retry next cycle")
            else:
                logger.error("Session refresh failed, will retry in 1 hour")
                time.sleep(3600)  # Retry sooner on failure
                continue

        logger.info(f"Sleeping for {check_interval/3600:.1f} hours...")
        time.sleep(check_interval)


if __name__ == "__main__":
    main()
