import pytest

from app.agent_workspaces import AgentWorkspaceManager, WorkspacePolicyError


def test_workspace_allocation_is_per_agent_and_empty(tmp_path):
    manager = AgentWorkspaceManager(str(tmp_path / "db.sqlite"), str(tmp_path / "work"))
    one = manager.create("agent_one", 600)
    two = manager.create("agent_two", 600)
    assert one["workspace_id"] != two["workspace_id"]
    assert one["agent_id"] == "agent_one"
    assert (tmp_path / "work" / one["workspace_id"] / ".ghostcorp-workspace").is_file()
    assert one["execution_enabled"] is False
    assert len(manager.list("agent_one")) == 1


def test_workspace_allocation_is_disabled_without_root(tmp_path):
    manager = AgentWorkspaceManager(str(tmp_path / "db.sqlite"))
    with pytest.raises(WorkspacePolicyError):
        manager.create("agent_one")


@pytest.mark.parametrize("agent", ["../bad", "x", "has space"])
def test_invalid_agent_identity_rejected(tmp_path, agent):
    manager = AgentWorkspaceManager(str(tmp_path / "db.sqlite"), str(tmp_path / "work"))
    with pytest.raises(WorkspacePolicyError):
        manager.create(agent)


def test_release_and_expiry_cleanup(tmp_path):
    clock = [1000]
    manager = AgentWorkspaceManager(str(tmp_path / "db.sqlite"), str(tmp_path / "work"),
                                    clock=lambda: clock[0])
    first = manager.create("agent_one", 60)
    second = manager.create("agent_two", 600)
    clock[0] = 1061
    assert manager.cleanup_expired() == [{"workspace_id": first["workspace_id"], "status": "RELEASED"}]
    active = next(item for item in manager.list() if item["agent_id"] == "agent_two")
    assert active["status"] == "ACTIVE"
    assert not (tmp_path / "work" / first["workspace_id"]).exists()
    manager.release(second["workspace_id"])
    assert manager.list()[0]["status"] == "RELEASED"


def test_release_refuses_missing_or_changed_marker(tmp_path):
    manager = AgentWorkspaceManager(str(tmp_path / "db.sqlite"), str(tmp_path / "work"))
    item = manager.create("agent_one")
    marker = tmp_path / "work" / item["workspace_id"] / ".ghostcorp-workspace"
    marker.write_text("tampered")
    with pytest.raises(WorkspacePolicyError):
        manager.release(item["workspace_id"])
