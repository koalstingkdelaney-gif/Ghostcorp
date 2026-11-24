import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app.main import app, settings

client = TestClient(app)


def test_health_remains_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_sensitive_read_fails_closed_without_owner_key(monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "")
    response = client.get("/api/leads")
    assert response.status_code == 503


def test_sensitive_read_rejects_missing_or_wrong_owner_key(monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "test-owner-secret")
    assert client.get("/api/leads").status_code == 401
    assert client.get(
        "/api/leads", headers={"X-GhostCorp-Admin-Key": "wrong"}
    ).status_code == 401


def test_sensitive_read_accepts_owner_key(monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "test-owner-secret")
    response = client.get(
        "/api/leads", headers={"X-GhostCorp-Admin-Key": "test-owner-secret"}
    )
    assert response.status_code == 200
