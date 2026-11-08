from fastapi import APIRouter, Request, Header, HTTPException
import httpx
from app.core.logger import logger
from app.api.webhook.schema.rafiki_event import RafikiWebhookEvent
from app.core.security import verify_rafiki_signature
from app.service.event_client import store_event
from app.service.queue_service import push_event
from app.core.config import settings
import json

router = APIRouter()


# Receives the event from rafiki
@router.post("/rafiki")
async def receive_rafiki_event(request: Request, rafiki_signature: str = Header(None)):

    # Raw body send from rafiki for signature check
    raw_body = await request.body()

    # Verify signature HMAC
    if not rafiki_signature or not verify_rafiki_signature(raw_body, rafiki_signature):
        logger.warning("Invalid Rafiki Signature")
        raise HTTPException(status_code=401, detail="Invalid Signature")

    try:
        body_dict = json.loads(raw_body)
        logger.info(f"Received Rafiki event: {body_dict}")
        event_type = body_dict.get("type", "unknown")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info(f"Rafiki event_type={event_type}")

    # Now convert to pydantic for validation
    payload = RafikiWebhookEvent(**body_dict)

    # Later implement redis duplication check also

    # Store event (idempotency)
    result = store_event(body_dict)

    # #Duplication detection and no double processing same event
    if not result or result.get("created") is False:
        logger.info(f"Webhook Payload: {payload}")
        logger.info(f"Duplicate event ignored: {payload.id}")
        return {"status": 200, "event_id": payload.id, "duplicate": True}

    # Push to redis queue
    try:
        push_event(payload.id)
        print(payload.id)
    except Exception as e:
        logger.error(f"Failed to queue event {payload.id}: {e}")

    async with httpx.AsyncClient() as client:
        try:
            target_url = (
                f"{settings.MIDDLEWARE_SERVICE_URL.rstrip('/')}/internal/process-event"
            )
            await client.post(
                target_url,
                json=body_dict,
                headers={"x-internal-token": settings.INTERNAL_WEBHOOK_TOKEN},
            )
            logger.info(f"Successfully relayed event to Middleware at {target_url}")
        except Exception as e:
            logger.error(f"Failed to relay event to {target_url}: {e}")

    logger.info(f"Received Rafiki event: " f"id={payload.id}," f"type={payload.type}")

    return {"status": "ok", "event_id": payload.id, "event_type": payload.type}
