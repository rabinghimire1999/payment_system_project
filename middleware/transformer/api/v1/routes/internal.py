from fastapi import APIRouter, Request, Header, HTTPException
import logging
from backend.services.events.event_handler import event_handler

router = APIRouter()
logger = logging.getLogger(__name__)

# This secret should be in your .env
INTERNAL_WEBHOOK_TOKEN = "your-shared-secret-between-webhook-and-middleware"


@router.post("/internal/process-event")
async def process_rafiki_event(request: Request, x_internal_token: str = Header(None)):
    # Security check: Only our own Webhook service can call this
    if x_internal_token != INTERNAL_WEBHOOK_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized internal call")

    event_data = await request.json()

    # Send the event to the Brain to handle the logic
    await event_handler.handle(event_data)

    return {"status": "processed"}
