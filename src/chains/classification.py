import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from llm_client import get_llm
from schemas.classification import TicketClassification

llm = get_llm()

parser = PydanticOutputParser(
    pydantic_object=TicketClassification
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You classify customer support tickets.

        Categories: billing, technical, account,
        cancellation_refund, order_delivery, general.

        Priorities: low, medium, high, critical.
        Languages: English, Hindi, Punjabi, Hinglish, Other.
        Sentiments: positive, neutral, frustrated, angry, distressed.

        Identify the issue type, customer sentiment, language,
        priority, summary, and missing information.

        Base priority on business impact, not anger alone.
        Never invent facts.

        {format_instructions}
        """
    ),
    (
        "human",
        "Classify this ticket:\n{ticket}"
    ),
])

classification_chain = (
    prompt.partial(
        format_instructions=parser.get_format_instructions()
    )
    | llm
    | parser
)


def classify_ticket(ticket):
    if hasattr(ticket, "model_dump"):
        ticket = ticket.model_dump()

    if not isinstance(ticket, str):
        ticket = json.dumps(ticket, ensure_ascii=False, default=str)

    return classification_chain.invoke({
        "ticket": ticket
    })