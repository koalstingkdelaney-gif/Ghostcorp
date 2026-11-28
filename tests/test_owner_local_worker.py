from fastapi.testclient import TestClient

from app import main
from app.agent_lifecycle import AgentLifecycle
from app.agent_runtime import AgentRuntime
from app.federation import FederationRegistry


def setup_owner_worker(monkeypatch):
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "owner-worker-secret")
    federation = FederationRegistry(":memory:")
    federation.create_division("research-lab", "Research Lab", "")
    created = federation.create_agent("research-lab", "researcher")
    lifecycle = AgentLifecycle(":memory:")
    lifecycle.register(created["machine_id"])
    lifecycle.transition(created["machine_id"], "WORKING", "Research customer problems")
    runtime = AgentRuntime(":memory:")
    monkeypatch.setattr(main, "federation", federation)
    monkeypatch.setattr(main, "agent_lifecycle", lifecycle)
    monkeypatch.setattr(main, "agent_runtime", runtime)
    return created["machine_id"], lifecycle, runtime


def test_owner_local_worker_claims_and_completes_task(monkeypatch):
    machine_id, lifecycle, runtime = setup_owner_worker(monkeypatch)
    runtime.enqueue("owner-worker-task-001", "research-lab", "researcher",
                    "research_summary", {"privacy_class": "internal", "prompt": "Summarize"})
    client = TestClient(main.app)
    headers = {"X-Federation-Admin": "owner-worker-secret"}
    claimed = client.post("/api/runtime/owner/claim", json={"machine_id": machine_id},
                          headers=headers)
    assert claimed.status_code == 200
    task = claimed.json()
    assert task["task_type"] == "research_summary"
    completed = client.post(
        f"/api/runtime/owner/tasks/{task['task_id']}/complete",
        json={"machine_id": machine_id, "lease_token": task["lease_token"],
              "result": {"execution_status": "completed", "content": "Test result"}},
        headers=headers,
    )
    assert completed.status_code == 200
    assert completed.json()["outcome"] == "completed"


def test_owner_local_worker_cannot_claim_while_agent_sleeps(monkeypatch):
    machine_id, lifecycle, runtime = setup_owner_worker(monkeypatch)
    lifecycle.transition(machine_id, "SLEEPING", reason="owner paused local worker")
    runtime.enqueue("owner-worker-task-002", "research-lab", "researcher",
                    "research_summary", {"privacy_class": "internal", "prompt": "Summarize"})
    client = TestClient(main.app)
    response = client.post(
        "/api/runtime/owner/claim", json={"machine_id": machine_id},
        headers={"X-Federation-Admin": "owner-worker-secret"},
    )
    assert response.status_code == 200
    assert response.json()["outcome"] == "no_matching_task"
