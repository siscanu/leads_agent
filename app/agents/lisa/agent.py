from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools
from agno.tools.googlecalendar import GoogleCalendarTools
# from app.tools.google_calendar import GoogleCalendarTools
# from agno.tools.google_maps import GoogleMapTools
from app.tools.google_maps import GoogleMapTools
# from app.tools.telegram.telegram_tool import TelegramTools
from app.models.chat_model import AgentResponse
from app.agents.lisa.behaviour import agent_instructions, agent_description
# from agno.tools.telegram import TelegramTools
from app.utils.config import get_agent_config

import datetime
# from tzlocal import get_localzone_name

# Create the agent instance
def create_agent(chatwoot_conversation_id: str = None):
    # Get configuration from config module
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
            CalculatorTools(
                add=True,
                subtract=True,
                multiply=True,
                divide=True,
                exponentiate=True,
                factorial=True,
                is_prime=True,
                square_root=True,
            ),
            GoogleCalendarTools(
                credentials_path="secrets/client_secret_836000232789-l1ae1n2burh365vr9iiktkoff5lo9kt4.apps.googleusercontent.com.json",
                token_path="secrets/token.json"  # Specify token path
            ),
            GoogleMapTools(key=config['google_maps_api_key'])
            # TelegramTools(token=config['telegram_bot_token'], chat_id=config['telegram_chat_id'])
            ],
        show_tool_calls=True,
        markdown=True,
        debug_mode=True,
        stream=True,  # Enable streaming responses
        add_datetime_to_instructions=True,
    )
    
    return agent

# No global instance - each conversation will create its own dedicated instance 