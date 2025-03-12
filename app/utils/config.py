import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Chatwoot configuration
CHATWOOT_CONFIG = {
    'api_token': os.getenv('CHATWOOT_API_TOKEN', ''),
    'account_id': os.getenv('CHATWOOT_ACCOUNT_ID', ''),
    'base_url': os.getenv('CHATWOOT_BASE_URL', 'https://app.chatwoot.com').rstrip('/')
}

# Agent configuration
AGENT_CONFIG = {
    'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
    'google_maps_api_key': os.getenv('GOOGLE_MAPS_API_KEY', ''),
    'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', '')
}

def get_chatwoot_config():
    """Get Chatwoot configuration settings"""
    return CHATWOOT_CONFIG 

def get_agent_config():
    """Get Agent configuration settings"""
    return AGENT_CONFIG 