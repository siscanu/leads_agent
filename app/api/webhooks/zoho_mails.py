from fastapi import APIRouter, Request # type: ignore
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.utils.logger import log_json
from app.api.services.zoho.handler import get_mail_handler

# Create a router for Zoho Mail webhook
router = APIRouter(prefix="/zoho-mails", tags=["zoho-mails"])

# Create a Pydantic model for the Zoho Mail webhook payload
class ZohoMailAttachment(BaseModel):
    name: str
    size: int
    content_type: str

class ZohoMailMessage(BaseModel):
    message_id: str
    subject: Optional[str] = None
    from_email: Optional[str] = None
    to_emails: Optional[List[str]] = None
    cc_emails: Optional[List[str]] = None
    content: Optional[str] = None
    html_content: Optional[str] = None
    date: Optional[str] = None
    attachments: Optional[List[ZohoMailAttachment]] = None

@router.post("/")
async def handle_zoho_mail(request: Request) -> Dict[str, Any]:
    """
    Webhook endpoint for incoming Zoho Mail emails
    """
    # Get the raw request body
    body = await request.body()
    
    try:
        # Log the raw incoming data
        payload = await request.json()
        log_json(payload, "Incoming Zoho Mail webhook")

        # Process the email using the ZohoMailHandler
        mail_handler = get_mail_handler()
        
        # Process only a small batch (1-3) since this is triggered by new emails
        # This avoids processing the entire inbox on each webhook
        result = await mail_handler.process_emails(limit=3, enable_draft_creation=True)
        
        log_json(result, "Email processing result")
        
        return {
            "status": "success", 
            "message": "Email received and processed",
            "processed": result.get("threads_processed", 0)
        }
    except Exception as e:
        log_json({"error": str(e), "body": body.decode('utf-8', errors='ignore')}, 
                 "Error processing Zoho Mail webhook")
        return {"status": "error", "message": str(e)}
