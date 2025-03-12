from typing import Dict, Any, Optional, List
import aiohttp # type: ignore
from urllib.parse import urljoin
from datetime import datetime

class TelegramAPI:
    BASE_URL = "https://api.telegram.org/bot{token}/"

    def __init__(self, token: str):
        self.token = token
        self.base_url = self.BASE_URL.format(token=token)
        self.session = aiohttp.ClientSession()
    
    async def _make_request(self, method: str, **kwargs) -> Dict[str, Any]:
        """Make a request to Telegram Bot API"""
        url = urljoin(self.base_url, method)
        async with self.session.post(url, json=kwargs) as response:
            data = await response.json()
            if not data.get('ok'):
                raise Exception(f"Telegram API error: {data.get('description')}")
            return data.get('result')
    
    async def send_message(self, chat_id: int, text: str, parse_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a text message to a chat
        
        Args:
            chat_id: Chat ID to send the message to
            text: Text of the message
            parse_mode: Mode for parsing entities. Can be 'MarkdownV2' or 'HTML'
        
        Returns:
            Dict with the sent message
        """
        params = {'chat_id': chat_id, 'text': text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        return await self._make_request('sendMessage', **params)
    
    async def set_webhook(self, url: str) -> bool:
        """Set the webhook URL for receiving updates"""
        result = await self._make_request('setWebhook', url=url)
        return bool(result)
    
    async def delete_webhook(self) -> bool:
        """Remove the webhook integration"""
        result = await self._make_request('deleteWebhook')
        return bool(result)
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Get current webhook status"""
        return await self._make_request('getWebhookInfo')
    
    async def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None) -> bool:
        """Answer a callback query"""
        params = {'callback_query_id': callback_query_id}
        if text:
            params['text'] = text
        result = await self._make_request('answerCallbackQuery', **params)
        return bool(result)
    
    async def edit_message_text(self, chat_id: int, message_id: int, text: str) -> Dict[str, Any]:
        """Edit a message's text"""
        return await self._make_request('editMessageText', chat_id=chat_id, message_id=message_id, text=text)
    
    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        """Delete a message"""
        result = await self._make_request('deleteMessage', chat_id=chat_id, message_id=message_id)
        return bool(result)
    
    async def get_chat(self, chat_identifier: str) -> Dict[str, Any]:
        """
        Get information about a chat by username.
        
        Args:
            chat_identifier: Username of the chat (must start with @)
            
        Returns:
            Dict containing chat information
        """
        # Ensure username starts with @
        if not chat_identifier.startswith('@'):
            chat_identifier = f"@{chat_identifier}"
            
        return await self._make_request('getChat', chat_id=chat_identifier)
    
    async def close(self):
        """Close the aiohttp session"""
        await self.session.close()