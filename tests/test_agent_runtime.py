import pytest

from app.federation import FederationRegistry
from app.agent_runtime import AgentRuntime


def setup(tmp_path, **kwargs):
    db = str(tmp_path / "ghostcorp.db")
    registry = FederationRegistry(db)
    registry.create_division("research-lab", "Research Lab", "")
    registry.create_division("build-lab", "Build Lab", "")
    agent = registry.create_agent("research-lab", "researcher")
    runtime = AgentRuntime(db, **kwargs)
    return runtime, agent["agent_token"]


def test_machine_agent_claims_and_completes_own_division_task(tmp_path):
    runtime, token = setup(tmp_path)
    agent = runtime.authenticate(token)
    assert agent["division_slug"] == "research-lab"
    assert runtime.enqueue("task-001", "research-lab", "researcher",
                           "research", {"topic": "open standards"}) == "queued"
    task = runtime.claim(agent)
    assert task["task_key"] == "task-001"
    assert task["attempt"] == 1
    assert runtime.complete(agent, task["task_id"], task["lease_token"],
                            {"summary": "draft ready"}) is True
    assert runtime.claim(agent) is None
    assert runtime.status()["counts"]["completed"] == 1


def test_agent_cannot_claim_another_divisions_task(tmp_path):
    runtime, token = setup(tmp_path)
    agent = runtime.authenticate(token)
    runtime.enqueue("task-002", "build-lab", "researcher",
                    "research", {"topic": "isolation"})
    assert runtime.claim(agent) is None


def test_task_keys_are_idempotent(tmp_path):
    runtime, token = setup(tmp_path)
    assert runtime.enqueue("task-003", "research-lab", "", "analyze", {}) == "queued"
    assert runtime.enqueue("task-003", "research-lab", "", "analyze", {}) == "duplicate"


def test_payload_size_is_bounded(tmp_path):
    runtime, token = setup(tmp_path, max_payload_bytes=1024)
    with pytest.raises(ValueError):
        runtime.enqueue("task-004", "research-lab", "", "analyze", {"large": "x" * 2000})


def test_expired_lease_retries_then_dead_letters(tmp_path):
    runtime, token = setup(tmp_path, max_attempts=2)
    agent = runtime.authenticate(token)
    runtime.enqueue("task-005", "research-lab", "", "analyze", {})
    first = runtime.claim(agent)
    runtime.conn.execute("UPDATE agent_tasks SET lease_until=0 WHERE id=?", (first["task_id"],))
    runtime.conn.commit()
    second = runtime.claim(agent)
    assert second["attempt"] == 2
    runtime.conn.execute("UPDATE agent_tasks SET lease_until=0 WHERE id=?", (second["task_id"],))
    runtime.conn.commit()
    assert runtime.claim(agent) is None
    assert runtime.status()["counts"]["dead_letter"] == 1


def test_registered_agent_must_explicitly_enter_working_before_claim(tmp_path):
    from app.agent_lifecycle import AgentLifecycle
    runtime, token = setup(tmp_path)
    agent = runtime.authenticate(token)
    lifecycle = AgentLifecycle(str(tmp_path / "ghostcorp.db"))
    lifecycle.register(agent["machine_id"])
    runtime.enqueue("task-lifecycle-gate", "research-lab", "researcher", "research", {})
    assert runtime.claim(agent) is None
    lifecycle.transition(agent["machine_id"], "WORKING", goal="Startup complete")
    assert runtime.claim(agent)["task_key"] == "task-lifecycle-gate"
