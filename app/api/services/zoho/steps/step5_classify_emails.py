"""
Step 5: Classify Emails
This module handles classifying emails to determine if they need a response.
"""
import json
from typing import Dict, Any, List

async def classify_thread(thread_data, classify_email_func, mark_as_spam, mark_as_responded, colors):
    """
    Classify a single thread and determine if it needs a response
    Returns classification result and whether it needs response
    """
    CYAN, RED, YELLOW, GREEN, RESET = colors["CYAN"], colors["RED"], colors["YELLOW"], colors["GREEN"], colors["RESET"]
    
    thread_id = thread_data["thread_id"]
    latest_email = thread_data["latest_email"]
    content = latest_email.get("content", "")
    
    if not content:
        print(f"{RED}Skipping thread {thread_id} - no content available{RESET}")
        return None
    
    # Classify the email
    print(f"{CYAN}▶ Classifying thread: {thread_id}{RESET}")
    
    # First do a simple check for confirmation/thank you emails
    # These are almost always from customers confirming appointments
    subject_lower = latest_email.get('subject', '').lower()
    content_lower = content.lower()
    
    # Check if this is likely a confirmation email
    is_confirmation = (
        ('thank' in content_lower or 'confirm' in content_lower or 'perfect' in content_lower) and
        len(content) < 200 and  # Short messages are often confirmations
        ('cleaning' in subject_lower or 'service' in subject_lower or 'booking' in subject_lower)
    )
    
    if is_confirmation:
        print(f"{YELLOW}Classification: RELEVANT but NO RESPONSE NEEDED - Appears to be a confirmation/thank you message{RESET}")
        classification = {
            "is_cleaning_related": True,
            "needs_response": False
        }
    else:
        # For other emails, use the classification agent
        classification = await classify_email_func(latest_email, content)
    
    # Skip if not cleaning related (mark as spam)
    if not classification["is_cleaning_related"]:
        print(f"{RED}Marking thread {thread_id} as spam{RESET}")
        message_id = latest_email.get("messageId")
        mark_as_spam(message_id, thread_id)
        return {
            "thread_id": thread_id,
            "result": classification, 
            "needs_response": False
        }
    
    # Skip if no response needed
    if not classification["needs_response"]:
        print(f"{YELLOW}Thread {thread_id} - No response needed{RESET}")
        # Still mark as responded to avoid reprocessing
        message_id = latest_email.get("messageId")
        if message_id:
            mark_as_responded(message_id)
        return {
            "thread_id": thread_id,
            "result": classification,
            "needs_response": False
        }
    
    # Thread needs response
    print(f"{GREEN}Thread {thread_id} - Response needed{RESET}")
    return {
        "thread_id": thread_id,
        "result": classification,
        "needs_response": True,
        "thread_data": thread_data
    }

async def classify_emails(threads_with_content, classify_email_func, mark_as_spam, mark_as_responded, colors) -> List[Dict[str, Any]]:
    """
    Step 5: Classify emails to determine which need responses
    Returns information about classified threads which need responses
    """
    CYAN, RESET = colors["CYAN"], colors["RESET"]
    
    print(f"\n{CYAN}═════════════════════════════════════════════════════════════{RESET}")
    print(f"{CYAN}▶▶▶ STEP 5: CLASSIFYING EMAILS ◀◀◀{RESET}")
    print(f"{CYAN}═════════════════════════════════════════════════════════════{RESET}")
    
    threads_for_response = []
    all_classifications = []
    
    for thread_data in threads_with_content:
        result = await classify_thread(thread_data, classify_email_func, mark_as_spam, mark_as_responded, colors)
        
        if result:
            all_classifications.append({
                "thread_id": result["thread_id"], 
                "result": result["result"]
            })
            
            if result["needs_response"]:
                threads_for_response.append(result["thread_data"])
    
    # Raw data dump
    print(f"{colors['WHITE']}RAW_CLASSIFICATIONS:{RESET}")
    print(json.dumps(all_classifications, indent=2, default=str))
    # print(f"{colors['WHITE']}RAW_THREADS_FOR_RESPONSE:{RESET}")
    # print(json.dumps(threads_for_response, indent=2, default=str))
    
    print(f"{CYAN}Found {len(threads_for_response)} threads needing response{RESET}")
    
    return threads_for_response 