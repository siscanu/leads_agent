from typing import Dict, Optional, Any
import os
from app.agents.lisa.agent import create_agent
from app.api.services.chatwoot.send_message import responder
from app.utils.logger import log_json

# Cache of bot instances by Chatwoot conversation ID
conversation_bots = {}

class ChatwootConversationManager:
    """Manages conversation instances and message processing for Chatwoot"""
    
    @staticmethod
    def get_or_create_bot(conversation_id: str):
        """Get an existing bot instance or create a new one for this conversation"""
        if conversation_id not in conversation_bots:
            # Create new bot instance specifically for this Chatwoot conversation
            conversation_bots[conversation_id] = create_agent(chatwoot_conversation_id=conversation_id)
            print(f"Created new bot instance for Chatwoot conversation {conversation_id}")
        
        return conversation_bots[conversation_id]
    
    @staticmethod
    def is_valid_for_processing(webhook_data: dict) -> bool:
        """Check if this message should be processed by our agent"""
        # Get the agent ID from environment variables
        agent_id = os.getenv('CHATWOOT_ACCOUNT_ID')
        
        # Get assignee ID from webhook (if available)
        assignee = webhook_data.get("conversation", {}).get("meta", {}).get("assignee")
        
        # Skip only if there's an assignee and it's not this agent
        if assignee and str(assignee.get("id")) != agent_id:
            return False
            
        # Only process incoming messages from users
        if webhook_data.get("event") == "message_created" and webhook_data.get("message_type") == "incoming":
            return True
            
        return False
    
    @staticmethod
    def format_first_message(content: str, conversation_meta: dict) -> str:
        """Format the first message with user details if available"""
        sender_info = conversation_meta.get("sender", {})
        
        # Extract user details
        user_name = sender_info.get("name", "")
        user_email = sender_info.get("email", "")
        user_phone = sender_info.get("phone_number", "")
        
        # Format the first message with user details
        return f"""A new user needs your support.
        Provided details:
        Name: {user_name}
        Email: {user_email}
        Phone: {user_phone}
        Message: {content}"""
    
    @staticmethod
    def process_message(webhook_data: dict) -> Dict[str, Any]:
        """Process a message from Chatwoot and return a response"""
        try:
            # Extract conversation ID from webhook
            conversation_id = str(webhook_data.get("conversation", {}).get("id"))
            
            if not conversation_id:
                return {"status": "error", "message": "No conversation ID found in webhook"}
            
            # Check if this is a new conversation (no bot instance yet)
            is_new_conversation = conversation_id not in conversation_bots
            
            # Get or create a bot instance for this Chatwoot conversation
            bot = ChatwootConversationManager.get_or_create_bot(conversation_id)
            
            # Format message - if it's the first message, include user details
            user_message = webhook_data.get("content", "")
            if is_new_conversation and webhook_data.get("conversation", {}).get("meta"):
                user_message = ChatwootConversationManager.format_first_message(
                    user_message, 
                    webhook_data.get("conversation", {}).get("meta", {})
                )
            
            # Process the message with this conversation's bot
            response = bot.run(user_message)
            
            # Extract the final message from the structured response
            full_response = ""
            if hasattr(response, 'content') and response.content:
                # For structured outputs, content will be a dictionary with final_message
                if isinstance(response.content, dict) and 'final_message' in response.content:
                    full_response = response.content['final_message']
                # If it's a Pydantic model with a final_message attribute
                elif hasattr(response.content, 'final_message'):
                    full_response = response.content.final_message
                else:
                    # Fallback to using content directly if it's not structured or is a string
                    full_response = str(response.content)
            
            # Send response back to Chatwoot
            if full_response:
                try:
                    chatwoot_response = responder.send_response(
                        conversation_id=conversation_id,
                        message=full_response,
                        echo_id=None
                    )
                except Exception as e:
                    return {"status": "error", "message": f"Failed to send response: {str(e)}"}
            
            return {"status": "success", "response": full_response}
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return {"status": "error", "message": str(e)}

# Create a singleton instance
conversation_manager = ChatwootConversationManager() 