"""One-task-at-a-time worker for the GhostCorp durable queue.

The worker can only process explicitly approved internal drafting/research task
types through the loopback-only model gateway. It cannot execute tools, code,
payments, communications, deployments, or arbitrary actions.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .model_gateway import LocalModelGateway, ModelPolicyError


def _request_json(url: str, token: str, method: str = "GET", body: dict | None = None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    })
    with urlopen(request, timeout=20) as response:
        raw = response.read(1_000_000)
    return json.loads(raw.decode("utf-8")) if raw else {}


def run_once(api_base: str, machine_token: str, gateway: LocalModelGateway) -> dict:
    """Claim and process at most one task; safe to call from a scheduled runner."""
    if not machine_token:
        raise ValueError("machine token is required")
    base = api_base.rstrip("/")
    task = _request_json(base + "/api/runtime/claim", machine_token, "POST")
    if task.get("outcome") == "no_matching_task":
        return {"outcome": "idle"}
    task_id = task.get("task_id")
    lease = task.get("lease_token")
    payload = task.get("payload") or {}
    if not isinstance(task_id, int) or not isinstance(lease, str):
        raise RuntimeError("queue returned an invalid task lease")

    task_type = task.get("task_type", "")
    privacy = payload.get("privacy_class", "internal")
    prompt = payload.get("prompt", "")
    try:
        generated = gateway.generate(
            task_type=task_type,
            privacy_class=privacy,
            prompt=prompt,
            max_output_tokens=payload.get("max_output_tokens", 512),
        )
        result = {
            "execution_status": "completed",
            "provider": generated["provider"],
            "model": generated["model"],
            "content": generated["content"],
            "paid_api_spend_usd": 0,
            "tools_executed": False,
        }
    except ModelPolicyError as exc:
        # Preserve the task result and make policy blocks visible to operators.
        result = {
            "execution_status": "blocked_by_policy",
            "reason": str(exc)[:300],
            "paid_api_spend_usd": 0,
            "tools_executed": False,
        }

    completed = _request_json(
        base + f"/api/runtime/tasks/{task_id}/complete",
        machine_token, "POST",
        {"lease_token": lease, "result": result},
    )
    return {"outcome": completed.get("outcome", "unknown"),
            "task_id": task_id, "execution_status": result["execution_status"]}
