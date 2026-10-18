import json
import uuid

from pathlib import Path

from schemas.ticket import TicketInput
from workflow import process_ticket, save_processed_ticket


def get_input(label, required=False):
    while True:
        value = input(f"{label}: ").strip()

        if value or not required:
            return value

        print("This field is required. Please try again.")


def collect_ticket():
    print("\n=== AI Customer Support Desk ===\n")

    customer_name = get_input("Customer name")
    customer_id = get_input("Customer ID")
    order_id = get_input("Order ID")
    channel = get_input(
        "Channel (email/chat/phone_transcript/web_form)"
    ).lower()

    allowed_channels = {
        "email",
        "chat",
        "phone_transcript",
        "web_form",
    }

    if channel not in allowed_channels:
        print("Invalid channel. Using web_form.")
        channel = "web_form"

    message = get_input(
        "\nEnter the customer's complaint",
        required=True,
    )

    return TicketInput(
        ticket_id=f"TKT-{uuid.uuid4().hex[:8].upper()}",
        customer_name=customer_name or None,
        customer_id=customer_id or None,
        order_id=order_id or None,
        channel=channel,
        message=message,
    )


def main():
    ticket = collect_ticket()

    print("\nProcessing ticket...")
    print("-" * 50)

    try:
        summary = process_ticket(ticket)

        print("\n=== Classification ===")
        print(summary.classification.model_dump_json(indent=2))

        print("\n=== Routing ===")
        print(summary.routing.model_dump_json(indent=2))

        print("\n=== Case Analysis ===")
        print(json.dumps(
            summary.case_analysis,
            indent=2,
            ensure_ascii=False,
            default=str,
        ))

        print("\n=== Resolution ===")
        print(summary.resolution.model_dump_json(indent=2))

        print("\n=== Customer Response ===")
        print(summary.response.model_dump_json(indent=2))

        print("\n=== Final Ticket Status ===")
        print(summary.ticket_status)

        save_processed_ticket(summary)

        print("\nTicket saved to data/processed_tickets.json")

    except Exception as exc:
        print(f"\nTicket processing failed: {exc}")
        print(
            "Check your LLM configuration, schema definitions, "
            "JSON files, and chain imports."
        )


if __name__ == "__main__":
    main()