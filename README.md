# OpenLeadsAI

<img src="https://img.shields.io/badge/Status-Beta-yellow" alt="Beta Status"/> <img src="https://img.shields.io/badge/Platform-Agno-blue" alt="Agno Platform"/> <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>

OpenLeadsAI is an open-source AI customer support automation system built on the Agno framework. It provides intelligent chat and email agents that help businesses handle customer inquiries efficiently.

## 🚀 Key Features

### 💬 AI-Powered Live Chat (Chatwoot Integration)
- **Instant Response**: Automatically processes and responds to customer chat messages
- **Human Takeover**: Seamless handoff when a human agent takes ownership
- **Contextual Memory**: Maintains conversation history for relevant responses
- **Auto-Information Extraction**: Captures customer details from first contact
- **Separate Bot Instances**: Creates unique context for each customer conversation

### 📧 Smart Email Processing (Zoho Mail - Beta)
- **Automated Draft Creation**: Generates response drafts for human review
- **Intelligent Classification**: Identifies which emails need responses
- **Thread Organization**: Groups emails by conversation for context
- **Spam Detection**: Automatically filters irrelevant messages
- **Response Tracking**: Avoids duplicate responses to the same inquiry

### 🛠️ Integrated Tools
- **Calendar Management**: Google Calendar integration for appointment scheduling
- **Location Verification**: Google Maps integration for service area validation
- **Pricing Engine**: Sophisticated pricing calculator based on service details

## 📋 Requirements

- Python 3.9+
- FastAPI & Uvicorn
- OpenAI API key
- Zoho Mail account (for email features)
- Chatwoot instance (for chat features)
- Google Cloud credentials (for Maps & Calendar)

## 🔧 Quick Setup

```bash
# Clone the repository
git clone https://github.com/siscanu/leads_agent.git
cd leads_agent

# Install dependencies
pip install -r req.txt

# Set up environment variables
.env
# Edit .env with your API keys and credentials

# Start the server
python3 -m uvicorn main:app --reload --port 5060
```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Chatwoot Configuration
CHATWOOT_API_TOKEN=your_chatwoot_api_token
CHATWOOT_ACCOUNT_ID=your_chatwoot_account_id  # Must match the bot's account ID
CHATWOOT_BASE_URL=https://app.chatwoot.com

# Zoho Mail Configuration
ZOHO_CLIENT_ID=your_zoho_client_id
ZOHO_CLIENT_SECRET=your_zoho_client_secret
ZOHO_REFRESH_TOKEN=your_zoho_refresh_token
ZOHO_ACCOUNT_ID=your_zoho_account_id
ZOHO_DOMAIN=zoho.eu
ZOHO_DEFAULT_SENDER=your_default_email@domain.com

# Google API Configuration
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## 🔍 How It Works

### Live Chat Flow

```
1. Customer sends message via Chatwoot
2. Webhook triggers OpenLeadsAI
3. System checks if human agent assigned
   └── If yes: Skip AI processing
   └── If no: Continue AI processing
4. AI analyzes message content
5. Location validated with Google Maps
6. Response generated with pricing if requested
7. Response sent back to Chatwoot
```

### Email Processing Flow (Beta)

```
1. New email notification via Zoho webhook
2. System fetches recent emails (limited to 3)
3. Emails organized by conversation thread
4. AI classifies if email needs response
5. For relevant emails, AI generates response
6. Draft created in Zoho Mail for human review
7. Human can edit & send or discard draft
```

## 🛣️ API Endpoints

- **Live Chat**: `POST /live-chat/` - Webhook for Chatwoot integration
- **Email**: `POST /zoho-mails/` - Webhook for Zoho Mail integration
- **Health Check**: `GET /` - Simple endpoint to verify API is running

## 📁 Project Structure

```
app/
├── agents/           # AI agent definitions
│   ├── lisa/         # Chat agent
│   └── zoho/         # Email agents
├── api/              # API endpoints and services
│   ├── webhooks/     # External service webhooks
│   └── services/     # Service integrations
├── models/           # Data models and schemas
├── tools/            # Custom tools for agents
└── utils/            # Utility functions
```

## 🔄 Current Limitations & Roadmap

- **Email**: Currently creates drafts only (no auto-sending)
- **Conversation Flow**: Limited handling of complex multi-turn interactions
- **Phone Agent**: Coming soon - integration with phone call systems

## 🙋‍♂️ How to Contribute

Contributions are welcome! Areas where help is needed:

- Phone call agent implementation
- Enhanced error handling and logging
- Additional messaging platform integrations
- Test coverage improvements

## 📄 License

This project is open source and available under the MIT License.

## 📊 Project Status

OpenLeadsAI is currently in beta. While the chat integration is fully functional, email processing is still in testing phase.
