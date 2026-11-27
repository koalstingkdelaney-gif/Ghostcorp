# Platform implementation increment — 2026-11-27

This increment moves selected foundations from specification into code. It does not claim the whole twelve-workstream plan is complete.

## Implemented in this increment

### Capability tracking API
- `GET /api/platform/capabilities` returns the twelve top-level workstreams and explicit lifecycle statuses.
- `GET /api/platform/compute/status` reports contributor counts and confirms that this release does not execute remote code.

### Opt-in compute contributor registry
- `POST /api/platform/compute/enroll` records a contributor's explicit acceptance of consent version `ghostcorp-compute-v1`; enrollment is pending review and grants no execution capability.
- `POST /api/platform/compute/{node_id}/approve` is protected by the existing federation admin token and issues a one-time node bearer token.
- `POST /api/platform/compute/heartbeat` authenticates an active node and records bounded health metrics.
- `POST /api/platform/compute/{node_id}/revoke` invalidates its token.
- `GET /api/platform/compute/nodes` is admin-protected and lists enrolled nodes without secrets.
- Node tokens are stored as SHA-256 hashes and are only returned once.

### Tests
- Registry tests cover capability catalogue initialization, pending enrollment, approval, heartbeat, token authentication and revocation.

## Not yet implemented

- No compute worker, job execution, container sandbox, remote command protocol or downloadable contributor agent.
- No public contributor web page or contributor terms page.
- No Meshtastic/MQTT adapter.
- No infrastructure provider discovery crawler or automated account creation.
- No corporate outreach or email sender.
- No live email provider connection or persistent email consent.
- No vector database or knowledge graph.
- No always-on deployment or uptime proof.
- No production owner login or VR-to-backend authenticated session.
- No live payments or payout execution.

## Safety model

Public enrollment does not equal permission to run work. Only approved nodes receive credentials, and even approved nodes cannot claim jobs in this increment because remote execution is deliberately absent. Do not deploy a compute worker until sandboxing, local resource enforcement, signed releases, data classification, audit and security review are implemented.

## Local verification still required

Run `pytest -q` in the repository environment and validate FastAPI startup. This code-writing session did not execute the test suite or deploy the service.


## Follow-up foundation hardening

- Contributor enrollment now validates display-name length, resource object shape and strict GPU boolean type.
- Contributor heartbeat metrics are persisted, not merely returned.
- Capacity inventory reports contributor-declared CPU/RAM/disk and paused/reporting counts, explicitly labelled as unverified declarations.
- New read-only endpoint: `GET /api/platform/compute/capacity`.
- Tests expanded for telemetry persistence, capacity aggregation and invalid enrollment input.
- Added [FOUNDATION-ARCHITECTURE.md](FOUNDATION-ARCHITECTURE.md), defining the experience, control, execution, memory, communications, distributed infrastructure, business, security and reliability planes.
- The 1,200-entry catalogue remains a planned capability inventory; no catalogue item becomes live merely because it is listed.

**Verification note:** GitHub Actions test execution has not been confirmed in this session. The source changes are committed; do not treat the tests as passing until CI reports success.


## Follow-on sandbox and workload-governance increment

- Added `app/sandbox.py` and `GET /api/sandbox/status` plus owner-admin-gated `POST /api/sandbox/run-public-tests`. This runs only the fixed public pytest command with network disabled, read-only mounts/filesystem, dropped capabilities, non-root UID, CPU/memory/process limits and bounded output/time. It is not a general-purpose code runner.
- Added `app/workload_governance.py`: fixed workload profiles, short-lived HMAC-signed manifests bound to an agent and immutable commit SHA, and a SQLite per-agent quota ledger with idempotent reservations, a default one-active-job limit and a 1,800-second rolling 24-hour budget.
- Added admin-gated endpoints: `GET /api/workloads/catalog`, `POST /api/workloads/manifest`, `POST /api/workloads/quotas/reserve`, `POST /api/workloads/quotas/settle`, and `GET /api/workloads/quotas/{agent_id}`.
- Added artifact path-name validation to reject traversal and unsafe relative paths. This is not yet artifact content scanning or quarantine.
- Manifest issuance requires `GHOSTCORP_WORKLOAD_SIGNING_KEY` (at least 32 characters) in the deployment secret manager. It is not committed and must not be placed in frontend code.
- Added unit tests for manifest tampering/expiry, quota limits/idempotency, and artifact path validation.

**Still blocked:** no trusted Docker host/image is configured; no actual contributor workload is dispatched; no per-job workspace lifecycle, artifact quarantine/content inspection, signed downloadable contributor agent, rootless multi-tenant runtime, or security review is complete. No test run or production deployment is verified in this session.


## Artifact quarantine increment (2026-11-27)

- Added app/artifact_quarantine.py and owner-admin routes for bounded artifact intake and metadata listing.
- Intake is bound to active, non-expired workspace registry records and uses no-follow filesystem operations, strict relative paths, single-link regular-file checks, private storage permissions, a 1 MiB default size limit, SHA-256 and source-mutation detection.
- Built-in inspection classifies text/JSON, archives, executable/script-like content, PDF, images and unknown binary data. It does not extract, render or execute artifacts and always leaves them QUARANTINED with review_required=true.
- Added docs/ARTIFACT-QUARANTINE.md and docs/ENGINEERING-BACKLOG.md with the next distinct implementation units.
- CI verification: run 46084948753, commit 2af6d589dac7500dacbc02c5e48e290afd63581b, 95 passed and 1 non-fatal deprecation warning.
- Remaining: no antivirus scanner, owner review/promotion workflow, retention/recovery, configured storage roots, production host or deployment. No contributor work can execute through this feature.
