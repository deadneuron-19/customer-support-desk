from typing import Literal, Optional
from pydantic import BaseModel, Field


TicketChannel = Literal[
    "email",
    "chat",
    "phone_transcript",
    "web_form",
]


class ConversationMessage(BaseModel):
    role: Literal["customer", "support"]
    content: str = Field(min_length=1)
    timestamp: Optional[str] = None


class TicketInput(BaseModel):
    ticket_id: str = Field(description="Unique ticket identifier")
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    message: str = Field(
        min_length=1,
        description="Original customer complaint or query",
    )
    channel: TicketChannel
    order_id: Optional[str] = None
    conversation_history: list[ConversationMessage] = Field(
        default_factory=list,
    )