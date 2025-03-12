import os
import json
import re
from typing import List, Dict, Any, Set

from app.api.services.zoho.api import get_email_handler
from app.agents.zoho.agent import create_response_agent, create_classification_agent
from app.api.services.zoho.steps import (
    fetch_recent_emails,
    organize_emails_by_thread,
    filter_threads,
    fetch_all_content,
    classify_emails,
    generate_responses,
    create_drafts
)

# Color constants for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
RESET = "\033[0m"

# Create a colors dictionary for passing to step modules
COLORS = {
    "RED": RED,
    "GREEN": GREEN,
    "YELLOW": YELLOW,
    "BLUE": BLUE,
    "MAGENTA": MAGENTA,
    "CYAN": CYAN,
    "WHITE": WHITE,
    "RESET": RESET
}

# Company email addresses that we use to respond
COMPANY_EMAIL_ADDRESSES = ["customers@deepcleaning.ie", "info@deepcleaning.ie"]
NUMBER_OF_EMAILS_TO_FETCH = 30

class ZohoMailHandler:
    """
    Handler for managing Zoho Mail workflows:
    - Fetching recent emails
    - Organizing emails by thread
    - Tracking responded emails
    - Generating draft responses using AI
    """
    
    def __init__(self):
        """Initialize the handler with email API access and tracking storage"""
        self.email_handler = get_email_handler()
        # Store data file in the /data folder
        self.data_dir = "data"
        self.responded_emails_file = os.path.join(self.data_dir, "responded_emails.json")
        self.spam_emails_file = os.path.join(self.data_dir, "spam_emails.json")
        self.responded_emails = self._load_responded_emails()
        self.spam_emails = self._load_spam_emails()
        self.company_email_addresses = COMPANY_EMAIL_ADDRESSES
    
    def _load_responded_emails(self) -> Set[str]:
        """Load the set of message IDs that have already been responded to"""
        if os.path.exists(self.responded_emails_file):
            try:
                with open(self.responded_emails_file, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                print(f"Error loading responded emails: {str(e)}")
        return set()
    
    def _save_responded_emails(self):
        """Save the set of message IDs that have been responded to"""
        try:
            # Ensure the data directory exists
            os.makedirs(self.data_dir, exist_ok=True)
            
            with open(self.responded_emails_file, 'w') as f:
                json.dump(list(self.responded_emails), f)
        except Exception as e:
            print(f"Error saving responded emails: {str(e)}")
    
    def _load_spam_emails(self) -> Set[str]:
        """Load the set of message IDs that have been marked as spam"""
        if os.path.exists(self.spam_emails_file):
            try:
                with open(self.spam_emails_file, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                print(f"Error loading spam emails: {str(e)}")
        return set()
    
    def _save_spam_emails(self):
        """Save the set of message IDs that have been marked as spam"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.spam_emails_file, 'w') as f:
                json.dump(list(self.spam_emails), f)
        except Exception as e:
            print(f"Error saving spam emails: {str(e)}")
    
    def mark_email_as_spam(self, message_id: str, thread_id: str = None):
        """Mark an email as spam by adding its message ID and thread ID to tracking"""
        if message_id:
            self.spam_emails.add(message_id)
            if thread_id:
                self.spam_emails.add(f"thread_{thread_id}")
            self._save_spam_emails()
            print(f"{RED}Marked message {message_id} as spam{RESET}")
    
    def mark_email_as_responded(self, message_id: str):
        """Mark an email as responded by adding its message ID to tracking"""
        if not message_id:
            return
            
        self.responded_emails.add(message_id)
        self._save_responded_emails()
        print(f"{YELLOW}Marked message {message_id} as responded{RESET}")
    
    async def classify_email(self, email: Dict[str, Any], content: str) -> Dict[str, bool]:
        """
        Use the classification agent to determine if an email is cleaning related and needs response
        Returns dict with classification results
        """
        try:
            formatted = f"""
            From: {email.get('fromAddress')} ({email.get('fromName', '')})
            Subject: {email.get('subject')}
            Content: {content}
            """
            agent = await create_classification_agent()
            response = await agent.arun(formatted)
            result = response.content
            if result.is_cleaning_related:
                if result.needs_response:
                    print(f"{GREEN}Classification: RELEVANT & NEEDS RESPONSE - {result.reason}{RESET}")
                else:
                    print(f"{YELLOW}Classification: RELEVANT but NO RESPONSE NEEDED - {result.reason}{RESET}")
            else:
                print(f"{RED}Classification: NOT RELEVANT (SPAM) - {result.reason}{RESET}")
                
            return {
                "is_cleaning_related": result.is_cleaning_related,
                "needs_response": result.needs_response
            }
        except Exception as e:
            print(f"{RED}Error classifying: {str(e)}{RESET}")
            # If classification fails, assume it's relevant and needs response
            return {"is_cleaning_related": True, "needs_response": True}
    
    async def create_draft_response(self, 
        latest_email: Dict[str, Any], 
        thread: List[Dict[str, Any]], 
        thread_id: str,
        create_draft: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a draft response to an email thread using an AI agent
        
        Args:
            latest_email: The most recent email in the thread
            thread: List of all emails in the thread
            thread_id: Thread ID
            create_draft: Whether to create a draft (True) or just generate response (False)
            
        Returns:
            Dict containing response data or error
        """
        try:
            # Format emails for agent
            formatted_emails = self._format_emails_for_agent(thread, latest_email)
            
            # Generate response with agent
            print(f"{BLUE}Generating response with AI agent...{RESET}")
            agent = await create_response_agent()
            
            # Extract the response from the agent
            response = ""
            try:
                # Try the normal way first
                response_obj = await agent.arun(formatted_emails)
                
                # Check various response formats
                if hasattr(response_obj, 'content') and hasattr(response_obj.content, 'final_message'):
                    response = response_obj.content.final_message
                elif isinstance(response_obj, dict) and 'final_message' in response_obj:
                    response = response_obj['final_message']
                else:
                    response = str(response_obj)
                
            except StopAsyncIteration:
                # Handle the common Agno exception - extract from debug output
                debug_output = str(agent)
                # Look for final_message in the debug output
                matches = re.findall(r'"final_message"\s*:\s*"([^"]*)"', debug_output)
                if matches:
                    response = matches[0].replace('\\n', '\n')
                else:
                    return {"error": "Failed to extract AI-generated response"}
            
            # Clean up the response - this is critical for handling escaped sequences
            # Handle any remaining escaped sequences properly
            response = response.replace('\\n', '\n').replace('\\\\', '\\').replace('\\"', '"')
            
            # Remove any remaining backslashes that could cause JSON issues
            response = response.replace('\\', '')
            
            # Check if we have a valid response
            if not response:
                return {"error": "Failed to generate response - empty response returned"}
                
            print(f"{GREEN}Generated response ({len(response)} chars){RESET}")
            
            # Extract recipient information
            to_address = latest_email.get("fromAddress", "")
            subject = latest_email.get("subject", "")
            if subject and not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"
                
            # Extract and filter CC addresses
            cc_address = latest_email.get("ccAddress", "")
            cc_list = []
            if cc_address:
                # Split and clean each CC address individually
                for cc_addr in cc_address.split(","):
                    cc_addr = cc_addr.strip()
                    if cc_addr and cc_addr.lower() not in [a.lower() for a in self.company_email_addresses]:
                        cc_list.append(cc_addr)
            
            if create_draft:
                # Create draft in Zoho Mail
                print(f"{BLUE}Creating draft to: {to_address}{RESET}")
                if cc_list:
                    print(f"{BLUE}CC: {', '.join(cc_list)}{RESET}")
                    
                # Ensure response is properly formatted as HTML if it contains HTML tags
                is_html = bool(re.search(r'<[^>]+>', response))
                if not is_html and ('\n' in response or '<br>' in response):
                    # Convert newlines to <br> tags if not already HTML
                    response = response.replace('\n', '<br>')
                    is_html = True
                
                result = await self.email_handler.create_draft(
                    to=[to_address],
                    subject=subject,
                    body=response,
                    thread_id=thread_id if not thread_id.startswith("standalone_") else None,
                    cc=cc_list,
                    is_html=is_html
                )
                
                if "error" in result:
                    print(f"{RED}Error creating draft: {result['error']}{RESET}")
                    return {
                        "response": response,
                        "error": result['error']
                    }
                else:
                    print(f"{GREEN}Draft created successfully{RESET}")
                    return {
                        "response": response,
                        "draft_id": result.get("data", {}).get("draftId")
                    }
            else:
                # Just return the generated response without creating a draft
                return {
                    "response": response,
                    "draft_created": False
                }
        except Exception as e:
            error_msg = f"AI agent error: {str(e)}"
            print(f"{RED}{error_msg}{RESET}")
            import traceback
            print(f"{RED}Stack trace: {traceback.format_exc()}{RESET}")
            return {"error": error_msg}
    
    def _format_emails_for_agent(self, thread: List[Dict[str, Any]], latest_email: Dict[str, Any]) -> str:
        """Format the email thread for the agent to process"""
        formatted_content = "--- EMAIL THREAD HISTORY (OLDEST TO NEWEST) ---\n\n"
        
        # Add all emails in the thread
        for i, email in enumerate(thread, 1):
            # Include all emails in the thread, including our responses
            formatted_content += f"EMAIL #{i}"
            if email.get("messageId") == latest_email.get("messageId"):
                formatted_content += " (NEEDS RESPONSE)"
            # Add a label for our company emails to make it clear
            if email.get("fromAddress", "").lower() in [addr.lower() for addr in self.company_email_addresses]:
                formatted_content += " (OUR PREVIOUS RESPONSE)"
            formatted_content += "\n"
            formatted_content += f"From: {email.get('fromAddress')} ({email.get('fromName', '')})\n"
            formatted_content += f"To: {email.get('toAddress')}\n"
            formatted_content += f"CC: {email.get('ccAddress', 'Not Provided')}\n"
            formatted_content += f"Subject: {email.get('subject')}\n"
            formatted_content += f"Date: {email.get('receivedTime')}\n"
            
            # Extract and clean content
            content = email.get("content", "No content")
            formatted_content += f"Content:\n{content}\n\n"
            formatted_content += "-" * 50 + "\n\n"
            
        # Add instructions for response
        formatted_content += "\n\nYour task is to write a professional response to the most recent email in this thread.\n"
        formatted_content += "Please draft a complete email response including appropriate greeting and signature.\n\n"
        
        return formatted_content

    async def process_emails(self, limit: int = NUMBER_OF_EMAILS_TO_FETCH, enable_draft_creation: bool = True) -> Dict[str, Any]:
        """
        Main workflow - processes multiple emails/threads in a logical order:
        1. Fetch basic email list
        2. Fetch email list by thread id, and keep those without a thread id
        3. Filter out threads where we sent the last email (based on full thread email list)
        4. Fetch full content for all filtered thread and emails with no thread id from step 2
        5. Classify emails with content
        6. Generate AI responses for threads that need them
        7. Create drafts in Zoho Mail
        
        Args:
            limit: Maximum number of recent emails to fetch (smaller values are faster for webhook triggers)
            enable_draft_creation: Whether to create actual drafts or just generate responses
            
        Returns:
            Dict with processing results and statistics
        """
        try:
            # Step 1: Fetch basic email list
            recent_emails = await fetch_recent_emails(
                email_handler=self.email_handler, 
                limit=limit, 
                colors=COLORS
            )
            
            if "error" in recent_emails:
                return {"error": recent_emails["error"]}
            
            total_emails = len(recent_emails.get("data", []))
            
            # Step 2: Organize emails by thread ID and fetch full thread info
            full_threads = await organize_emails_by_thread(
                recent_emails=recent_emails,
                email_handler=self.email_handler,
                spam_emails=self.spam_emails,
                colors=COLORS
            )
            
            if not full_threads:
                return {
                    "total_emails": total_emails,
                    "total_threads": 0,
                    "customer_last_emails": 0,
                    "threads_processed": 0,
                    "results": []
                }
            
            # Step 3: Filter threads based on sender
            customer_last_threads = filter_threads(
                full_threads=full_threads,
                company_email_addresses=self.company_email_addresses,
                responded_emails=self.responded_emails,
                spam_emails=self.spam_emails,
                colors=COLORS
            )
            
            if not customer_last_threads:
                return {
                    "total_emails": total_emails,
                    "total_threads": len(full_threads),
                    "customer_last_emails": 0,
                    "threads_processed": 0,
                    "results": []
                }
            
            # Step 4: Fetch full content for all filtered threads
            threads_with_content = await fetch_all_content(
                customer_last_threads=customer_last_threads,
                email_handler=self.email_handler,
                company_email_addresses=self.company_email_addresses,
                colors=COLORS
            )
            
            # Step 5: Classify emails to determine which need responses
            threads_for_response = await classify_emails(
                threads_with_content=threads_with_content,
                classify_email_func=self.classify_email,
                mark_as_spam=self.mark_email_as_spam,
                mark_as_responded=self.mark_email_as_responded,
                colors=COLORS
            )
            
            # Step 6: Generate AI responses for threads that need them
            try:
                generated_responses = await generate_responses(
                    threads_for_response=threads_for_response,
                    create_draft_response_func=self.create_draft_response,
                    colors=COLORS
                )
            except Exception as e:
                print(f"{RED}Error in generate_responses: {str(e)}{RESET}")
                import traceback
                print(f"{RED}Stack trace: {traceback.format_exc()}{RESET}")
                return {
                    "total_emails": total_emails,
                    "total_threads": len(full_threads),
                    "customer_last_emails": len(customer_last_threads),
                    "threads_processed": 0,
                    "error": f"Error generating responses: {str(e)}"
                }
            
            # Step 7: Create drafts in Zoho Mail
            try:
                results = await create_drafts(
                    responses_from_step6=generated_responses,
                    email_handler=self.email_handler,
                    company_email_addresses=self.company_email_addresses,
                    colors=COLORS,
                    enable_draft_creation=enable_draft_creation
                )
            except Exception as e:
                print(f"{RED}Error in create_drafts: {str(e)}{RESET}")
                import traceback
                print(f"{RED}Stack trace: {traceback.format_exc()}{RESET}")
                return {
                    "total_emails": total_emails,
                    "total_threads": len(full_threads),
                    "customer_last_emails": len(customer_last_threads),
                    "responses_generated": len(generated_responses),
                    "threads_processed": 0,
                    "error": f"Error creating drafts: {str(e)}"
                }
            
            # Mark processed emails as responded
            for result in results:
                message_id = result.get("message_id")
                if message_id:
                    self.mark_email_as_responded(message_id)
            
            # Final summary with color
            print(f"\n{GREEN}═════════════════════════════════════════════════════════════{RESET}")
            print(f"{GREEN}▶▶▶ RESULTS SUMMARY ◀◀◀{RESET}")
            print(f"{GREEN}═════════════════════════════════════════════════════════════{RESET}")
            print(f"{GREEN}- Total emails fetched: {total_emails}{RESET}")
            print(f"{GREEN}- Total threads: {len(full_threads)}{RESET}")
            print(f"{GREEN}- Customer last emails: {len(customer_last_threads)}{RESET}")
            print(f"{GREEN}- Threads processed: {len(results)}{RESET}")
            
            if enable_draft_creation:
                print(f"{GREEN}- Drafts created: {len(results)}{RESET}")
            else:
                print(f"{YELLOW}Running in TEST MODE - no drafts were actually created{RESET}")
            
            # Output results
            return {
                "total_emails": total_emails,
                "total_threads": len(full_threads),
                "customer_last_emails": len(customer_last_threads),
                "threads_processed": len(results),
                "results": results
            }
        except Exception as e:
            print(f"{RED}Unexpected error in process_emails: {str(e)}{RESET}")
            import traceback
            print(f"{RED}Stack trace: {traceback.format_exc()}{RESET}")
            return {"error": f"Unexpected error: {str(e)}"}

def get_mail_handler():
    """Get or create a mail handler instance"""
    return ZohoMailHandler()