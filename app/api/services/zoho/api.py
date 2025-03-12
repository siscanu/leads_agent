import os
import requests
import aiohttp  # For async HTTP requests
from typing import Dict, List, Any, Optional
from .ZohoAuthManager import get_auth_manager
import html
import re
import json

class ZohoEmailHandler:
    """
    Simple handler for Zoho Mail API operations
    """
    def __init__(self):
        self.auth_manager = get_auth_manager()
        self.account_id = os.environ.get("ZOHO_ACCOUNT_ID")
        self.domain = os.environ.get("ZOHO_DOMAIN", "zoho.eu")
        
        if not self.account_id:
            raise ValueError("ZOHO_ACCOUNT_ID environment variable is not set")
    
    async def list_emails(self, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """
        List emails with optional filtering parameters
        
        Args:
            limit: Maximum number of emails to return
            **kwargs: Additional filtering parameters (e.g., threadId, before, after)
            
        Returns:
            Dict with email data or error
        """
        # Get authentication headers
        headers = self.auth_manager.get_auth_headers()
        if not headers:
            return {"error": "Failed to get authentication headers"}
        
        # Build API URL
        url = f"https://mail.{self.domain}/api/accounts/{self.account_id}/messages/view"
        
        # Prepare parameters - limit, sortBy, and sortorder are required
        params = {
            "limit": limit,
            "sortBy": "date",
            "sortorder": "false"  # newest first
        }
        
        # Add any additional parameters
        params.update(kwargs)
        
        # Make the request asynchronously
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        text = await response.text()
                        return {"error": f"API error: {text}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def get_email(self, message_id: str) -> Dict[str, Any]:
        """
        Get a specific email by message ID
        
        Args:
            message_id: Email ID
            
        Returns:
            Dict with email data or error
        """
        # Get authentication headers
        headers = self.auth_manager.get_auth_headers()
        if not headers:
            return {"error": "Failed to get authentication headers"}
        
        # Build API URL
        url = f"https://mail.{self.domain}/api/accounts/{self.account_id}/messages/{message_id}"
        
        # Make the request asynchronously
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        text = await response.text()
                        return {"error": f"API error: {text}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def send_email(
        self, 
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        is_html: bool = True
    ) -> Dict[str, Any]:
        """
        Send an email
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            is_html: Whether the body is HTML
            
        Returns:
            Dict with response data or error
        """
        # Get authentication headers
        headers = self.auth_manager.get_auth_headers()
        if not headers:
            return {"error": "Failed to get authentication headers"}
        
        # Build API URL
        url = f"https://mail.{self.domain}/api/accounts/{self.account_id}/messages"
        
        # Prepare data
        data = {
            "toAddress": ",".join(to),
            "subject": subject,
            "content": body,
        }
        
        if cc:
            data["ccAddress"] = ",".join(cc)
        
        if bcc:
            data["bccAddress"] = ",".join(bcc)
        
        if is_html:
            data["mailFormat"] = "html"
        
        # Make the request
        try:
            response = requests.post(url, headers=headers, data=data)
            
            if response.status_code in (200, 201):
                return response.json()
            else:
                return {"error": f"API error: {response.text}"}
                
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def create_draft(
        self,
        to: List[str],
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        is_html: bool = True
    ) -> Dict[str, Any]:
        """
        Create a draft email
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            thread_id: Optional thread ID to add this email to
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            is_html: Whether the body is HTML (default: True)
            
        Returns:
            Dict with created draft data or error
        """
        # Get authentication headers
        headers = self.auth_manager.get_auth_headers()
        headers["Content-Type"] = "application/json"  # Set content type to JSON
        
        if not headers:
            return {"error": "Failed to get authentication headers"}
        
        # Build API URL - using the endpoint from the documentation
        url = f"https://mail.{self.domain}/api/accounts/{self.account_id}/messages"
        
        # Get default sender from environment variable or use a fallback
        default_sender = os.environ.get("ZOHO_DEFAULT_SENDER", "info@deepcleaning.ie")
        
        # Extract valid email addresses from potentially formatted strings
        def clean_email(email_str):
            if not email_str or email_str == "Not Provided":
                return ""
            
            # Unescape HTML entities first
            email_str = html.unescape(email_str)
            
            # Remove any remaining HTML-like formatting
            email_str = re.sub(r'["\']|&quot;|&lt;|&gt;', '', email_str)
            
            # Extract just the email address
            match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', email_str)
            return match.group(0) if match else ""
        
        # Clean and filter recipient lists
        clean_to = [clean_email(addr) for addr in to if addr]
        clean_to = [addr for addr in clean_to if addr]  # Remove empty entries
        
        if not clean_to:
            return {"error": "No valid recipient email addresses provided"}
            
        # Clean CC/BCC lists if present
        clean_cc = []
        if cc:
            for cc_addr in cc:
                cleaned = clean_email(cc_addr)
                if cleaned:
                    clean_cc.append(cleaned)
            if clean_cc:
                print(f"Cleaned CC addresses: {clean_cc}")
        
        clean_bcc = []
        if bcc:
            clean_bcc = [clean_email(addr) for addr in bcc]
            clean_bcc = [addr for addr in clean_bcc if addr]
        
        # Simplify body content processing to avoid issues
        # First, check if the body already contains HTML tags
        contains_html = re.search(r'<[^>]+>', body) is not None
        
        # Normalize HTML content to fix inconsistent newline handling (root cause of 500 errors)
        if contains_html:
            # Normalize newlines between HTML tags
            # Replace various newline patterns with a consistent format
            # This pattern matches HTML tags followed by any whitespace and newlines
            clean_body = re.sub(r'(</[^>]+>)\s*\n+\s*(<[^>]+>)', r'\1\n\2', body)
            
            # Remove control characters that could cause issues
            clean_body = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', clean_body)
            
            # Normalize space between paragraphs (consistent with successful examples)
            clean_body = re.sub(r'</p>\s*\n*\s*<p>', r'</p>\n<p>', clean_body)
        else:
            # If it's plain text, convert newlines to <br> tags for HTML formatting
            clean_body = body.replace('\n', '<br>')
            clean_body = re.sub(r'[\x00-\x1F\x7F]', '', clean_body)
            # Force HTML format
            is_html = True
        
        # Clean thread_id - ensure it's a valid string and not a problematic value
        use_thread_id = None
        if thread_id and not thread_id.startswith("standalone_"):
            # Ensure thread_id is clean and numeric
            clean_thread = re.sub(r'[^\d]', '', thread_id)
            if clean_thread:
                use_thread_id = clean_thread
        
        # Prepare data for API request - keep it minimal and match Zoho's format exactly
        data = {
            "mode": "draft",
            "fromAddress": default_sender,
            "toAddress": ",".join(clean_to),
            "subject": subject.strip(),
            "content": clean_body,  # Use the normalized content
            "mailFormat": "html" if is_html else "plaintext",
            "encoding": "UTF-8"  # Explicitly set encoding to ensure proper handling
        }
        
        # Add CC only if present
        if clean_cc:
            data["ccAddress"] = ",".join(clean_cc)
            
        # Print request data for debugging
        print(f"Sending draft request with data: {json.dumps(data, indent=2)}")
        
        # Make the request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    response_text = await response.text()
                    if response.status in (200, 201):
                        try:
                            return await response.json()
                        except:
                            return {"data": {"message": "Draft created", "raw": response_text}}
                    else:
                        print(f"Draft creation error: Status {response.status}, Response: {response_text}")
                        return {"error": f"API error ({response.status}): {response_text}"}
        except Exception as e:
            error_message = str(e)
            print(f"Exception during draft creation: {error_message}")
            return {"error": f"Request failed: {error_message}"}
    
    async def get_email_content(self, message_id: str, folder_id: str) -> Dict[str, Any]:
        """
        Get the content of a specific email
        
        Args:
            message_id: Email ID
            folder_id: Folder ID containing the email
            
        Returns:
            Dict with email content or error
        """
        # Get authentication headers
        headers = self.auth_manager.get_auth_headers()
        if not headers:
            return {"error": "Failed to get authentication headers"}
        
        # Build API URL - using folder path required by Zoho API
        url = f"https://mail.{self.domain}/api/accounts/{self.account_id}/folders/{folder_id}/messages/{message_id}/content"
        
        # Add parameter to include block content
        params = {
            "includeBlockContent": "true"
        }
        
        # Make the request asynchronously
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        text = await response.text()
                        return {"error": f"API error: {text}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

# Singleton instance
_email_handler = None

def get_email_handler():
    global _email_handler
    if _email_handler is None:
        _email_handler = ZohoEmailHandler()
    return _email_handler
