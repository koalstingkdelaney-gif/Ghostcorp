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
