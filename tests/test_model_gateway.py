import json
from io import BytesIO

import pytest

from app.model_gateway import LocalModelGateway, ModelPolicyError


def test_gateway_is_disabled_by_default_and_never_cloud():
    gateway = LocalModelGateway(enabled=False, model="local-test")
    status = gateway.status()
    assert status["enabled"] is False
    assert status["cloud_fallback"] is False
    assert status["paid_api_spend_usd"] == 0


@pytest.mark.parametrize("endpoint", [
    "https://example.com", "http://example.com", "http://127.0.0.1:8080/path?x=1",
    "http://user:pass@localhost:11434",
])
def test_gateway_rejects_non_loopback_or_ambiguous_endpoint(endpoint):
    with pytest.raises(ModelPolicyError):
        LocalModelGateway(enabled=True, endpoint=endpoint, model="local-test")


def test_gateway_rejects_unapproved_tasks_and_sensitive_data():
    gateway = LocalModelGateway(enabled=True, model="local-test")
    with pytest.raises(ModelPolicyError):
        gateway.generate("send_email", "public", "hello")
    with pytest.raises(ModelPolicyError):
        gateway.generate("research_summary", "financial", "private account data")


def test_gateway_calls_only_local_ollama_and_returns_bounded_result(monkeypatch):
    import app.model_gateway as module

    seen = {}

    class Response(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["body"] = json.loads(request.data.decode())
        return Response(json.dumps({"message": {"content": "local answer"}}).encode())

    monkeypatch.setattr(module, "urlopen", fake_urlopen)
    gateway = LocalModelGateway(enabled=True, model="local-test")
    result = gateway.generate("research_summary", "internal", "summarize public docs")
    assert seen["url"] == "http://127.0.0.1:11434/api/chat"
    assert seen["body"]["stream"] is False
    assert result["content"] == "local answer"
    assert result["paid_api_spend_usd"] == 0
    assert result["tools_executed"] is False


def test_gateway_rejects_oversized_prompt():
    gateway = LocalModelGateway(enabled=True, model="local-test")
    with pytest.raises(ModelPolicyError):
        gateway.generate("research_summary", "public", "x" * 20001)
