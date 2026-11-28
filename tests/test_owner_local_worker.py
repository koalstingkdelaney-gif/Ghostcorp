from fastapi.testclient import TestClient

from app import main
from app.agent_lifecycle import AgentLifecycle
from app.agent_runtime import AgentRuntime
from app.federation import FederationRegistry


def setup_owner_worker(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "owner-worker-secret")
    federation = FederationRegistry(":memory:")
    federation.create_division("research-lab", "Research Lab", "")
    created = federation.create_agent("research-lab", "researcher")
    shared_db = str(tmp_path / "owner-worker.sqlite")
    lifecycle = AgentLifecycle(shared_db)
    lifecycle.register(created["machine_id"])
    lifecycle.transition(created["machine_id"], "WORKING", "Research customer problems")
    runtime = AgentRuntime(shared_db)
    monkeypatch.setattr(main, "federation", federation)
    monkeypatch.setattr(main, "agent_lifecycle", lifecycle)
    monkeypatch.setattr(main, "agent_runtime", runtime)
    return created["machine_id"], lifecycle, runtime


def test_owner_local_worker_claims_and_completes_task(monkeypatch, tmp_path):
    machine_id, lifecycle, runtime = setup_owner_worker(monkeypatch, tmp_path)
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


def test_owner_local_worker_cannot_claim_while_agent_sleeps(monkeypatch, tmp_path):
    machine_id, lifecycle, runtime = setup_owner_worker(monkeypatch, tmp_path)
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

def test_owner_local_dream_session_can_submit_reviewable_artifact(monkeypatch, tmp_path):
    machine_id, lifecycle, runtime = setup_owner_worker(monkeypatch, tmp_path)
    lifecycle.transition(machine_id, "SLEEPING", reason="local work paused")
    lifecycle.transition(machine_id, "DREAMING", goal="Explore product ideas")
    client = TestClient(main.app)
    response = client.post(
        f"/api/owner/agents/{machine_id}/dream-artifacts",
        headers={"X-Federation-Admin": "owner-worker-secret"},
        json={
            "artifact_type": "product-opportunity",
            "title": "Small-business website repair kit",
            "summary": "A repeatable checklist and test harness for common website failures.",
            "artifact": {"evidence_class": "MODEL_HYPOTHESIS", "external_research": False},
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "AWAITING_REVIEW"


def test_owner_local_dream_artifact_rejected_outside_dream_mode(monkeypatch, tmp_path):
    machine_id, lifecycle, runtime = setup_owner_worker(monkeypatch, tmp_path)
    client = TestClient(main.app)
    response = client.post(
        f"/api/owner/agents/{machine_id}/dream-artifacts",
        headers={"X-Federation-Admin": "owner-worker-secret"},
        json={
            "artifact_type": "idea", "title": "Idea",
            "summary": "A short idea outside dream mode.",
            "artifact": {},
        },
    )
    assert response.status_code == 409
