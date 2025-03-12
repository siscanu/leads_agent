from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    """
    A model to structure the agent's response with clear guidelines about pricing presentation.
    """
    final_message: str = Field(
        ..., 
        description="The polished, final message that will be shown to the customer. This should not include any reasoning, thought process, or price breakdowns. When presenting pricing information, only provide the total price range (e.g., 'The total estimated price is between €X and €Y') without itemizing individual service costs. Never list out individual prices for bedrooms, bathrooms, or other services separately."
    )
