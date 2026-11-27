from app.agent_world import AgentWorld
from app.federation import FederationRegistry


def setup(tmp_path):
    db = str(tmp_path / "ghostcorp-world.db")
    registry = FederationRegistry(db)
    registry.create_division("research-lab", "Research Lab", "Research")
    created = registry.create_agent("research-lab", "researcher")
    world = AgentWorld(db)
    return registry, world, created


def test_world_creates_one_identity_per_registered_agent(tmp_path):
    registry, world, agent = setup(tmp_path)
    assert world.sync_registry(registry) == 1
    snapshot = world.snapshot()
    assert snapshot["counts"]["total"] == 1
    entry = snapshot["agents"][0]
    assert entry["machine_id"] == agent["machine_id"]
    assert entry["division"] == "research-lab"
    assert entry["presence"] == "SIMULATED"


def test_agent_heartbeat_marks_authenticated_machine_live(tmp_path):
    registry, world, agent = setup(tmp_path)
    world.sync_registry(registry)
    result = world.heartbeat(agent["machine_id"], "research-lab")
    assert result["presence"] == "LIVE"
    snapshot = world.snapshot()
    assert snapshot["counts"]["live"] == 1
    assert snapshot["agents"][0]["presence"] == "LIVE"


def test_unknown_zone_is_rejected(tmp_path):
    registry, world, agent = setup(tmp_path)
    world.sync_registry(registry)
    try:
        world.heartbeat(agent["machine_id"], "private-treasury")
    except ValueError as exc:
        assert "unknown world zone" in str(exc)
    else:
        raise AssertionError("unknown zone should be rejected")


def test_daily_routine_has_defined_role_and_hour():
    result = AgentWorld.routine_for("researcher", 9)
    assert result["activity"] == "research"
    assert result["zone"] == "research-lab"


def test_event_history_is_bounded_by_requested_limit(tmp_path):
    registry, world, agent = setup(tmp_path)
    world.sync_registry(registry)
    world.heartbeat(agent["machine_id"], "research-lab")
    world.heartbeat(agent["machine_id"], "research-library")
    assert len(world.recent_events(1)) == 1


def test_agents_have_business_missions_and_free_first_world_policy(tmp_path):
    registry, world, agent = setup(tmp_path)
    world.sync_registry(registry)
    snapshot = world.snapshot()
    assert "net revenue" in snapshot["agents"][0]["long_term_mission"]
    assert snapshot["world_policy"]["default_paid_spend_usd"] == 0
    assert snapshot["world_policy"]["owner_override"] is True
    assert snapshot["world_policy"]["agent_work_environment"] == "private GhostCorp sandbox"
