import os
import time
import requests
from typing import Dict, Optional

class ZohoAuthManager:
    def __init__(self):
        # Get credentials from environment variables
        self.client_id = os.environ.get("ZOHO_CLIENT_ID")
        self.client_secret = os.environ.get("ZOHO_CLIENT_SECRET")
        self.refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN")
        self.domain = os.environ.get("ZOHO_DOMAIN", "zoho.eu")
        
        # In-memory storage only
        self.access_token = None
        self.token_expires_at = 0
    
    def get_access_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing it if necessary
        
        Returns:
            str: Valid access token or None if refresh failed
        """
        # Check if token needs refreshing (expired or will expire in next minute)
        current_time = time.time()
        if not self.access_token or current_time >= (self.token_expires_at - 60):
            self.refresh_access_token()
        
        return self.access_token
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            print("Missing credentials for token refresh")
            return False
        
        url = f"https://accounts.{self.domain}/oauth/v2/token"
        data = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                # Tokens usually expire in 3600 seconds (1 hour)
                expires_in = result.get("expires_in", 3600)
                self.token_expires_at = time.time() + expires_in
                return True
            else:
                print(f"Token refresh failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error refreshing token: {str(e)}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authorization headers for API requests
        
        Returns:
            Dict[str, str]: Headers with valid access token
        """
        token = self.get_access_token()
        if not token:
            return {}
        
        return {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Accept": "application/json"
        }

# Singleton instance
_auth_manager = None

def get_auth_manager():
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = ZohoAuthManager()
    return _auth_manager
