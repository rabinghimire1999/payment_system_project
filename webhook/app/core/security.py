import hmac
import hashlib
import json
import time
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def canonicalize(body: bytes) -> bytes:
    parsed = json.loads(body)
    return json.dumps(parsed, separators=(",", ":"), sort_keys=True).encode()

def verify_rafiki_signature(body: bytes, signature_header: str) -> bool:
    try:
        if settings.SIGNATURE_SECRET == "dev-secret":
            return True

        parts = dict(item.split("=", 1) for item in signature_header.split(", "))

        timestamp = parts["t"]
        signature_digest = parts["v1"]

        #Timestamp validation
        # current_time = int(time.time())
        # if abs(current_time - int(timestamp)) > 300:  # 5 minute window 
        #     raise ValueError("Webhook timestamp too old - possible replay attack")
        
        
        # Canonicalize body (sorted keys, no spaces)
        canonical_body = canonicalize(body)

        # Build payload
        signed_payload = f"{timestamp}.".encode() + canonical_body

        # Secret as raw UTF-8 string (NOT base64 decoded)
        expected = hmac.new(
            settings.SIGNATURE_SECRET.encode("utf-8"),
            signed_payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature_digest)

    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False