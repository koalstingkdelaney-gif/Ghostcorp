import pytest
from fastapi.testclient import TestClient

from app import main
from app.customer_feedback import CustomerFeedback, FeedbackError


def test_feedback_requires_contact_consent_and_keeps_ip_only_as_fingerprint():
    store = CustomerFeedback(":memory:")
    fp = store.fingerprint("203.0.113.10", "x" * 40)
    result = store.submit("Small shops need an easier way to manage returns.",
                          "A simple workflow would help.", "person@example.com",
                          False, fp)
    row = store.list("NEW")[0]
    assert result["status"] == "RECEIVED"
    assert row["email"] == ""
    assert row["contact_permission"] == 0
    assert "203.0.113.10" not in str(row)


def test_feedback_requires_email_when_reply_is_requested():
    store = CustomerFeedback(":memory:")
    fp = store.fingerprint("203.0.113.11", "x" * 40)
    with pytest.raises(FeedbackError):
        store.submit("Small shops need an easier way to manage returns.",
                     "", "", True, fp)


def test_feedback_rate_limit_is_enforced():
    store = CustomerFeedback(":memory:")
    fp = store.fingerprint("203.0.113.12", "x" * 40)
    for _ in range(3):
        store.submit("Small shops need an easier way to manage returns.",
                     "", "", False, fp)
    with pytest.raises(FeedbackError, match="limit"):
        store.submit("Small shops need an easier way to manage returns.",
                     "", "", False, fp)


def test_feedback_review_states_are_owner_operated():
    store = CustomerFeedback(":memory:")
    fp = store.fingerprint("203.0.113.13", "x" * 40)
    item = store.submit("Small shops need an easier way to manage returns.",
                        "", "", False, fp)
    reviewed = store.update_status(item["id"], "ROADMAP")
    assert reviewed["status"] == "ROADMAP"
    assert store.list("ROADMAP")[0]["id"] == item["id"]


def test_public_problem_submission_endpoint(monkeypatch):
    monkeypatch.setenv("PUBLIC_FEEDBACK_RATE_SECRET", "test-secret-" + "z" * 40)
    monkeypatch.setattr(main, "customer_feedback", CustomerFeedback(":memory:"))
    client = TestClient(main.app)
    response = client.post("/api/public/problem-submissions", json={
        "problem": "Independent creators struggle to validate which products customers need.",
        "context": "I spend too much time guessing.",
        "email": "person@example.com",
        "contact_permission": False,
    })
    assert response.status_code == 200
    assert response.json()["accepted"] is True
    stored = main.customer_feedback.list("NEW")
    assert len(stored) == 1
    assert stored[0]["email"] == ""


def test_public_problem_submission_requires_rate_limit_secret(monkeypatch):
    monkeypatch.delenv("PUBLIC_FEEDBACK_RATE_SECRET", raising=False)
    client = TestClient(main.app)
    response = client.post("/api/public/problem-submissions", json={
        "problem": "Independent creators struggle to validate which products customers need."
    })
    assert response.status_code == 503
