import pytest


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_admin_route_security(client):
    """Verify that /enroll is protected by Admin Key."""
    # Attempt without header
    response = client.post("/api/v1/fsp/enroll", json={})
    assert response.status_code == 403


def test_user_route_security(client):
    """Verify that /transfer is protected by JWT."""
    response = client.post("/api/v1/payment/transfer", json={})
    assert response.status_code == 401
