from fastapi.testclient import TestClient

from app import main


def test_action_center_is_owner_protected(monkeypatch):
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "action-center-secret")
    client = TestClient(main.app)
    assert client.get("/api/owner/action-center").status_code == 403
    response = client.get(
        "/api/owner/action-center",
        headers={"X-Federation-Admin": "action-center-secret"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "OWNER_PRIVATE_ACTION_CENTER"
    assert "customer_problems" in payload
    assert "product_drafts" in payload
    assert "dream_artifacts" in payload
    assert payload["capability_status"]["live_workers"] is False
