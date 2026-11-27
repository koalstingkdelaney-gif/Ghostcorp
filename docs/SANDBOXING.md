# GhostCorp sandbox implementation

## What is implemented

`app/sandbox.py` provides a default-deny Docker adapter for one fixed workload: running the repository's public pytest suite. It does not accept arbitrary commands, scripts, images or workload payloads.

The API exposes:
- `GET /api/sandbox/status` — reports whether prerequisites are present.
- `POST /api/sandbox/run-public-tests` — owner-admin gated fixed test run; disabled unless explicitly configured.

## Isolation applied to each container

- immutable image reference required (`name@sha256:<64 hex>`);
- image must already exist locally (`--pull=never`);
- no network (`--network=none`);
- read-only container root filesystem;
- repository mounted read-only;
- all Linux capabilities dropped;
- no-new-privileges enabled;
- non-root numeric UID/GID;
- 512 MiB memory and 1 CPU;
- 64 process limit and file-descriptor limit;
- small no-exec/no-suid/no-device temporary filesystem;
- no Docker socket, host home, secrets or writable source mounts;
- fixed pytest command only and bounded timeout/output.

## Configuration required on a trusted host

Set all of the following in the deployment environment:
- `GHOSTCORP_SANDBOX_ENABLED=1`
- `GHOSTCORP_SANDBOX_IMAGE=<registry/name>@sha256:<immutable-digest>`
- `GHOSTCORP_SANDBOX_WORKSPACE=<absolute-read-only-checkout-path>`
- Docker Engine and the exact image digest must already be installed locally.

The image must contain the supported Python version, pytest and the project's test dependencies. Build and scan that image in a trusted pipeline, then pin its digest. Do not use mutable tags such as `latest`.

## Limits and remaining hardening

This is an initial fixed-workload sandbox adapter, not a complete multi-tenant hostile-code execution service. It has no job scheduler, per-contributor isolated runtime, artifact quarantine/scanning, signed workload manifests, egress proxy, seccomp profile management, rootless Docker provisioning, Kubernetes isolation or remote contributor execution. Docker daemon security remains part of the trusted host boundary. Never run untrusted arbitrary code or third-party contributor jobs through this adapter.

The adapter is not enabled by default. This repository does not currently prove that a Docker host, pinned image, or production deployment exists. No claim is made that sandboxed tests have run successfully.
