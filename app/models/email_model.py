from pydantic import BaseModel, Field

class EmailClassification(BaseModel):
    """
    Model to classify if an email is related to cleaning services and should be responded to.
    """
    is_cleaning_related: bool = Field(
        ..., 
        description="Whether the email is related to cleaning services. Set to True if the email mentions cleaning services, quotes, bookings, or related inquiries."
    )
    needs_response: bool = Field(
        ...,
        description="Whether the email needs a response. Set to False if the email is a confirmation, thank you note, or if the conversation has concluded (e.g. agreed to call, booked appointment)."
    )
    reason: str = Field(
        ..., 
        description="Brief explanation of why this email is or isn't cleaning related and whether it needs a response. Keep it concise."
    )
