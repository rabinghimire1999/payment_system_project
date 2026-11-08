from app.core.redis import redis_client

QUEUE_NAME = "rafiki_events"

def push_event(event_id: str):
    redis_client.lpush(QUEUE_NAME, event_id)

def pop_event():
    return redis_client.rpop(QUEUE_NAME)