from fastapi.testclient import TestClient

from app import main
from app.gumroad import GumroadSales
from app.service_workflow import WebsiteServiceWorkflow


def test_website_audit_to_customer_approved_paid_delivery_api(monkeypatch):
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "service-owner-secret")
    monkeypatch.setenv("PUBLIC_FEEDBACK_RATE_SECRET", "service-rate-" + "t" * 40)
    monkeypatch.setenv("GUMROAD_SERVICE_PACKAGE_MAP", "AI Website=ihqce")
    monkeypatch.setattr(main, "service_workflow", WebsiteServiceWorkflow(":memory:"))
    ledger = GumroadSales(":memory:")
    ledger.conn.execute(
        """INSERT INTO gumroad_verified_sales
           (sale_id,product_permalink,status,amount_raw,currency,provider_created_at,verified_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        ("service-sale-1", "ihqce", "PAID_VERIFIED", "49900", "USD",
         "2026-11-27T12:00:00Z", 1, 1),
    )
    ledger.conn.commit()
    monkeypatch.setattr(main, "gumroad_sales", ledger)
    monkeypatch.setattr(main, "audit_website", lambda url: {
        "url": url, "findings": ["Missing page title"],
        "evidence": {"http_status": 200, "response_ms": 120},
    })

    client = TestClient(main.app)
    request = client.post("/api/public/website-audit-requests", json={
        "business_name": "Local Shop", "website_url": "https://shop.example",
        "contact_email": "owner@shop.example", "package": "AI Website",
        "contact_permission": True,
    })
    assert request.status_code == 200
    request_id = request.json()["request_id"]
    headers = {"X-Federation-Admin": "service-owner-secret"}

    audit = client.post(f"/api/service/requests/{request_id}/audit", headers=headers)
    assert audit.status_code == 200
    proposal = client.post(f"/api/service/requests/{request_id}/proposal", headers=headers)
    assert proposal.status_code == 200
    approval = client.post(f"/api/service/requests/{request_id}/approval-link", headers=headers)
    assert approval.status_code == 200
    token = approval.json()["token"]

    preview = client.post("/api/public/service-approval-preview", json={"token": token})
    assert preview.status_code == 200
    decision = client.post("/api/public/service-approvals",
                           json={"token": token, "decision": "ACCEPTED"})
    assert decision.status_code == 200

    delivery = client.post(f"/api/service/requests/{request_id}/delivery",
                           headers=headers,
                           json={"status": "IN_PROGRESS", "payment_sale_id": "service-sale-1"})
    assert delivery.status_code == 200
    assert delivery.json()["status"] == "IN_PROGRESS"

    completed = client.post(f"/api/service/requests/{request_id}/delivery",
                            headers=headers,
                            json={"status": "DELIVERED", "payment_sale_id": "service-sale-1",
                                  "notes": "Website delivered and tested with the customer.",
                                  "deliverable_url": "https://deliverables.example/local-shop"})
    assert completed.status_code == 200
    assert completed.json()["status"] == "DELIVERED"
