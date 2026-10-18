import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from llm_client import get_llm
from schemas.case_result import (
    BillingAnalysis,
    TechnicalAnalysis,
    AccountAnalysis,
    CancellationRefundAnalysis,
    OrderDeliveryAnalysis,
    GeneralAnalysis,
)

llm = get_llm()


def to_json(data):
    if hasattr(data, "model_dump"):
        data = data.model_dump()

    if isinstance(data, str):
        return data

    return json.dumps(data, ensure_ascii=False, default=str)


def create_analysis_chain(schema, instructions):
    parser = PydanticOutputParser(pydantic_object=schema)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are a customer support case analyst.

            Analyze the ticket using only the supplied information.

            Rules:
            - Never invent records or investigation results.
            - Distinguish verified facts from possible causes.
            - Identify missing information.
            - Never claim an action was completed without evidence.
            - Follow the supplied company policies.
            - Never execute refunds or modify customer accounts.

            Specific instructions:
            {instructions}

            {format_instructions}
            """
        ),
        (
            "human",
            """
            TICKET:
            {ticket}

            CLASSIFICATION:
            {classification}

            BUSINESS RECORDS:
            {records}

            COMPANY POLICIES:
            {policies}
            """
        ),
    ])

    return (
        prompt.partial(
            instructions=instructions,
            format_instructions=parser.get_format_instructions(),
        )
        | llm
        | parser
    )


billing_analysis_chain = create_analysis_chain(
    BillingAnalysis,
    """
    Investigate duplicate payments, failed payments, incorrect charges,
    transaction records, and refund status.
    Never assume a refund has been issued.
    """,
)

technical_analysis_chain = create_analysis_chain(
    TechnicalAnalysis,
    """
    Investigate login failures, application errors, crashes,
    connectivity problems, and known service incidents.
    Distinguish possible causes from confirmed causes.
    """,
)

account_analysis_chain = create_analysis_chain(
    AccountAnalysis,
    """
    Investigate account access, locked accounts, and profile issues.
    Respect identity verification and account security.
    """,
)

cancellation_refund_analysis_chain = create_analysis_chain(
    CancellationRefundAnalysis,
    """
    Investigate cancellations and refund eligibility using supplied
    order records and company policies.
    Never authorize or issue refunds.
    """,
)

order_delivery_analysis_chain = create_analysis_chain(
    OrderDeliveryAnalysis,
    """
    Investigate delivery status, tracking information, missing
    deliveries, and delivery delays.
    Never invent tracking IDs or estimated delivery dates.
    """,
)

general_analysis_chain = create_analysis_chain(
    GeneralAnalysis,
    """
    Investigate general questions, feedback, and complaints.
    Identify customer intent, relevant policies, missing information,
    and appropriate next steps.
    """,
)


def run_analysis_chain(
    chain,
    ticket,
    classification,
    records,
    policies,
):
    return chain.invoke({
        "ticket": to_json(ticket),
        "classification": to_json(classification),
        "records": to_json(records),
        "policies": to_json(policies),
    })


ANALYSIS_CHAINS = {
    "billing": billing_analysis_chain,
    "technical": technical_analysis_chain,
    "account": account_analysis_chain,
    "cancellation_refund": cancellation_refund_analysis_chain,
    "order_delivery": order_delivery_analysis_chain,
    "general": general_analysis_chain,
}