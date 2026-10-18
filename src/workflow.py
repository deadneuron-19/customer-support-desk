import json
from pathlib import Path
from datetime import datetime, timezone

from schemas.ticket import TicketInput
from schemas.classification import TicketClassification
from schemas.case_result import ResolutionDecision, CustomerResponse
from schemas.summary import FinalTicketSummary, RoutingResult

from chains.classification import classify_ticket
from chains.case_analysis import (
    ANALYSIS_CHAINS,
    run_analysis_chain,
)
from chains.response_generation import generate_response


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# --------------------------------------------------
# JSON HELPERS
# --------------------------------------------------

def load_json(filename, default=None):
    path = DATA_DIR / filename

    if not path.exists():
        return default if default is not None else []

    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def save_json(filename, data):
    path = DATA_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False, default=str)


def to_dict(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()

    return value


def select_records(records, ticket):
    """Return records relevant to this ticket."""

    if not isinstance(records, list):
        return records

    ticket_data = to_dict(ticket)
    order_id = ticket_data.get("order_id")
    customer_id = ticket_data.get("customer_id")

    # If no identifier is available, do not expose unrelated records.
    if not order_id and not customer_id:
        return []

    selected = []

    for record in records:
        if not isinstance(record, dict):
            continue

        matches_order = (
            order_id is not None
            and record.get("order_id") == order_id
        )
        matches_customer = (
            customer_id is not None
            and record.get("customer_id") == customer_id
        )

        if matches_order or matches_customer:
            selected.append(record)

    return selected


def get_policies(category):
    policies = load_json("company_policies.json", {})

    if isinstance(policies, dict):
        return policies.get(category, policies.get("default", policies))

    return policies


def get_business_records(category, ticket):
    ticket_data = to_dict(ticket)

    if category in ("billing", "cancellation_refund"):
        return select_records(
            load_json("payments.json", []),
            ticket,
        )

    if category == "account":
        return select_records(
            load_json("accounts.json", []),
            ticket,
        )

    if category == "order_delivery":
        return select_records(
            load_json("orders.json", []),
            ticket,
        )

    if category == "technical":
        # Known incidents are shared operational data, not customer data.
        return load_json("known_incidents.json", [])

    if category == "general":
        return get_policies("general")

    return []


# --------------------------------------------------
# ROUTING
# --------------------------------------------------

def route_ticket(category):
    routes = {
        "billing": ("billing", "billing_analysis"),
        "technical": ("technical", "technical_analysis"),
        "account": ("account", "account_analysis"),
        "cancellation_refund": (
            "refunds",
            "cancellation_refund_analysis",
        ),
        "order_delivery": (
            "delivery_support",
            "order_delivery_analysis",
        ),
        "general": ("general_support", "general_analysis"),
    }

    department, analysis_type = routes.get(
        category,
        ("human_review", "human_review"),
    )

    return RoutingResult(
        department=department,
        analysis_type=analysis_type,
        reason=f"Ticket classified as {category}",
        requires_human_review=category not in ANALYSIS_CHAINS,
    )


# --------------------------------------------------
# RESOLUTION POLICY
# --------------------------------------------------

def decide_resolution(classification, analysis, policy):
    """
    Conservative example policy.

    Customize these rules to match your fictional company's
    actual policies. The LLM does not authorize financial actions.
    """

    policy_text = json.dumps(policy, ensure_ascii=False, default=str).lower()

    if classification.confidence < 0.70:
        return ResolutionDecision(
            resolution_type="escalate",
            human_required=True,
            customer_response_allowed=False,
            reason="Classification confidence is below the configured threshold.",
        )

    if classification.priority == "critical":
        return ResolutionDecision(
            resolution_type="escalate",
            human_required=True,
            customer_response_allowed=False,
            reason="Critical tickets require immediate human review.",
        )

    if analysis.status in ("failed", "record_not_found"):
        return ResolutionDecision(
            resolution_type="escalate",
            human_required=True,
            customer_response_allowed=False,
            reason="Investigation failed or required records were not found.",
        )

    if analysis.status == "needs_information":
        return ResolutionDecision(
            resolution_type="request_information",
            human_required=False,
            customer_response_allowed=True,
            reason="Additional information is required.",
            required_actions=["Request the missing information"],
        )

    if classification.category in ("billing", "cancellation_refund"):
        return ResolutionDecision(
            resolution_type="escalate",
            human_required=True,
            customer_response_allowed=True,
            reason="Billing or refund cases require human verification.",
            required_actions=["Review payment records and applicable policy"],
        )

    if "human_approval_required" in policy_text:
        return ResolutionDecision(
            resolution_type="escalate",
            human_required=True,
            customer_response_allowed=False,
            reason="Company policy requires human approval.",
        )

    return ResolutionDecision(
        resolution_type="self_service",
        human_required=False,
        customer_response_allowed=True,
        reason="No escalation rule was triggered; a response draft may be prepared.",
    )


# --------------------------------------------------
# CASE ANALYSIS
# --------------------------------------------------

def analyze_case(ticket, classification):
    category = classification.category

    if category not in ANALYSIS_CHAINS:
        return None, RoutingResult(
            department="human_review",
            analysis_type="human_review",
            reason="No analysis chain is configured for this category.",
            requires_human_review=True,
        )

    routing = route_ticket(category)

    records = get_business_records(category, ticket)
    policies = get_policies(category)

    analysis = run_analysis_chain(
        ANALYSIS_CHAINS[category],
        ticket,
        classification,
        records,
        policies,
    )

    return (analysis, records, policies), routing


# --------------------------------------------------
# MAIN WORKFLOW
# --------------------------------------------------

def process_ticket(ticket):
    if not isinstance(ticket, TicketInput):
        ticket = TicketInput.model_validate(ticket)

    # Stage 1: Classification
    classification = classify_ticket(ticket)

    # Stage 2: Routing and case analysis
    analysis_result, routing = analyze_case(ticket, classification)

    if analysis_result is None:
        resolution = ResolutionDecision(
            resolution_type="escalate",
            human_required=True,
            customer_response_allowed=False,
            reason=routing.reason,
        )

        case_analysis = {
            "status": "needs_information",
            "findings": [],
            "missing_information": [],
            "recommended_action": "Human review",
        }

        response = CustomerResponse(
            status="not_generated",
            subject=None,
            body=None,
            language=classification.language,
            requires_approval=True,
            internal_note=routing.reason,
        )

    else:
        analysis, records, policies = analysis_result

        # Stage 3: Resolution decision
        resolution = decide_resolution(
            classification,
            analysis,
            policies,
        )

        # Stage 4: Generate draft only if permitted
        response = generate_response(
            customer_message=ticket.message,
            classification=classification,
            case_analysis=analysis,
            resolution=resolution,
        )

        case_analysis = analysis.model_dump()

    # Stage 5: Build final summary
    if resolution.human_required:
        ticket_status = "awaiting_human_review"
    elif response.status == "not_generated":
        ticket_status = "awaiting_information"
    else:
        ticket_status = "classified"

    summary = FinalTicketSummary(
        ticket_id=ticket.ticket_id,
        classification=classification,
        routing=routing,
        case_analysis=case_analysis,
        resolution=resolution,
        response=response,
        ticket_status=ticket_status,
        processing_errors=[],
    )

    return summary


# --------------------------------------------------
# SAVE PROCESSED TICKETS
# --------------------------------------------------

def save_processed_ticket(summary):
    filename = "processed_tickets.json"
    existing = load_json(filename, [])

    if not isinstance(existing, list):
        existing = []

    record = summary.model_dump(mode="json")
    record["processed_at"] = datetime.now(timezone.utc).isoformat()

    existing.append(record)
    save_json(filename, existing)