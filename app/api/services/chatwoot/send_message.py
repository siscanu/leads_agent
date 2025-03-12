import requests
from typing import Optional, Dict, Any
from app.utils.config import get_chatwoot_config

class ChatwootResponder:
    """A class to handle responses to Chatwoot conversations"""
    
    def __init__(self):
        config = get_chatwoot_config()
        self.api_token = config['api_token']
        self.base_url = config['base_url']
        self.headers = {
            'api_access_token': self.api_token,
            'Content-Type': 'application/json'
        }
    
    def send_response(self, conversation_id: str, message: str, echo_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a response back to a Chatwoot conversation
        
        Args:
            conversation_id: The ID of the conversation to respond to
            message: The message content to send
            echo_id: Optional echo ID for message threading
            
        Returns:
            Dict containing the API response
        """
        url = f"{self.base_url}/api/v1/accounts/1/conversations/{conversation_id}/messages"
        payload = {
            "content": message,
            "message_type": "outgoing",
            "private": False
        }
        
        if echo_id:
            payload["echo_id"] = echo_id
            
        response = requests.post(url, headers=self.headers, json=payload)
        
        try:
            return response.json()
        except Exception as e:
            return {"error": str(e), "raw_response": response.text}

# Create a singleton instance
responder = ChatwootResponder() 