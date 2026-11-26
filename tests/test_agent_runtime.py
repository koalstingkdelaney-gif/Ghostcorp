import pytest

from app.federation import FederationRegistry
from app.agent_runtime import AgentRuntime


def setup(tmp_path):
    db = str(tmp_path / "ghostcorp.db")
    registry = FederationRegistry(db)
    registry.create_division("research-lab", "Research Lab", "")
    registry.create_division("build-lab", "Build Lab", "")
    agent = registry.create_agent("research-lab", "researcher")
    runtime = AgentRuntime(db)
    return runtime, agent["agent_token"]


def test_machine_agent_claims_and_completes_own_division_task(tmp_path):
    runtime, token = setup(tmp_path)
    agent = runtime.authenticate(token)
    assert agent["division_slug"] == "research-lab"
    assert runtime.enqueue("task-001", "research-lab", "researcher",
                           "research", {"topic": "open standards"}) == "queued"
    task = runtime.claim(agent)
    assert task["task_key"] == "task-001"
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
