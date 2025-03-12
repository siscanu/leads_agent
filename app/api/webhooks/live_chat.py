from fastapi import APIRouter, Request # type: ignore
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from app.utils.logger import log_json
from app.api.services.chatwoot.handler import conversation_manager

# Create a router for the live chat endpoints
router = APIRouter(prefix="/live-chat", tags=["live-chat"])

# Create a Pydantic model for the Chatwoot webhook
class ChatwootMessage(BaseModel):
    event: str
    message_type: Optional[str] = None
    content: Optional[str] = None
    conversation: Optional[Dict] = None
    id: Optional[int] = None
    sender: Optional[Dict] = None
    
    # Fields that might be needed for compatibility
    conversation_id: Optional[str] = None
    account_id: Optional[str] = None
    echo_id: Optional[str] = None

# Live chat endpoint for Chatwoot
@router.post("/")
async def live_chat(request: Request) -> Dict[str, Any]:
    try:
        # Parse the webhook data
        body = await request.body()
        data = json.loads(body)
        webhook = ChatwootMessage(**data)
        
        # Log the incoming webhook data with message type for clarity
        log_type = f"Parsed Webhook Data ({webhook.message_type} message)" if webhook.message_type else "Parsed Webhook Data"
        log_json(webhook.dict(), log_type)
        
        # Check if this message should be processed
        if conversation_manager.is_valid_for_processing(webhook.dict()):
            # Process the message with the conversation manager
            return conversation_manager.process_message(webhook.dict())
        else:
            return {"status": "ignored"}
    
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
