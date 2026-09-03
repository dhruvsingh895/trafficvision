"""Tests for the health endpoint."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_settings_defaults() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    assert settings.app_name == "TrafficVision"
    assert ".mp4" in settings.allowed_extensions_set
