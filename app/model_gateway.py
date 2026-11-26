"""Free-first local model gateway with explicit privacy and task policy.

No cloud provider, paid API, remote endpoint, or model is enabled by default.
The first adapter is deliberately limited to a loopback Ollama-compatible API.
This module never receives secrets from task payloads and never executes tools.
"""
from __future__ import annotations

import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ALLOWED_TASKS = {"research_summary", "classify", "code_review", "draft_internal"}
PRIVACY_CLASSES = {"public", "internal", "restricted", "financial"}
MAX_PROMPT_CHARS = 20000


class ModelPolicyError(ValueError):
    """A model request violates the local execution policy."""


def _local_endpoint(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ModelPolicyError("only a loopback HTTP model endpoint is permitted")
    return value.rstrip("/")


class LocalModelGateway:
    def __init__(self, enabled: bool | None = None, endpoint: str | None = None,
                 model: str | None = None, timeout_seconds: int = 60):
        self.enabled = (os.getenv("GHOSTCORP_LOCAL_MODEL_ENABLED", "0").lower()
                        in {"1", "true", "yes", "on"}) if enabled is None else bool(enabled)
        self.endpoint = _local_endpoint(
            endpoint or os.getenv("GHOSTCORP_OLLAMA_URL", "http://127.0.0.1:11434")
        )
        self.model = (model or os.getenv("GHOSTCORP_OLLAMA_MODEL", "")).strip()
        self.timeout_seconds = max(5, min(int(timeout_seconds), 120))

    def status(self) -> dict:
        return {
            "mode": "LOCAL_OLLAMA",
            "enabled": self.enabled and bool(self.model),
            "configured": bool(self.model),
            "endpoint_scope": "loopback_only",
            "model": self.model if self.model else None,
            "paid_api_spend_usd": 0,
            "cloud_fallback": False,
            "tool_execution": False,
        }

    def generate(self, task_type: str, privacy_class: str, prompt: str,
                 max_output_tokens: int = 512) -> dict:
        if task_type not in ALLOWED_TASKS:
            raise ModelPolicyError("task type is not approved for model execution")
        if privacy_class not in PRIVACY_CLASSES:
            raise ModelPolicyError("unknown privacy classification")
        if privacy_class in {"restricted", "financial"}:
            raise ModelPolicyError("restricted and financial data are not eligible for model submission")
        if not self.enabled or not self.model:
            raise ModelPolicyError("local model gateway is disabled or not configured")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_PROMPT_CHARS:
            raise ModelPolicyError("prompt must be non-empty and within the configured size limit")
        token_limit = max(32, min(int(max_output_tokens), 2048))
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_predict": token_limit},
        }).encode("utf-8")
        request = Request(
            self.endpoint + "/api/chat", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            result = json.loads(response.read(2_000_000).decode("utf-8"))
        message = result.get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("local model returned an invalid response")
        return {
            "status": "completed",
            "provider": "local_ollama",
            "model": self.model,
            "content": content[:50000],
            "paid_api_spend_usd": 0,
            "tools_executed": False,
        }
