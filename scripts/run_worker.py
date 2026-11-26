"""Run one GhostCorp queue task using a configured local Ollama model."""
import os
import sys

from app.model_gateway import LocalModelGateway
from app.worker import run_once


def main():
    api_base = os.environ.get("GHOSTCORP_API_BASE", "http://127.0.0.1:8000")
    token = os.environ.get("GHOSTCORP_MACHINE_TOKEN", "")
    gateway = LocalModelGateway()
    result = run_once(api_base, token, gateway)
    print(result)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"worker_error: {type(exc).__name__}: {str(exc)[:300]}", file=sys.stderr)
        raise SystemExit(1)
