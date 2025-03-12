from agno.agent import Agent
from agno.models.openai import OpenAIChat
from app.models.chat_model import AgentResponse
from app.models.email_model import EmailClassification
from app.tools.google_maps import GoogleMapTools
from agno.tools.googlecalendar import GoogleCalendarTools
from app.agents.zoho.behaviour import agent_instructions, agent_description
from app.utils.config import get_agent_config

import datetime
# from tzlocal import get_localzone_name

# Create the classification agent instance
async def create_classification_agent():
    config = get_agent_config()
    
    agent = Agent(
        model=OpenAIChat(
            id="gpt-4o-mini",
            api_key=config['openai_api_key'],
        ),
        description="You classify if emails are related to cleaning services and need a response.",
        response_model=EmailClassification,
        structured_outputs=True,
        instructions="""
        Your task is to determine if an email is related to cleaning services and needs a response.
        
        Consider an email cleaning-related if it:
        - Asks about cleaning services or quotes
        - Discusses booking or scheduling cleaning
        - Has questions about cleaning methods or products
        - Mentions specific cleaning needs
        - Is about an existing cleaning service
        
        Mark as NOT cleaning-related if it:
        - Is spam or promotional content
        - Is completely unrelated to cleaning services
        - Is automated system notifications
        - Is marketing or sales pitches for other services
        
        Consider an email as NOT needing response if:
        - It's just saying "thank you" with no questions
        - It's confirming they received our message
        - It's confirming a scheduled call or meeting
        - It's confirming a booking that's already made
        - The conversation has reached a natural conclusion
        - We've already agreed on next steps (e.g. phone call)
        
        Always provide clear reasoning for both classifications.
        """
    )
    return agent

# Create the response agent instance
async def create_response_agent(chatwoot_conversation_id: str = None):
    config = get_agent_config()
    
    agent = Agent(
        model=OpenAIChat(
            id="gpt-4o-mini",
            api_key=config['openai_api_key'],  # Add API key from config
        ),
        add_history_to_messages=True,
        num_history_responses=20,
        # Set the session_id based on the Chatwoot conversation
        session_id=f"chatwoot_{chatwoot_conversation_id}" if chatwoot_conversation_id else None,
        response_model=AgentResponse,  # Add structured output model
        structured_outputs=True,  # Enable structured outputs
        description=agent_description,
        instructions=agent_instructions,
        tools=[
            GoogleCalendarTools(
                credentials_path="secrets/client_secret_836000232789-l1ae1n2burh365vr9iiktkoff5lo9kt4.apps.googleusercontent.com.json",
                token_path="secrets/token.json"  # Specify token path
            ),
            GoogleMapTools(key=config['google_maps_api_key']),
            ],
        show_tool_calls=True,
        markdown=False,  # Turn off markdown to prevent double-escaping with HTML
        debug_mode=True,
        stream=True,  # Enable streaming responses
        add_datetime_to_instructions=True,
    )
    
    return agent

# No global instance - each conversation will create its own dedicated instance 