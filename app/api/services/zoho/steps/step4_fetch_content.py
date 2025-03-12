"""
Step 4: Fetch Full Content for Threads
This module handles fetching the full content for email threads.
"""
import json
import asyncio
import html
import re
from typing import Dict, Any, List
from app.api.services.zoho.steps.step3_filter_threads import clean_email_address

def clean_html(html_content):
    """Clean HTML content to plain text without line breaks"""
    # Remove HTML tags
    text = re.sub(r'<head.*?>.*?</head>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    
    # Replace common HTML entities
    text = html.unescape(text)
    
    # Replace <br>, <p>, <div> tags with spaces instead of newlines
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'</p>\s*<p[^>]*>', ' ', text)
    text = re.sub(r'<div[^>]*>', ' ', text)
    text = re.sub(r'</div>', '', text)
    
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Clean up whitespace - remove newlines completely
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)  # Reduce multiple spaces to single space
    
    return text.strip()

def remove_quoted_content(text):
    """Remove quoted email content from email body"""
    # Common email citation patterns
    patterns = [
        # Pattern: ---- On [date] [name] [email] wrote ----
        r'[-_]{2,}(\s)?On.*?wrote(\s)?[-_]{2,}.*',
        # Pattern: From: [sender] Sent: [date] To: [recipient]
        r'From:.*?Sent:.*?To:.*',
        # Pattern: On [date], [name] <[email]> wrote:
        r'On\s+.*?,\s+.*?\s+wrote:.*',
        # Pattern: On [date] at [time], [name] <[email]> wrote:
        r'On\s+.*?\s+at\s+.*?,\s+.*?\s+wrote:.*',
        # Pattern: -------- Original message -------- (mobile email format)
        r'[-]{4,}\s*Original message\s*[-]{4,}.*',
        # Pattern: Sent from my [device] followed by original message marker
        r'Sent from my.*?[-]{4,}.*',
        # Pattern: From: [sender] Date: [date] To: [recipient] (another email client format)
        r'From:.*?Date:.*?To:.*',
        # Pattern: From: [sender] Date: [date], at [time] To: [recipient] Subject: [subject]
        r'From:.*?Date:.*?at.*?To:.*?Subject:.*',
    ]
    
    # Apply each pattern
    for pattern in patterns:
        # First attempt - keep only the content before the pattern
        split_text = re.split(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if len(split_text) > 1:
            # Found a pattern match, keep only the content before it
            text = split_text[0].strip()
    
    # Check for any lines starting with ">" which is a common quote marker
    text = re.sub(r'(?m)^>.*$', '', text)
    
    # Clean up any trailing signatures or footers with common patterns
    text = re.sub(r'--\s*$.*', '', text, flags=re.DOTALL)  # "--" signature marker
    
    # Clean up any extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

async def fetch_thread_content(thread_info, email_handler, company_email_addresses, colors):
    """Fetch content for a thread asynchronously"""
    MAGENTA, RED, GREEN, YELLOW, CYAN, RESET = colors["MAGENTA"], colors["RED"], colors["GREEN"], colors["YELLOW"], colors["CYAN"], colors["RESET"]
    
    try:
        thread_id = thread_info["thread_id"]
        latest_email = thread_info["latest_email"]
        is_standalone = thread_info["standalone"]
        is_contact_form = thread_info.get("is_contact_form", False)
        
        print(f"\n{MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{MAGENTA}▶ PROCESSING THREAD: {thread_id}{RESET}")
        if is_contact_form:
            print(f"{YELLOW}This is a contact form submission{RESET}")
        
        # Log thread info at start
        print(f"\n{CYAN}=== Thread Info {thread_id} ==={RESET}")
        thread_info_log = {
            "is_standalone": is_standalone,
            "is_contact_form": is_contact_form,
            "email_from": latest_email.get("fromAddress"),
            "email_to": latest_email.get("toAddress"),
            "sender": latest_email.get("sender"),
            "subject": latest_email.get("subject")
        }
        print(json.dumps(thread_info_log, indent=2, default=str))
        
        # Helper function for fetching a single email's content
        async def fetch_single_email_content(email, msg_id, folder_id=None):
            """Internal helper to fetch content for a single email with retries"""
            max_retries = 3
            retry_count = 0
            
            folder_id = folder_id or email.get("folderId")
            if not folder_id:
                print(f"{RED}· Missing folder ID for email {msg_id}, cannot fetch content{RESET}")
                return False
            
            while retry_count < max_retries:
                try:
                    # Simplified log to reduce output clutter
                    print(f"{MAGENTA}· Fetching content for email {msg_id}{RESET}")
                    email_content = await email_handler.get_email_content(msg_id, folder_id)
                    
                    if "data" in email_content and "content" in email_content["data"]:
                        # Clean and store the content
                        content = clean_html(email_content["data"]["content"])
                        # Remove quoted email content
                        content = remove_quoted_content(content)
                        email["content"] = content
                        print(f"{GREEN}· Email {msg_id}: Content fetched ({len(content)} chars){RESET}")
                        return True
                    else:
                        error = email_content.get('error', 'Unknown error')
                        print(f"{RED}· Email {msg_id}: Failed to fetch content: {error}{RESET}")
                        retry_count += 1
                        await asyncio.sleep(1)  # Wait 1 second before retrying
                except Exception as e:
                    print(f"{RED}· Email {msg_id}: Exception fetching content: {str(e)}{RESET}")
                    retry_count += 1
                    await asyncio.sleep(1)
            
            # Failed after max retries
            print(f"{RED}· Email {msg_id}: Failed after {max_retries} attempts{RESET}")
            return False
        
        if is_standalone:
            # Handle standalone emails
            message_id = latest_email.get("messageId", "")
            folder_id = latest_email.get("folderId", "")
            
            if not folder_id:
                print(f"Missing folder ID for email {message_id}, cannot fetch content")
                thread = [latest_email]  # Fallback to basic email
                return {
                    "thread_id": thread_id,
                    "latest_email": latest_email,
                    "thread": thread
                }
            
            if message_id:
                print(f"Email (ID: {message_id}, folder ID: {folder_id})")
                success = await fetch_single_email_content(latest_email, message_id, folder_id)
                
                thread = [latest_email]
                if success:
                    print(f"Content: {latest_email.get('content', '')[:100]}...")
                else:
                    print(f"Failed to fetch content")
                
                return {
                    "thread_id": thread_id,
                    "latest_email": latest_email, 
                    "thread": thread
                }
            else:
                thread = [latest_email]  # Thread is just the single email
                return {
                    "thread_id": thread_id,
                    "latest_email": latest_email,
                    "thread": thread
                }
        else:
            # Fetch all emails in thread
            print(f"{MAGENTA}▶ Fetching thread: {thread_id}{RESET}")
            thread_response = await email_handler.list_emails(threadId=thread_id, limit=100)
            print(f"\n{CYAN}=== Thread Response for {thread_id} ==={RESET}")
            thread_log = {
                "has_data": "data" in thread_response,
                "has_error": "error" in thread_response,
                "emails_count": len(thread_response.get("data", [])) if "data" in thread_response else 0
            }
            print(json.dumps(thread_log, indent=2, default=str))
            
            if "data" in thread_response:
                # Sort thread emails by received time
                try:
                    thread = sorted(thread_response["data"], 
                                    key=lambda x: int(x.get("receivedTime", 0)))
                except (ValueError, TypeError):
                    # Fallback if sorting by time fails
                    thread = thread_response["data"]
                
                # Skip if the thread is empty
                if not thread:
                    print(f"{RED}Skipping thread {thread_id} - no emails found{RESET}")
                    return None
                
                # Use our original logic in the parent to determine if this is a contact form
                # Check if last email is the same as our last_email from parent (don't try to redetermine)
                if not is_contact_form and thread and len(thread) > 0:
                    last_email = thread[-1]
                    last_email_id = last_email.get("messageId", "")
                    latest_email_id = latest_email.get("messageId", "")
                    
                    # Verify if the email IDs match - they should match if we're looking at the same email
                    if last_email_id != latest_email_id:
                        print(f"{RED}⚠️ WARNING: Thread last email ID ({last_email_id}) doesn't match our latest email ID ({latest_email_id}){RESET}")
                        print(f"{YELLOW}Using our original determination to continue processing{RESET}")
                
                # Create tasks for fetching content for all emails in the thread
                fetch_tasks = []
                for email in thread:
                    msg_id = email.get("messageId")
                    if msg_id:
                        task = fetch_single_email_content(email, msg_id)
                        fetch_tasks.append(task)
                
                # Group all content fetching logs to keep them together
                print(f"{MAGENTA}━ Fetching content for {len(fetch_tasks)} emails in thread {thread_id} ━{RESET}")
                
                # Run all fetch tasks concurrently with retry logic
                if fetch_tasks:
                    results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
                    success_count = sum(1 for r in results if not isinstance(r, Exception) and r is True)
                    print(f"{GREEN}Fetched content for {success_count} out of {len(fetch_tasks)} emails in thread {thread_id}{RESET}")
                
                print(f"{GREEN}Total emails in thread {thread_id}: {len(thread)}{RESET}")
                
                # Check last email has content
                last_email_content = thread[-1].get("content", "")
                print(f"\n{CYAN}=== Last Email Content Length for {thread_id} ==={RESET}")
                content_length_log = {
                    "length": len(last_email_content),
                    "from": thread[-1].get("fromAddress"),
                    "has_content": bool(last_email_content)
                }
                print(json.dumps(content_length_log, indent=2, default=str))
                
                return {
                    "thread_id": thread_id,
                    "latest_email": thread[-1],
                    "thread": thread
                }
            else:
                print(f"{RED}Failed to fetch thread: {thread_response.get('error', 'Unknown error')}{RESET}")
                return None
    except Exception as e:
        print(f"{RED}Error processing thread {thread_info['thread_id']}: {str(e)}{RESET}")
        return None

async def fetch_all_content(customer_last_threads, email_handler, company_email_addresses, colors):
    """
    Step 4: Fetch full content for all filtered threads
    Returns a list of threads with full content
    """
    MAGENTA, RED, RESET = colors["MAGENTA"], colors["RED"], colors["RESET"]
    
    print(f"\n{MAGENTA}═════════════════════════════════════════════════════════════{RESET}")
    print(f"{MAGENTA}▶▶▶ STEP 4: FETCHING FULL CONTENT FOR {len(customer_last_threads)} THREADS ◀◀◀{RESET}")
    print(f"{MAGENTA}═════════════════════════════════════════════════════════════{RESET}")
    threads_with_content = []
    
    # Create tasks for fetching content for all threads
    fetch_tasks = []
    for thread_id, thread_data in customer_last_threads.items():
        thread_info = {
            "thread_id": thread_id,
            "latest_email": thread_data["latest_email"],
            "standalone": thread_id.startswith("standalone_"),
            "is_contact_form": thread_data["is_contact_form"]
        }
        task = fetch_thread_content(thread_info, email_handler, company_email_addresses, colors)
        fetch_tasks.append(task)
    
    # Run all fetch tasks concurrently
    if fetch_tasks:
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"{RED}Error fetching thread content: {result}{RESET}")
            elif result is not None:
                threads_with_content.append(result)
    
    # Raw data dump
    # print(f"{colors['WHITE']}RAW_THREADS_WITH_CONTENT:{RESET}")
    # print(json.dumps(threads_with_content, indent=2, default=str))
    
    print(f"{MAGENTA}Successfully fetched content for {len(threads_with_content)} threads{RESET}")
    
    return threads_with_content 