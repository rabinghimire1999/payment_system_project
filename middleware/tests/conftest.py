import pytest
import os

# Set dummy environment variables for testing
os.environ["ADMIN_API_SECRET"] = "test_secret_key"
os.environ["MIDDLEWARE_ADMIN_KEY"] = "test_admin_key"
os.environ["DATABASE_SERVICE_URL"] = "http://localhost:8000/v1"
os.environ["RAFIKI_ADMIN_URL"] = "http://localhost:3001/graphql"
os.environ["RAFIKI_WALLET_BASE_URL"] = "https://test.com"
os.environ["OPERATOR_HMAC_SECRET"] = "test_secret_key"
os.environ["OPERATOR_TENANT_ID"] = "test_tenant_id"
os.environ["DATABASE_API_KEY"] = "test_database_api_key"

from fastapi.testclient import TestClient
from transformer.api.main import app

@pytest.fixture
def client():
    """Provides a virtual client to hit our API routes."""
    with TestClient(app) as c:
        yield c