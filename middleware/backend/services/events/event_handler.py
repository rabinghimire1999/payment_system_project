import logging
from backend.services.events.payment_handler import (
    handle_outgoing_created,
    handle_outgoing_completed,
    handle_incoming_completed,
    handle_outgoing_failed,
)

logger = logging.getLogger(__name__)


class RafikiEventHandler:
    async def handle(self, event: dict):
        event_type = event.get("type")
        data = event.get("data", {})

        logger.info(f" Event Handler: Dispatching {event_type}")

        # 1. Payment created but needs money (JIT Fueling)
        if event_type == "outgoing_payment.created":
            await handle_outgoing_created(data, event.get("tenantId"))

        # 2. Payment finished (Finalize DB)
        elif event_type == "outgoing_payment.completed":
            await handle_outgoing_completed(data)

        # --- NEW: Handle Failures ---
        elif event_type == "outgoing_payment.failed":
            await handle_outgoing_failed(
                data
            )  # We will define this in payment_handlers.py

        # 3. Money arrived at destination (Release to Receiver)
        elif event_type == "incoming_payment.completed":
            await handle_incoming_completed(data, event.get("tenantId"))

        else:
            logger.info(f"Ignoring event type: {event_type}")


event_handler = RafikiEventHandler()
