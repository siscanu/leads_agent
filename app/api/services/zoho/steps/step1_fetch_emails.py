"""
Step 1: Fetch Basic Email List
This module handles fetching recent emails from Zoho.
"""
import json
from typing import Dict, Any

async def fetch_recent_emails(email_handler, limit: int, colors) -> Dict[str, Any]:
    """
    Fetch the most recent emails from the inbox
    Returns the raw API response with basic email information
    """
    BLUE, GREEN, RED, RESET = colors["BLUE"], colors["GREEN"], colors["RED"], colors["RESET"]
    
    print(f"\n{BLUE}═════════════════════════════════════════════════════════════{RESET}")
    print(f"{BLUE}▶▶▶ STEP 1: FETCHING BASIC EMAIL LIST ◀◀◀{RESET}")
    print(f"{BLUE}═════════════════════════════════════════════════════════════{RESET}")
    print(f"\n{BLUE}=== Step 1: Fetching {limit} Recent Emails ==={RESET}")
    
    # Make the API request
    result = await email_handler.list_emails(limit=limit)
    
    if "data" in result:
        print(f"{GREEN}Successfully fetched {len(result['data'])} emails{RESET}")
    else:
        print(f"{RED}Error fetching emails: {result.get('error', 'Unknown error')}{RESET}")
    
    # Raw data dump
    # print(f"{colors['WHITE']}RAW_EMAILS:{RESET}")
    # print(json.dumps(result, indent=2, default=str))
    
    total_emails = len(result.get("data", []))
    print(f"{BLUE}Fetched {total_emails} recent emails{RESET}")
    
    return result 