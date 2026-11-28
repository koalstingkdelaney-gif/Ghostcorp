from fastapi.testclient import TestClient

from app import main


def test_private_lead_data_is_locked_when_owner_secret_missing(monkeypatch):
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "")
    client = TestClient(main.app)

    # Public health checks remain available, but private prospect records fail closed.
    assert client.get("/health").status_code == 200
    response = client.get("/api/leads")
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_private_lead_data_rejects_missing_or_wrong_owner_secret(monkeypatch):
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "test-owner-secret")
    client = TestClient(main.app)

    assert client.get("/api/leads").status_code == 403
    assert client.get(
        "/api/leads", headers={"X-Federation-Admin": "wrong-secret"}
    ).status_code == 403


def test_owner_secret_unlocks_private_lead_read(monkeypatch):
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "test-owner-secret")
    client = TestClient(main.app)

    response = client.get(
        "/api/leads", headers={"X-Federation-Admin": "test-owner-secret"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
