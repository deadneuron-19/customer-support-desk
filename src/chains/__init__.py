from langchain_core.prompts import ChatPromptTemplate

from schemas.ticket import TicketInput
from schemas.classification import TicketClassification


def create_classification_chain(llm):
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are a customer support ticket classification system.

            Classify the customer's ticket using these rules:

            1. Select the most appropriate category.
            2. Identify the specific issue type using snake_case.
            3. Assign priority based on business impact and urgency.
            4. Identify the customer's language and sentiment.
            5. Identify information missing for investigation.
            6. Do not invent customer, order, or transaction details.
            7. A customer's anger alone does not make a ticket critical.
            8. If the category is uncertain, use general and lower confidence.
            9. Return only data matching the required structured schema.
            """
        ),
        (
            "human",
            """
            Classify the following customer ticket.

            Ticket:
            {ticket}
            """
        ),
    ])

    return prompt | llm.with_structured_output(
        TicketClassification
    )