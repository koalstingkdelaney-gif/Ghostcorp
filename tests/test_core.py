import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["AGENCY_DB_PATH"] = ":memory:"

import pytest

from app.audit_site import UnsafeURL, validate_public_url
from app.comms import CommsDisabled, DisabledCommsProvider
from app.governor import SpendCapExceeded, SpendGovernor
from app.proposals import PACKAGES, build_proposal
from app.scoring import score_lead
from app.store import Store


def test_governor_zero_cap_blocks_any_spend():
    g = SpendGovernor(0)
    with pytest.raises(SpendCapExceeded):
        g.record(0.01, "anything")
    g.record(0, "free tier")  # $0 is always allowed


def test_governor_cap_enforced():
    g = SpendGovernor(10)
    g.record(7, "a")
    with pytest.raises(SpendCapExceeded):
        g.record(4, "b")


def test_scoring_is_transparent():
    score, reasons = score_lead({"service": "AI Website", "email": "a@b.co",
                                 "source_url": "https://b.co", "city": "Elkhart",
                                 "vertical": "roofing"})
    assert score >= 80 and reasons and all(isinstance(r, str) for r in reasons)


def test_store_dedup_and_suppression():
    s = Store(":memory:")
    lead = {"name": "A", "email": "A@Example.com"}
    assert s.add_lead(lead) == "added"
    assert s.add_lead(lead) == "duplicate"  # one email = one lead, ever
    s.suppress("gone@example.com", "opt-out")
    assert s.add_lead({"name": "G", "email": "gone@example.com"}) == "suppressed"


def test_jobs_idempotent():
    s = Store(":memory:")
    assert s.enqueue("audit_lead", "k1", {"lead_id": 1}) == "queued"
    assert s.enqueue("audit_lead", "k1", {"lead_id": 1}) == "duplicate"


def test_ssrf_private_addresses_refused():
    for url in ("http://127.0.0.1/admin", "http://localhost/x",
                "http://169.254.169.254/latest/meta-data/", "file:///etc/passwd",
                "ftp://example.com/x"):
        with pytest.raises(UnsafeURL):
            validate_public_url(url)


def test_proposals_use_existing_rate_card_only():
    prop = build_proposal({"name": "Acme Roofing", "service": "AI Website"})
    assert prop["total_upfront_usd"] == PACKAGES["AI Website"]["upfront_usd"] == 499
    prop2 = build_proposal({"name": "Spa", "service": "AI Front Desk"})
    assert (prop2["total_upfront_usd"], prop2["monthly_usd"]) == (299, 149)
    assert "guarantee" not in prop["body"].lower()


def test_comms_disabled_by_default():
    c = DisabledCommsProvider()
    with pytest.raises(CommsDisabled):
        c.place_call("+15551234567", "script-1", {"consent": True})
    with pytest.raises(CommsDisabled):
        c.send_sms("+15551234567", "hi", {"consent": True})


def test_comms_refuses_without_consent_even_if_enabled():
    c = DisabledCommsProvider(calling_enabled=True, sms_enabled=True)
    with pytest.raises(CommsDisabled):
        c.place_call("+15551234567", "script-1", None)


def test_api_health_and_comms_endpoints():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    assert client.get("/health").json()["ok"] is True
    assert client.get("/api/packages").json()["AI Website"]["upfront_usd"] == 499
    assert client.post("/api/comms/call").status_code == 403
    r = client.post("/api/leads", json={"name": "Test Co", "email": "t@example.com",
                                        "service": "AI Website"})
    assert r.json()["outcome"] in ("added", "duplicate")
