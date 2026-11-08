from pydantic import BaseModel
from typing import Dict, Any


class RafikiWebhookEvent(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]
