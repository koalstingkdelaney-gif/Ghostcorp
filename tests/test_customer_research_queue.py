import json

from fastapi.testclient import TestClient

from app import main
from app.agent_runtime import AgentRuntime
from app.customer_feedback import CustomerFeedback
from app.federation import FederationRegistry


def test_reviewed_customer_problem_can_be_queued_without_contact_data(monkeypatch):
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "owner-secret")
    feedback = CustomerFeedback(":memory:")
    fingerprint = feedback.fingerprint("203.0.113.30", "rate-secret-" + "a" * 40)
    item = feedback.submit(
        "Independent creators struggle to validate which products customers need.",
        "I want a simpler way to interview potential buyers.",
        "private-contact@example.com", True, fingerprint,
    )
    feedback.update_status(item["id"], "ROADMAP")

    registry = FederationRegistry(":memory:")
    registry.create_division("research-lab", "Research Lab", "Customer problem validation")
    runtime = AgentRuntime(":memory:")
    monkeypatch.setattr(main, "customer_feedback", feedback)
    monkeypatch.setattr(main, "federation", registry)
    monkeypatch.setattr(main, "agent_runtime", runtime)

    client = TestClient(main.app)
    response = client.post(
        f"/api/customer/problem-submissions/{item['id']}/research",
        json={"division_slug": "research-lab"},
        headers={"X-Federation-Admin": "owner-secret"},
    )
    assert response.status_code == 200
    assert response.json()["outcome"] == "queued"
    assert response.json()["contact_data_shared"] is False

    row = runtime.conn.execute("SELECT payload FROM agent_tasks").fetchone()
    task_payload = json.loads(row["payload"])
    assert "private-contact@example.com" not in json.dumps(task_payload)
    assert task_payload["privacy_class"] == "internal"
    assert task_payload["tools_enabled"] is False


def test_customer_problem_research_requires_review_and_existing_division(monkeypatch):
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "owner-secret")
    feedback = CustomerFeedback(":memory:")
    fingerprint = feedback.fingerprint("203.0.113.31", "rate-secret-" + "b" * 40)
    item = feedback.submit(
        "Independent creators struggle to validate which products customers need.",
        "", "", False, fingerprint,
    )
    registry = FederationRegistry(":memory:")
    registry.create_division("research-lab", "Research Lab", "")
    monkeypatch.setattr(main, "customer_feedback", feedback)
    monkeypatch.setattr(main, "federation", registry)
    monkeypatch.setattr(main, "agent_runtime", AgentRuntime(":memory:"))

    client = TestClient(main.app)
    response = client.post(
        f"/api/customer/problem-submissions/{item['id']}/research",
        json={"division_slug": "research-lab"},
        headers={"X-Federation-Admin": "owner-secret"},
    )
    assert response.status_code == 409
