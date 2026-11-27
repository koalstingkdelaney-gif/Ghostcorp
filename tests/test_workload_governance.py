import pytest

from app.workload_governance import (
    QuotaLedger, WorkloadAuthority, WorkloadPolicyError, validate_artifact_name,
)


def test_signed_manifest_is_bound_to_agent_and_revision():
    clock = [1000]
    authority = WorkloadAuthority("k" * 40, clock=lambda: clock[0])
    manifest = authority.issue("public-build-test", "agent_123", "a" * 40)
    assert authority.verify(manifest)
    changed = dict(manifest, agent_id="agent_other")
    assert not authority.verify(changed)
    clock[0] = manifest["expires_at"] + 1
    assert not authority.verify(manifest)


def test_manifest_rejects_unknown_workload_and_mutable_revision():
    authority = WorkloadAuthority("k" * 40)
    with pytest.raises(WorkloadPolicyError):
        authority.issue("arbitrary-shell", "agent_123", "a" * 40)
    with pytest.raises(WorkloadPolicyError):
        authority.issue("public-build-test", "agent_123", "main")


def test_quota_reservations_are_idempotent_and_bounded(tmp_path):
    ledger = QuotaLedger(str(tmp_path / "quota.db"))
    first = ledger.reserve("agent_123", "task:001", 300)
    second = ledger.reserve("agent_123", "task:001", 300)
    assert first["reservation_id"] == second["reservation_id"]
    with pytest.raises(WorkloadPolicyError):
        ledger.reserve("agent_123", "task:002", 60)
    settled = ledger.settle(first["reservation_id"], 240)
    assert settled["actual_seconds"] == 240
    assert ledger.status("agent_123")["events"][0]["count"] == 1


def test_quota_enforces_daily_budget_and_settlement_bounds(tmp_path):
    ledger = QuotaLedger(str(tmp_path / "quota.db"))
    for i in range(3):
        item = ledger.reserve("agent_123", f"task:{i:03}", 600)
        ledger.settle(item["reservation_id"], 600)
    with pytest.raises(WorkloadPolicyError):
        ledger.reserve("agent_123", "task:004", 1)


@pytest.mark.parametrize("name", ["../secret", "/etc/passwd", ".env", "a/../b", "a\\b"])
def test_artifact_path_traversal_is_rejected(name):
    with pytest.raises(WorkloadPolicyError):
        validate_artifact_name(name)


def test_artifact_relative_path_is_accepted():
    assert validate_artifact_name("reports/test-results.json") == "reports/test-results.json"
