"""Bounded long-running queue worker for a host with local Ollama compute.

The worker only claims approved queue tasks and delegates to the existing
loopback-only LocalModelGateway. It never executes tools or arbitrary code.
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import time
from urllib.parse import urlsplit

from app.model_gateway import LocalModelGateway
from app.worker import run_once

LOG = logging.getLogger("ghostcorp.worker")
_STOP = False


def _stop(_signum, _frame):
    global _STOP
    _STOP = True


def positive_int(name: str, default: int, minimum: int, maximum: int,
                 environ: dict | None = None) -> int:
    env = os.environ if environ is None else environ
    raw = env.get(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def validate_api_base(value: str) -> str:
    parsed = urlsplit(value)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (parsed.scheme != "https" and not (parsed.scheme == "http" and local)):
        raise ValueError("GHOSTCORP_API_BASE must use HTTPS (HTTP is allowed only for loopback)")
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("GHOSTCORP_API_BASE must be an origin/base path without credentials, query, or fragment")
    return value.rstrip("/")


def main() -> int:
    global _STOP
    logging.basicConfig(level=os.getenv("GHOSTCORP_WORKER_LOG_LEVEL", "INFO").upper(),
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        api_base = validate_api_base(os.getenv("GHOSTCORP_API_BASE", "http://127.0.0.1:8000"))
        token = os.getenv("GHOSTCORP_MACHINE_TOKEN", "")
        if not token:
            raise ValueError("GHOSTCORP_MACHINE_TOKEN is required")
        max_tasks = positive_int("GHOSTCORP_WORKER_MAX_TASKS", 20, 1, 200)
        max_runtime = positive_int("GHOSTCORP_WORKER_MAX_RUNTIME_SECONDS", 3300, 60, 3600)
        idle_sleep = positive_int("GHOSTCORP_WORKER_IDLE_SECONDS", 15, 5, 300)
        gateway = LocalModelGateway()
    except ValueError as exc:
        LOG.error("worker configuration invalid: %s", exc)
        return 2

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    started = time.monotonic()
    completed = 0
    backoff = 5
    LOG.info("worker started; max_tasks=%s max_runtime_seconds=%s", max_tasks, max_runtime)

    while not _STOP and completed < max_tasks and time.monotonic() - started < max_runtime:
        try:
            result = run_once(api_base, token, gateway)
            backoff = 5
            if result.get("outcome") == "idle":
                time.sleep(idle_sleep)
                continue
            completed += 1
            # Never log task prompts, customer data, machine tokens or model output.
            LOG.info("task processed; task_id=%s execution_status=%s",
                     result.get("task_id"), result.get("execution_status", "unknown"))
        except Exception as exc:
            LOG.warning("worker iteration failed (%s); retrying in %ss",
                        type(exc).__name__, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 300)

    LOG.info("worker stopped; tasks_processed=%s stop_requested=%s",
             completed, _STOP)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
