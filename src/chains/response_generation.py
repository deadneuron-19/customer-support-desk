from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from llm_client import get_llm
from schemas.case_result import CustomerResponse

llm = get_llm()

parser = PydanticOutputParser(
    pydantic_object=CustomerResponse
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a professional customer support response writer.

        Write a clear, polite, concise response in the customer's
        language.

        Rules:
        - Use only verified findings and supplied policies.
        - Never invent refunds, payment statuses, delivery dates,
          or completed actions.
        - If the issue is unresolved, explain the next steps.
        - Do not reveal internal notes or sensitive information.
        - Never claim an email has been sent.
        - This is a draft and requires human approval.

        {format_instructions}
        """
    ),
    (
        "human",
        """
        CUSTOMER MESSAGE:
        {customer_message}

        CLASSIFICATION:
        {classification}

        CASE ANALYSIS:
        {case_analysis}

        RESOLUTION DECISION:
        {resolution}
        """
    ),
])

response_generation_chain = (
    prompt.partial(
        format_instructions=parser.get_format_instructions()
    )
    | llm
    | parser
)


def generate_response(
    customer_message,
    classification,
    case_analysis,
    resolution,
):
    # Do not call the LLM if policy forbids a customer response.
    if not resolution.customer_response_allowed:
        return CustomerResponse(
            status="not_generated",
            subject=None,
            body=None,
            language=classification.language,
            requires_approval=True,
            internal_note=resolution.reason,
        )

    response = response_generation_chain.invoke({
        "customer_message": customer_message,
        "classification": classification.model_dump_json(),
        "case_analysis": case_analysis.model_dump_json(),
        "resolution": resolution.model_dump_json(),
    })

    # Enforce human approval in Python.
    response.requires_approval = True

    if response.status in ("approved", "rejected"):
        response.status = "drafted"

    return response