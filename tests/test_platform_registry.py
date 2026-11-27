import pytest

from app.platform_registry import PlatformRegistry


def test_capability_catalogue_is_trackable_and_not_claimed_live(tmp_path):
    registry = PlatformRegistry(str(tmp_path / "platform.db"))
    items = registry.capabilities()
    assert len(items) == 12
    assert all(item["status"] in {"PLANNED", "PARTIAL", "IMPLEMENTED"} for item in items)


def test_contributor_requires_review_and_token_is_revocable(tmp_path):
    registry = PlatformRegistry(str(tmp_path / "platform.db"))
    pending = registry.enroll(
        "Community workstation",
        "ghostcorp-compute-v1",
        {"cpu_cores": 8, "ram_mb": 16384, "disk_mb": 50000, "gpu": True},
    )
    assert pending["status"] == "PENDING_REVIEW"
    assert registry.authenticate("not-a-token") is None

    approved = registry.approve(pending["node_id"])
    token = approved["node_token"]
    assert registry.authenticate(token)["node_id"] == pending["node_id"]

    heartbeat = registry.heartbeat(
        pending["node_id"], {"cpu_percent": 42, "ram_used_mb": 1024, "paused": False}
    )
    assert heartbeat["metrics"]["cpu_percent"] == 42.0

    registry.revoke(pending["node_id"])
    assert registry.authenticate(token) is None


def test_pending_and_duplicate_approval_are_rejected(tmp_path):
    registry = PlatformRegistry(str(tmp_path / "platform.db"))
    pending = registry.enroll("Contributor", "ghostcorp-compute-v1", {})
    with pytest.raises(LookupError):
        registry.approve("gcnode_missing")
    registry.approve(pending["node_id"])
    with pytest.raises(ValueError):
        registry.approve(pending["node_id"])


def test_resource_metrics_are_persisted_and_capacity_is_labelled(tmp_path):
    registry = PlatformRegistry(str(tmp_path / "platform.db"))
    pending = registry.enroll(
        "Compute donor",
        "ghostcorp-compute-v1",
        {"cpu_cores": 4, "ram_mb": 8192, "disk_mb": 20000, "gpu": False},
    )
    registry.approve(pending["node_id"])
    registry.heartbeat(
        pending["node_id"],
        {"cpu_percent": 25, "ram_used_mb": 2048, "paused": True},
    )
    node = registry.list_nodes()[0]
    assert node["metrics"]["cpu_percent"] == 25.0
    assert node["metrics"]["paused"] is True
    capacity = registry.capacity_snapshot()
    assert capacity["declared_cpu_cores"] == 4
    assert capacity["declared_ram_mb"] == 8192
    assert capacity["nodes_reporting"] == 1
    assert capacity["nodes_paused"] == 1
    assert "not independently verified" in capacity["note"]


def test_enrollment_rejects_invalid_display_name_and_gpu_type(tmp_path):
    registry = PlatformRegistry(str(tmp_path / "platform.db"))
    with pytest.raises(ValueError):
        registry.enroll("  ", "ghostcorp-compute-v1", {})
    with pytest.raises(ValueError):
        registry.enroll("Contributor", "ghostcorp-compute-v1", {"gpu": "yes"})
