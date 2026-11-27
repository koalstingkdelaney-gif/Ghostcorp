"""Default-deny Docker sandbox for fixed public build/test workloads.

This is a guarded adapter, not a general-purpose remote shell. It runs one
fixed pytest command against a read-only workspace in a pinned image. It
requires an operator-provided Docker host and image digest; it never mounts
the Docker socket, host home, credentials, or writable source tree.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

_DIGEST_IMAGE = re.compile(r"^[a-zA-Z0-9._/:@-]+@sha256:[a-f0-9]{64}$")
_OUTPUT_LIMIT = 12000


class SandboxUnavailable(RuntimeError):
    pass


class DockerSandbox:
    def __init__(self, image=None, workspace=None, docker_binary="docker"):
        self.image = image if image is not None else os.environ.get("GHOSTCORP_SANDBOX_IMAGE", "")
        self.workspace = Path(workspace or os.environ.get("GHOSTCORP_SANDBOX_WORKSPACE", ".")).resolve()
        self.docker_binary = docker_binary

    def status(self):
        docker_found = shutil.which(self.docker_binary) is not None
        image_valid = bool(_DIGEST_IMAGE.fullmatch(self.image))
        workspace_valid = self.workspace.is_dir()
        enabled = os.environ.get("GHOSTCORP_SANDBOX_ENABLED", "0").lower() in {"1", "true", "yes"}
        return {
            "enabled": enabled and docker_found and image_valid and workspace_valid,
            "docker_available": docker_found,
            "pinned_image_configured": image_valid,
            "workspace_available": workspace_valid,
            "workload_allowlist": ["public-build-test", "synthetic-benchmark"],
            "network": "disabled",
            "workspace_mount": "read-only",
            "paid_spend": "not used by this adapter",
            "note": "Disabled unless explicitly enabled with Docker and an immutable image digest.",
        }

    def run_public_tests(self, timeout_seconds=300):
        state = self.status()
        if not state["enabled"]:
            raise SandboxUnavailable("sandbox is not enabled or Docker/image/workspace prerequisites are missing")
        if not 1 <= timeout_seconds <= 600:
            raise ValueError("timeout must be between 1 and 600 seconds")
        command = [
            self.docker_binary, "run", "--rm", "--pull=never",
            "--network=none", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
            "--pids-limit=64", "--memory=512m", "--memory-swap=512m",
            "--cpus=1.0", "--user=65532:65532",
            "--ulimit=nofile=256:256",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=64m",
            "--mount", f"type=bind,src={self.workspace},dst=/workspace,readonly",
            "--workdir=/workspace",
            self.image, "python", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
        ]
        try:
            completed = subprocess.run(
                command, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                timeout=timeout_seconds, check=False, env={"PATH": os.environ.get("PATH", "")},
            )
        except subprocess.TimeoutExpired as exc:
            return {"outcome": "TIMEOUT", "return_code": None,
                    "stdout": str(exc.stdout or "")[-_OUTPUT_LIMIT:],
                    "stderr": str(exc.stderr or "")[-_OUTPUT_LIMIT:]}
        return {
            "outcome": "PASSED" if completed.returncode == 0 else "FAILED",
            "return_code": completed.returncode,
            "stdout": (completed.stdout or "")[-_OUTPUT_LIMIT:],
            "stderr": (completed.stderr or "")[-_OUTPUT_LIMIT:],
            "isolation": {
                "network": "none", "root_filesystem": "read-only",
                "workspace": "read-only", "capabilities": "dropped",
                "privilege_escalation": "disabled", "memory_limit": "512 MiB",
                "cpu_limit": "1 core", "process_limit": 64,
            },
        }
