from typing import Literal
from pydantic import BaseModel, Field


Category = Literal[
    "billing",
    "technical",
    "account",
    "cancellation_refund",
    "order_delivery",
    "general",
]

Priority = Literal["low", "medium", "high", "critical"]

Language = Literal[
    "English",
    "Hindi",
    "Punjabi",
    "Hinglish",
    "Other",
]

Sentiment = Literal[
    "positive",
    "neutral",
    "frustrated",
    "angry",
    "distressed",
]


class TicketClassification(BaseModel):
    category: Category
    issue_type: str = Field(
        description="Specific issue, such as duplicate_payment or login_failure",
    )
    priority: Priority
    language: Language
    sentiment: Sentiment
    summary: str = Field(
        description="Short summary of the customer's problem",
    )
    requires_investigation: bool
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)