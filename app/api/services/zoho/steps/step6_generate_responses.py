"""
Step 6: Generate AI Responses
This module handles generating AI responses to emails that need a reply (without saving drafts).
"""
import json
from typing import Dict, Any, List

async def generate_responses(threads_for_response, create_draft_response_func, colors) -> List[Dict[str, Any]]:
    """
    Step 6: Generate AI responses for threads that need replies
    Returns a list of results with generated content (without creating drafts)
    """
    BLUE, RED, RESET = colors["BLUE"], colors["RED"], colors["RESET"]
    
    print(f"\n{BLUE}═════════════════════════════════════════════════════════════{RESET}")
    print(f"{BLUE}▶▶▶ STEP 6: GENERATING AI RESPONSES ◀◀◀{RESET}")
    print(f"{BLUE}═════════════════════════════════════════════════════════════{RESET}")
    print(f"{BLUE}Generating responses for {len(threads_for_response)} threads{RESET}")
    
    results = []
    for thread_data in threads_for_response:
        thread_id = thread_data["thread_id"]
        latest_email = thread_data["latest_email"]
        thread = thread_data["thread"]
        
        print(f"{BLUE}▶ Creating AI response for thread: {thread_id}{RESET}")
        
        try:
            # Generate response WITHOUT creating draft (passing create_draft=False)
            result = await create_draft_response_func(latest_email, thread, thread_id, create_draft=False)
            
            if "error" in result:
                print(f"{RED}Error generating response for thread {thread_id}: {result['error']}{RESET}")
            elif "response" in result and result["response"]:
                print(f"{BLUE}Successfully generated response ({len(result['response'])} chars){RESET}")
            else:
                print(f"{RED}No response generated for thread {thread_id}{RESET}")
                result["error"] = "No response content was generated"
            
            # Store the result along with thread data for step 7
            results.append({
                "thread_id": thread_id,
                "message_id": latest_email.get("messageId"),
                "subject": latest_email.get("subject"),
                "to_address": latest_email.get("fromAddress", ""),
                "cc_address": latest_email.get("ccAddress", ""),
                "is_standalone": thread_id.startswith("standalone_"),
                "latest_email": latest_email,
                "response": result.get("response", ""),
                "error": result.get("error", None)
            })
        except Exception as e:
            error_msg = f"Unexpected error generating response: {str(e)}"
            print(f"{RED}{error_msg}{RESET}")
            results.append({
                "thread_id": thread_id,
                "message_id": latest_email.get("messageId"),
                "subject": latest_email.get("subject"),
                "to_address": latest_email.get("fromAddress", ""),
                "cc_address": latest_email.get("ccAddress", ""),
                "is_standalone": thread_id.startswith("standalone_"),
                "response": "",
                "error": error_msg
            })
    
    # Raw data dump
    # print(f"{colors['WHITE']}RAW_GENERATED_RESPONSES:{RESET}")
    # print(json.dumps(results, indent=2, default=str))
    
    successful = sum(1 for r in results if r.get("response") and not r.get("error"))
    print(f"{BLUE}Successfully generated {successful} of {len(results)} AI responses{RESET}")
    
    return results 