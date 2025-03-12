"""
Step 7: Create Draft Emails
This module handles saving the generated AI responses as draft emails in Zoho Mail.
"""
import json
import re
from typing import Dict, Any, List

def extract_customer_email(content: str) -> str:
    """Extract customer email from form submission content"""
    email_match = re.search(r"Email:\s*([^\s]+@[^\s]+\.[^\s]+)", content)
    if email_match:
        return email_match.group(1)
    return ""

async def create_drafts(responses_from_step6, email_handler, company_email_addresses, colors, enable_draft_creation: bool = True) -> List[Dict[str, Any]]:
    """
    Step 7: Create draft emails in Zoho Mail using the responses from step 6
    Returns a list of results for each draft created
    """
    GREEN, RED, BLUE, YELLOW, RESET = colors["GREEN"], colors["RED"], colors["BLUE"], colors["YELLOW"], colors["RESET"]
    
    print(f"\n{GREEN}═════════════════════════════════════════════════════════════{RESET}")
    print(f"{GREEN}▶▶▶ STEP 7: CREATING DRAFT EMAILS IN ZOHO MAIL ◀◀◀{RESET}")
    print(f"{GREEN}═════════════════════════════════════════════════════════════{RESET}")
    print(f"{GREEN}Creating drafts for {len(responses_from_step6)} emails{RESET}")
    
    results = []
    
    if not enable_draft_creation:
        print(f"{YELLOW}Running in TEST MODE - no drafts will be created{RESET}")
        for response_data in responses_from_step6:
            results.append({
                "thread_id": response_data["thread_id"],
                "message_id": response_data["message_id"],
                "subject": response_data["subject"],
                "result": {
                    "response": response_data.get("response", ""),
                    "draft_created": False,
                    "test_mode": True
                }
            })
        return results
    
    for response_data in responses_from_step6:
        thread_id = response_data["thread_id"]
        subject = response_data["subject"]
        to_address = response_data["to_address"]
        cc_address = response_data.get("cc_address", "")
        response_content = response_data.get("response", "")
        error = response_data.get("error")
        is_contact_form = thread_id.startswith("standalone_") and "Email:" in response_data.get("latest_email", {}).get("content", "")
        
        # Skip if there was an error generating the response
        if error:
            print(f"{RED}▶ Skipping draft creation for thread {thread_id} due to error: {error}{RESET}")
            results.append({
                "thread_id": thread_id,
                "message_id": response_data["message_id"],
                "subject": subject,
                "result": {"error": error}
            })
            continue
        
        # Skip if no response content was generated
        if not response_content:
            print(f"{RED}▶ Skipping draft creation for thread {thread_id} - no response content{RESET}")
            results.append({
                "thread_id": thread_id,
                "message_id": response_data["message_id"],
                "subject": subject,
                "result": {"error": "No response content generated"}
            })
            continue
            
        print(f"{GREEN}▶ Creating draft for thread: {thread_id}{RESET}")
        
        # Format subject with Re: prefix if needed
        if subject and not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        
        # For contact forms, extract the customer email from the content
        if is_contact_form:
            content = response_data.get("latest_email", {}).get("content", "")
            customer_email = extract_customer_email(content)
            if customer_email:
                to_address = customer_email
                print(f"{GREEN}Using customer email from form: {customer_email}{RESET}")
            
        # Process CC addresses
        cc_list = [cc.strip() for cc in cc_address.split(",")] if cc_address else []
        # Only include CC addresses that are not company addresses
        cc_list = [cc for cc in cc_list if cc and cc.lower() not in [a.lower() for a in company_email_addresses]]
        
        # Log draft information
        print(f"{BLUE}Creating draft to: {to_address}{RESET}")
        if cc_list:
            print(f"{BLUE}CC: {', '.join(cc_list)}{RESET}")
        
        # Create the draft in Zoho Mail
        draft_result = await email_handler.create_draft(
            to=[to_address],
            subject=subject,
            body=response_content,
            cc=cc_list,
            is_html=True  # Always use HTML for consistent formatting
        )
        
        if "error" in draft_result:
            print(f"{RED}Error creating draft: {draft_result['error']}{RESET}")
            results.append({
                "thread_id": thread_id,
                "message_id": response_data["message_id"],
                "subject": subject,
                "result": {
                    "response": response_content,
                    "error": draft_result['error']
                }
            })
        else:
            print(f"{GREEN}Draft created successfully{RESET}")
            results.append({
                "thread_id": thread_id,
                "message_id": response_data["message_id"],
                "subject": subject,
                "result": {
                    "response": response_content,
                    "draft_id": draft_result.get("data", {}).get("draftId"),
                    "draft_created": True
                }
            })
    
    # Raw data dump
    print(f"{colors['WHITE']}RAW_DRAFT_RESULTS:{RESET}")
    print(json.dumps(results, indent=2, default=str))
    
    successful_drafts = sum(1 for r in results if r.get("result", {}).get("draft_created", False))
    print(f"{GREEN}Successfully created {successful_drafts} draft emails{RESET}")
    
    return results 