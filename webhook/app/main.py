from fastapi import FastAPI
from app.api.webhook.routes.rafiki import router as rafiki_webhook_router

# from app.core.config import settings

app = FastAPI(
    title="Rafiki Webhook Service",
    description="Handles Rafiki webhook events and processes payment flows",
    version="1.0.0",
)

app.include_router(rafiki_webhook_router, prefix="/webhook", tags=["Rafiki Webhooks"])


@app.get("/")
def root():
    return {"status": "ok", "service": "rafiki-webhook", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
    )
