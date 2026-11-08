"""
This file is responsible for sending the events to the database
"""

import requests
from app.core.logger import logger
from app.core.config import settings


def store_event(event: dict):
    url = f"{settings.DB_SERVICE_URL}/webhook/"

    headers = {
        "X-API-Key": settings.DATABASE_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url, json=event, headers=headers, timeout=5  
        )

        if response.status_code in [401, 403]:
            logger.error("❌ Database Access Denied: Webhook API Key is invalid")
            return {"created": False, "error": "Unauthorized"}

        response.raise_for_status()

        logger.info(f"Event stored in DB service: {event['id']}")

        try:
            return response.json()
        except Exception:
            return {"created": True}

    except Exception as e:
        logger.error(f"Failed to store event: {str(e)}")
        return None
