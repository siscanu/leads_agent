"""
Step 2: Organize Emails by Thread ID
This module handles organizing emails by thread ID and fetching full thread information.
"""
from typing import Dict, Any

async def organize_emails_by_thread(recent_emails: Dict[str, Any], email_handler, 
                                  spam_emails: set, colors) -> Dict[str, Dict[str, Any]]:
    """
    Step 2: Organize emails by thread ID and fetch full thread information
    Returns a dictionary with thread IDs as keys and thread data as values
    """
    GREEN, RED, RESET = colors["GREEN"], colors["RED"], colors["RESET"]
    
    print(f"\n{GREEN}═════════════════════════════════════════════════════════════{RESET}")
    print(f"{GREEN}▶▶▶ STEP 2: FETCHING EMAILS BY THREAD ID ◀◀◀{RESET}")
    print(f"{GREEN}═════════════════════════════════════════════════════════════{RESET}")
    print(f"\n{GREEN}=== Step 2: Organizing Emails by Thread ID ==={RESET}")
    
    if "data" not in recent_emails:
        print(f"{RED}No emails to organize{RESET}")
        return {}
    
    # First organize by thread ID
    threads = {}
    standalone_emails = []
    
    # Group emails by thread ID
    for email in recent_emails["data"]:
        thread_id = email.get("threadId")
        if thread_id:
            # Parse received time as integer for accurate comparison
            try:
                current_time = int(threads.get(thread_id, {}).get("receivedTime", 0))
                new_time = int(email.get("receivedTime", 0))
            except (ValueError, TypeError):
                # Fallback if time is not a valid integer
                current_time = 0
                new_time = 1
            
            # If thread already exists, check if this email is newer
            if thread_id in threads:
                if new_time > current_time:
                    threads[thread_id] = email
                    print(f"Updated thread {thread_id} with newer email, time: {new_time}")
            else:
                threads[thread_id] = email
                print(f"Added new thread {thread_id}, time: {new_time}")
        else:
            standalone_emails.append(email)
    
    # Add standalone emails to the result with their message ID as key
    for email in standalone_emails:
        message_id = email.get("messageId", "standalone_" + str(len(threads)))
        threads[f"standalone_{message_id}"] = email
    
    print(f"{GREEN}Organized emails into {len(threads)} threads{RESET}")
    
    # Now fetch full thread information for each thread ID
    thread_ids = []
    full_threads = {}
    
    # Find all the thread IDs from the emails
    for thread_id in threads.keys():
        if not thread_id.startswith("standalone_"):
            thread_ids.append(thread_id)
    
    # Fetch all thread emails for each thread ID
    for thread_id in thread_ids:
        print(f"Fetching emails for thread: {thread_id}")
        # Skip if thread is already marked as spam
        if f"thread_{thread_id}" in spam_emails:
            print(f"{RED}Skipping thread {thread_id} - previously marked as spam{RESET}")
            continue
        
        thread_result = await email_handler.list_emails(threadId=thread_id)
        if "data" in thread_result and thread_result["data"]:
            # Sort emails in thread by receivedTime
            thread_emails = sorted(
                thread_result["data"],
                key=lambda x: int(x.get("receivedTime", 0)),
                reverse=True  # newest first
            )
            full_threads[thread_id] = thread_emails
            print(f"Found {len(thread_emails)} emails in thread {thread_id}")
    
    # Add standalone emails to the result with their message ID as key
    for thread_id, email in threads.items():
        if thread_id.startswith("standalone_"):
            full_threads[thread_id] = [email]
    
    # Raw data dump 
    # print(f"{colors['WHITE']}RAW_FULL_THREADS:{RESET}")
    # print(json.dumps(full_threads, indent=2, default=str))
    
    print(f"{GREEN}Organized {len(full_threads)} threads with full email lists{RESET}")
    
    return full_threads 