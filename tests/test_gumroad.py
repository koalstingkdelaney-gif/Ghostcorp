import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.gumroad import GumroadError, GumroadSales


def sale_transport(refunded=False, permalink="ihqce"):
    def handler(request):
        assert request.url.host == "api.gumroad.com"
        assert request.url.path == "/v2/sales/sale-123"
        assert request.url.params.get("access_token") == "gumroad-test-token"
        return httpx.Response(200, json={
            "success": True,
            "sale": {
                "id": "sale-123",
                "product_permalink": permalink,
                "refunded": refunded,
                "price": "900",
                "currency": "usd",
                "created_at": "2026-11-27T12:00:00Z",
            },
        })
    return httpx.MockTransport(handler)


def configure_gumroad(monkeypatch):
    monkeypatch.setenv("GUMROAD_ACCESS_TOKEN", "gumroad-test-token")
    monkeypatch.setenv("GUMROAD_PING_SECRET", "ping-secret-" + "s" * 40)
    monkeypatch.setenv("GUMROAD_ALLOWED_PERMALINKS", "ihqce,lttjbc")


def test_gumroad_sale_is_verified_and_idempotently_recorded(monkeypatch):
    configure_gumroad(monkeypatch)
    ledger = GumroadSales(":memory:", transport=sale_transport())
    first = ledger.verify_and_record({"resource_name": "sale", "sale_id": "sale-123"})
    second = ledger.verify_and_record({"resource_name": "sale", "sale_id": "sale-123"})
    assert first["status"] == "PAID_VERIFIED"
    assert first["amount_units"] == "GUMROAD_API_RAW_UNCONVERTED"
    assert second["sale_id"] == first["sale_id"]
    assert len(ledger.list()) == 1


def test_gumroad_refund_only_records_after_provider_confirms(monkeypatch):
    configure_gumroad(monkeypatch)
    ledger = GumroadSales(":memory:", transport=sale_transport(refunded=True))
    result = ledger.verify_and_record({"resource_name": "refund", "sale_id": "sale-123"})
    assert result["status"] == "REFUNDED"


def test_gumroad_rejects_unapproved_product_permalink(monkeypatch):
    configure_gumroad(monkeypatch)
    ledger = GumroadSales(":memory:", transport=sale_transport(permalink="not-ours"))
    with pytest.raises(GumroadError, match="allowlist"):
        ledger.verify_and_record({"resource_name": "sale", "sale_id": "sale-123"})


def test_gumroad_ignores_unsupported_ping_resources(monkeypatch):
    configure_gumroad(monkeypatch)
    ledger = GumroadSales(":memory:", transport=sale_transport())
    result = ledger.verify_and_record({"resource_name": "dispute", "sale_id": "sale-123"})
    assert result["outcome"] == "ignored_unsupported_event"
    assert ledger.list() == []


def test_gumroad_webhook_requires_secret_and_api_verification(monkeypatch):
    configure_gumroad(monkeypatch)
    ledger = GumroadSales(":memory:", transport=sale_transport())
    monkeypatch.setattr(main, "gumroad_sales", ledger)
    secret = "ping-secret-" + "s" * 40
    client = TestClient(main.app)
    assert client.post("/webhooks/gumroad/wrong", data={"sale_id": "sale-123"}).status_code == 404
    response = client.post(
        "/webhooks/gumroad/" + secret,
        data={"resource_name": "sale", "sale_id": "sale-123"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "PAID_VERIFIED"
