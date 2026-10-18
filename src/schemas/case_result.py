from typing import Literal, Optional
from pydantic import BaseModel, Field


AnalysisStatus = Literal[
    "completed",
    "needs_information",
    "record_not_found",
    "failed",
]


ResolutionType = Literal[
    "self_service",
    "resolve",
    "escalate",
    "request_information",
]


class BillingAnalysis(BaseModel):
    status: AnalysisStatus
    order_id: Optional[str] = None
    payment_status: Optional[str] = None
    transaction_ids: list[str] = Field(default_factory=list)
    duplicate_payment_detected: Optional[bool] = None
    refund_status: Optional[str] = None
    verified_facts: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_action: str


class TechnicalAnalysis(BaseModel):
    status: AnalysisStatus
    issue_type: str
    error_message: Optional[str] = None
    affected_service: Optional[str] = None
    known_incident_found: bool = False
    troubleshooting_steps: list[str] = Field(default_factory=list)
    verified_facts: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_action: str


class AccountAnalysis(BaseModel):
    status: AnalysisStatus
    account_status: Optional[str] = None
    access_issue: Optional[str] = None
    identity_verification_required: bool = True
    verified_facts: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_action: str


class CancellationRefundAnalysis(BaseModel):
    status: AnalysisStatus
    order_id: Optional[str] = None
    cancellation_status: Optional[str] = None
    refund_status: Optional[str] = None
    policy_eligibility: Literal[
        "eligible",
        "ineligible",
        "requires_review",
        "unknown",
    ] = "unknown"
    verified_facts: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_action: str


class OrderDeliveryAnalysis(BaseModel):
    status: AnalysisStatus
    order_id: Optional[str] = None
    delivery_status: Optional[str] = None
    estimated_delivery: Optional[str] = None
    tracking_id: Optional[str] = None
    delay_detected: Optional[bool] = None
    verified_facts: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_action: str


class GeneralAnalysis(BaseModel):
    status: AnalysisStatus
    customer_intent: str
    policy_reference: Optional[str] = None
    verified_facts: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_action: str


class ResolutionDecision(BaseModel):
    resolution_type: ResolutionType
    human_required: bool
    customer_response_allowed: bool
    reason: str
    required_actions: list[str] = Field(default_factory=list)
    policy_violations: list[str] = Field(default_factory=list)


class CustomerResponse(BaseModel):
    status: Literal[
        "drafted",
        "not_generated",
        "awaiting_approval",
        "approved",
        "rejected",
    ]
    subject: Optional[str] = None
    body: Optional[str] = None
    language: str
    requires_approval: bool
    internal_note: Optional[str] = None