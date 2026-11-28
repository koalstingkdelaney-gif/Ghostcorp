from app.agent_world import AgentWorld
from app.federation import FederationRegistry


def setup(tmp_path):
    db = str(tmp_path / "ghostcorp-world.db")
    registry = FederationRegistry(db)
    registry.create_division("research-lab", "Research Lab", "Research")
    research = registry.create_agent("research-lab", "researcher")
    registry.create_division("build-lab", "Build Lab", "Build")
    builder = registry.create_agent("build-lab", "builder")
    world = AgentWorld(db)
    world.sync_registry(registry)
    world.heartbeat(research["machine_id"], "research-lab", "research")
    world.heartbeat(builder["machine_id"], "build-lab", "building")
    return world, research, builder


def test_learning_adaptation_is_persisted_in_agents_own_zone(tmp_path):
    world, research, _ = setup(tmp_path)
    result = world.record_learning(
        research["machine_id"], "research-note-001", "knowledge-cluster",
        "New market evidence", "Connected three verified sources.",
        {"accent": "#65eaff", "intensity": 0.7, "labels": ["market", "evidence"]})
    assert result["outcome"] == "created"
    assert result["adaptation"]["zone"] == "research-lab"
    assert world.adaptations(zone="research-lab")[0]["title"] == "New market evidence"
    assert world.adaptations(zone="build-lab") == []


def test_learning_event_is_idempotent(tmp_path):
    world, research, _ = setup(tmp_path)
    args = (research["machine_id"], "stable-event-001", "display-panel",
            "Research findings", "New evidence summary", {})
    assert world.record_learning(*args)["outcome"] == "created"
    assert world.record_learning(*args)["outcome"] == "duplicate"
    assert len(world.adaptations()) == 1


def test_learning_rejects_unsupported_visual_config(tmp_path):
    world, research, _ = setup(tmp_path)
    try:
        world.record_learning(research["machine_id"], "bad-config-001",
                              "workspace-layout", "Unsafe", "Should be rejected",
                              {"script": "alert(1)"})
    except ValueError as exc:
        assert "unsupported properties" in str(exc)
    else:
        raise AssertionError("arbitrary script config must be rejected")


def test_learning_rejects_out_of_range_visual_values(tmp_path):
    world, research, _ = setup(tmp_path)
    try:
        world.record_learning(research["machine_id"], "bad-scale-001",
                              "workstation-upgrade", "Too large", "Out of range",
                              {"scale": 99})
    except ValueError as exc:
        assert "outside its allowed range" in str(exc)
    else:
        raise AssertionError("unbounded visual changes must be rejected")


def test_unknown_machine_cannot_change_world(tmp_path):
    world, _, _ = setup(tmp_path)
    try:
        world.record_learning("unknown-agent", "unknown-event-001",
                              "ambient-state", "Unknown", "No identity", {})
    except LookupError as exc:
        assert "no world identity" in str(exc)
    else:
        raise AssertionError("unknown machine identity must be rejected")
