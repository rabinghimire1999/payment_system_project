# Inside your existing FastAPI route (e.g., in backend/api/webhooks.py)

from middleware.backend.services.payments.webhook_handler import RafikiWebhookHandler

# Instantiate the handler once or use dependency injection
event_handler = RafikiWebhookHandler()

@router.post("/rafiki")
async def your_validated_webhook_route(request: Request):
    # Your existing middleware has already run here (verifying signature, etc.)
    payload = await request.json()
    
    # Extract the event envelope parameters
    event_type = payload.get("type")  # e.g., "incoming_payment.completed"
    event_data = payload.get("data")  # The actual incoming payment object
    
    # Dispatch directly to the handler logic
    await event_handler.process_event(event_type, event_data)
    
    return {"status": "success"}

