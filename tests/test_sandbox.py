import subprocess

import pytest

from app.sandbox import DockerSandbox, SandboxUnavailable


def test_sandbox_is_default_denied(tmp_path, monkeypatch):
    monkeypatch.delenv("GHOSTCORP_SANDBOX_ENABLED", raising=False)
    runner = DockerSandbox(
        image="registry.example/ghostcorp-test@sha256:" + "a" * 64,
        workspace=str(tmp_path),
    )
    monkeypatch.setattr("app.sandbox.shutil.which", lambda _: "/usr/bin/docker")
    assert runner.status()["enabled"] is False
    with pytest.raises(SandboxUnavailable):
        runner.run_public_tests()


def test_sandbox_rejects_mutable_image_tag(tmp_path, monkeypatch):
    monkeypatch.setenv("GHOSTCORP_SANDBOX_ENABLED", "1")
    runner = DockerSandbox(image="python:3.12", workspace=str(tmp_path))
    monkeypatch.setattr("app.sandbox.shutil.which", lambda _: "/usr/bin/docker")
    assert runner.status()["pinned_image_configured"] is False


def test_sandbox_runs_only_fixed_isolated_test_command(tmp_path, monkeypatch):
    monkeypatch.setenv("GHOSTCORP_SANDBOX_ENABLED", "1")
    runner = DockerSandbox(
        image="registry.example/ghostcorp-test@sha256:" + "b" * 64,
        workspace=str(tmp_path),
    )
    monkeypatch.setattr("app.sandbox.shutil.which", lambda _: "/usr/bin/docker")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, "2 passed", "")

    monkeypatch.setattr("app.sandbox.subprocess.run", fake_run)
    result = runner.run_public_tests()
    command = captured["command"]
    assert result["outcome"] == "PASSED"
    assert "--network=none" in command
    assert "--read-only" in command
    assert "--cap-drop=ALL" in command
    assert "--security-opt=no-new-privileges:true" in command
    assert "--memory=512m" in command
    assert "--cpus=1.0" in command
    assert command[-5:] == ["python", "-I", "-m", "pytest", "-q"]
    assert "GHOSTCORP_SANDBOX_ENABLED" not in captured["kwargs"]["env"]


def test_sandbox_rejects_unbounded_timeout(tmp_path, monkeypatch):
    monkeypatch.setenv("GHOSTCORP_SANDBOX_ENABLED", "1")
    runner = DockerSandbox(
        image="registry.example/ghostcorp-test@sha256:" + "c" * 64,
        workspace=str(tmp_path),
    )
    monkeypatch.setattr("app.sandbox.shutil.which", lambda _: "/usr/bin/docker")
    with pytest.raises(ValueError):
        runner.run_public_tests(timeout_seconds=900)
