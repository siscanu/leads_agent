"""
Step 3: Filter Threads Based on Last Email Sender
This module handles filtering threads to identify relevant customer emails.
"""
import json
import html
from typing import Dict, Any, List

def clean_email_address(raw_address):
    """Clean an email address by unescaping HTML entities and removing angle brackets"""
    if not raw_address:
        return ""
    address = html.unescape(raw_address).lower().strip()
    address = address.replace("<", "").replace(">", "").strip()
    return address

def get_clean_email_addresses(raw_addresses):
    """Split and clean a string of comma-separated email addresses"""
    if not raw_addresses:
        return []
    
    # Split by comma and clean each address
    addresses = [clean_email_address(addr) for addr in raw_addresses.split(',')]
    return [addr for addr in addresses if addr]  # Filter out empty addresses

def filter_threads(full_threads: Dict[str, List[Dict[str, Any]]], 
                  company_email_addresses: List[str],
                  responded_emails: set,
                  spam_emails: set,
                  colors) -> Dict[str, Dict[str, Any]]:
    """
    Step 3: Filter out threads where the last email was sent by the company
    Returns a dictionary of threads that need processing
    """
    YELLOW, RED, GREEN, RESET = colors["YELLOW"], colors["RED"], colors["GREEN"], colors["RESET"]
    
    print(f"\n{YELLOW}═════════════════════════════════════════════════════════════{RESET}")
    print(f"{YELLOW}▶▶▶ STEP 3: FILTERING THREADS BASED ON LAST EMAIL SENDER ◀◀◀{RESET}")
    print(f"{YELLOW}═════════════════════════════════════════════════════════════{RESET}")
    
    # Convert company emails to lowercase for case-insensitive comparison
    company_emails_lower = [email.lower() for email in company_email_addresses]
    customer_last_threads = {}
    
    for thread_id, thread_emails in full_threads.items():
        if not thread_emails:
            continue
        
        # Get the latest email in the thread
        latest_email = thread_emails[0]  # Already sorted newest first
        
        # Skip if message is already marked as spam
        message_id = latest_email.get("messageId")
        if message_id in spam_emails:
            print(f"{RED}Skipping message {message_id} - previously marked as spam{RESET}")
            continue
        
        # Skip if we've already responded
        if message_id and message_id in responded_emails:
            print(f"{RED}Skipping {thread_id} - already responded - {message_id}{RESET}")
            continue
        
        # Get raw data
        raw_from_address = latest_email.get("fromAddress", "")
        raw_to_address = latest_email.get("toAddress", "")
        
        # Clean and process email addresses
        from_address = clean_email_address(raw_from_address)
        to_addresses = get_clean_email_addresses(raw_to_address)
        
        # Special case: Contact form submissions
        # A contact form is when the company emails itself with form data
        is_from_company = from_address in company_emails_lower
        has_company_recipient = any(addr in company_emails_lower for addr in to_addresses)
        
        is_contact_form = is_from_company and has_company_recipient
        
        if is_contact_form:
            print(f"{YELLOW}Thread {thread_id} - Including contact form submission{RESET}")
            print(f"{YELLOW}RAW FROM: {raw_from_address}{RESET}")
            print(f"{YELLOW}RAW TO: {raw_to_address}{RESET}")
            customer_last_threads[thread_id] = {
                "latest_email": latest_email,
                "thread_emails": thread_emails,
                "is_contact_form": True
            }
            continue
        
        # Regular case: Check if sender is a company email
        if is_from_company:
            print(f"{RED}Thread {thread_id} - SKIPPING: Last email from company ({from_address}){RESET}")
            continue
        
        # Only keep threads where the last email is from a customer
        print(f"{GREEN}Thread {thread_id} - FROM: {from_address} - SUBJECT: {latest_email.get('subject')}{RESET}")
        customer_last_threads[thread_id] = {
            "latest_email": latest_email,
            "thread_emails": thread_emails,
            "is_contact_form": False
        }
    
    # Raw data dump
    # print(f"{colors['WHITE']}RAW_CUSTOMER_THREADS:{RESET}")
    # print(json.dumps(customer_last_threads, indent=2, default=str))
    
    print(f"{YELLOW}Found {len(customer_last_threads)} threads with customer's last email{RESET}")
    
    return customer_last_threads 