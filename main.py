import sys
from pathlib import Path

# Add the project root directory to Python's module search path
# This ensures that absolute imports work correctly
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI # type: ignore
import uvicorn # type: ignore

# Initialize FastAPI app
app = FastAPI(title="Live Chat API")

# Import and include the live chat router
from app.api.webhooks.live_chat import router as live_chat_router
app.include_router(live_chat_router)

# Import and include the Zoho Mail webhook router
from app.api.webhooks.zoho_mails import router as zoho_mails_router
app.include_router(zoho_mails_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

# For direct script execution
if __name__ == "__main__":
    # You can also run this with:
    # python3 -m uvicorn main:app --reload --port 5060
    uvicorn.run(app, host="0.0.0.0", port=5060)