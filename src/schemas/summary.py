from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

from .classification import TicketClassification
from .case_result import (
    BillingAnalysis,
    TechnicalAnalysis,
    AccountAnalysis,
    CancellationRefundAnalysis,
    OrderDeliveryAnalysis,
    GeneralAnalysis,
    ResolutionDecision,
    CustomerResponse,
)


CaseAnalysisResult = Annotated[
    Union[
        BillingAnalysis,
        TechnicalAnalysis,
        AccountAnalysis,
        CancellationRefundAnalysis,
        OrderDeliveryAnalysis,
        GeneralAnalysis,
    ],
    Field(discriminator="category"),
]


# Add a category field to each analysis schema before
# using the discriminated union above.
# Each category must have a distinct Literal value.


class RoutingResult(BaseModel):
    department: str
    analysis_type: str
    reason: str
    requires_human_review: bool = False


class FinalTicketSummary(BaseModel):
    ticket_id: str
    classification: TicketClassification
    routing: RoutingResult
    case_analysis: dict
    resolution: ResolutionDecision
    response: CustomerResponse
    ticket_status: Literal[
        "received",
        "classified",
        "investigating",
        "awaiting_information",
        "awaiting_human_review",
        "resolved",
        "closed",
        "failed",
    ]
    processing_errors: list[str] = Field(default_factory=list)