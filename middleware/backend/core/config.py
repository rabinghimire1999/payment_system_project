import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- SERVICE URLS ---
    DATABASE_SERVICE_URL: str
    RAFIKI_ADMIN_URL: str
    RAFIKI_WALLET_BASE_URL: str

    # --- SECURITY ---
    ADMIN_API_SECRET: str
    OPERATOR_HMAC_SECRET: str
    OPERATOR_TENANT_ID: str
    DATABASE_API_KEY: str
    MIDDLEWARE_ADMIN_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
