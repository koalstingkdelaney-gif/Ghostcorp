import json
from io import BytesIO

import pytest

import app.worker as worker
from app.model_gateway import LocalModelGateway


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_worker_claims_generates_and_completes_one_task(monkeypatch):
    calls = []
    task = {"task_id": 7, "lease_token": "x" * 32, "task_type": "research_summary",
            "payload": {"privacy_class": "internal", "prompt": "summarize"}}

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, request.method))
        if request.full_url.endswith("/api/runtime/claim"):
            payload = task
        else:
            payload = {"outcome": "completed"}
            assert json.loads(request.data)["result"]["execution_status"] == "completed"
        return Response(json.dumps(payload).encode())

    monkeypatch.setattr(worker, "urlopen", fake_urlopen)
    gateway = LocalModelGateway(enabled=True, model="local-model")
    monkeypatch.setattr(gateway, "generate", lambda **kwargs: {
        "provider": "local_ollama", "model": "local-model", "content": "answer"
    })
    result = worker.run_once("http://localhost:8000", "machine-secret", gateway)
    assert result == {"outcome": "completed", "task_id": 7, "execution_status": "completed"}
    assert len(calls) == 2


def test_worker_records_policy_block_without_model_execution(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        if request.full_url.endswith("/api/runtime/claim"):
            payload = {"task_id": 8, "lease_token": "y" * 32,
                       "task_type": "research_summary",
                       "payload": {"privacy_class": "financial", "prompt": "sensitive"}}
        else:
            body = json.loads(request.data)["result"]
            assert body["execution_status"] == "blocked_by_policy"
            payload = {"outcome": "completed"}
        return Response(json.dumps(payload).encode())

    monkeypatch.setattr(worker, "urlopen", fake_urlopen)
    gateway = LocalModelGateway(enabled=True, model="local-model")
    result = worker.run_once("http://localhost:8000", "machine-secret", gateway)
    assert result["execution_status"] == "blocked_by_policy"
    assert len(calls) == 2


def test_worker_idle_does_not_call_model(monkeypatch):
    def fake_urlopen(request, timeout):
        return Response(b'{"outcome":"no_matching_task"}')
    monkeypatch.setattr(worker, "urlopen", fake_urlopen)
    gateway = LocalModelGateway(enabled=False)
    assert worker.run_once("http://localhost:8000", "machine-secret", gateway) == {"outcome": "idle"}


def test_worker_requires_machine_token():
    with pytest.raises(ValueError):
        worker.run_once("http://localhost:8000", "", LocalModelGateway(enabled=False))
