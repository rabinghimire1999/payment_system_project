import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Later remove dev-secret
    SIGNATURE_SECRET = os.getenv("SIGNATURE_SECRET")

    # Later remove database_url
    DB_SERVICE_URL = os.getenv("DB_SERVICE_URL")
    DATABASE_API_KEY = os.getenv("DATABASE_API_KEY")

    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    MIDDLEWARE_SERVICE_URL = os.getenv("MIDDLEWARE_SERVICE_URL")
    INTERNAL_WEBHOOK_TOKEN = os.getenv("INTERNAL_WEBHOOK_TOKEN")

settings = Settings()
