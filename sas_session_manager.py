import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SASSessionManager:
    """Manages SAS session data (cookies and local storage) from captured JSON."""
    
    def __init__(self, session_file: str = "sas_session.json"):
        self.session_file = Path(session_file)
        self.session_data = self._load_session()
        
    def _load_session(self) -> Dict:
        """Load session data from JSON file."""
        if not self.session_file.exists():
            logger.warning(f"Session file {self.session_file} not found.")
            return {"cookies": [], "local_storage": {}, "url": ""}
            
        try:
            with open(self.session_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading session file: {e}")
            return {"cookies": [], "local_storage": {}, "url": ""}
            
    def get_cookie_dict(self) -> Dict[str, str]:
        """Get cookies as a simple name=value dictionary."""
        cookies = {}
        for cookie in self.session_data.get("cookies", []):
            cookies[cookie["name"]] = cookie["value"]
        return cookies
        
    def get_cookie_string(self) -> str:
        """Get cookies as a 'name=value; name2=value2' string."""
        cookies = self.get_cookie_dict()
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])
        
    def get_local_storage(self) -> Dict[str, str]:
        """Get local storage items."""
        return self.session_data.get("local_storage", {})
        
    def get_user_agent(self) -> str:
        """Get a realistic user agent (defaulting to a modern one if not captured)."""
        # Note: We didn't explicitly capture User-Agent in our script, 
        # but we can use a standard one that matches the browser we used.
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def is_session_valid(self) -> bool:
        """Check if the current session is likely still valid based on cookie expiration."""
        if not self.session_data.get("cookies"):
            return False
            
        import time
        now = time.time()
        
        # Check critical cookies like auth0 or session_id
        for cookie in self.session_data.get("cookies", []):
            if cookie["name"] == "auth0":
                expires = cookie.get("expires", -1)
                if expires != -1 and expires < now + 300: # 5 min buffer
                    logger.info("auth0 cookie expired or close to expiring.")
                    return False
        
        # Check if we have the session_id
        if "session_id" not in self.get_cookie_dict():
            logger.info("session_id cookie missing.")
            return False
            
        return True

    def refresh_session(self) -> bool:
        """Trigger the automated capture_session.py script."""
        logger.info("Attempting to refresh SAS session automatically...")
        import subprocess
        import sys
        
        try:
            # Run the capture script in automated mode
            script_path = self.session_file.parent / "capture_session.py"
            result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Session refresh successful.")
                # Reload data
                self.session_data = self._load_session()
                return True
            else:
                logger.error(f"Session refresh failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error during automated session refresh: {e}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = SASSessionManager()
    if not manager.is_session_valid():
        print("Session invalid or expired. Refreshing...")
        manager.refresh_session()
    else:
        print("Session is still valid.")

