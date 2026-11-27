# GhostCorp build snapshot

**Snapshot date:** 2026-11-27  
**Repositories:** `koalstingkdelaney-gif/ghostcorpnet-site` and `koalstingkdelaney-gif/Ghostcorp`.

## Existing repository work

### Website / VR repository

- Existing domain and website: `ghostcorpnet.com`.
- VR entry point: `/vr/`.
- Three.js/WebXR headquarters prototype with desktop fallback, Quest controller support, movement, interaction and department portals.
- The current VR scene is a visual foundation. Its live business systems and owner authentication are not connected.
- The current page imports Three.js from a CDN. Deployment and Quest-browser behavior have not been verified in this work session.

### Backend repository

- FastAPI service foundation with health/readiness endpoints.
- SQLite persistence, audit log, lead intake, website audit, proposal drafting and bounded job runner.
- Spend governor with a $0 default cap.
- Identity-minimal division and machine-agent registry; provisioning requires an external admin token.
- Durable division-scoped task queue with idempotent keys, leases, retries and dead-letter handling.
- Persistent agent-world profiles, routines, zones, heartbeat and bounded event history.
- Local model gateway adapter restricted to loopback inference; disabled by default and not connected to an agent worker.
- Simulated ledger only; no live payment processor, wallet custody, conversion or payouts.
- Communications are disabled at the API layer; no live email sender is connected.
- Documentation for always-on operations, local model runtime, owner sign-in, virtual OS and scale architecture.

## Not yet implemented or verified

- Production backend hosting or 24/7 workers.
- Secure owner login/session bridge.
- Quest-tested local model download and inference.
- Connected AI scheduler/model executor.
- Live agent heartbeats or autonomous business activity.
- Community compute enrollment, sandbox execution or Meshtastic gateway.
- Persistent production vector database or memory service.
- Live email provider integration and standing send permissions.
- Checkout, payouts, banking or crypto settlement.
- Deployment pipeline and verified live domain routes.

## Expansion now catalogued

- 1,200 planned capabilities across 30 departments in `EXPANSION-CATALOGUE.md`.
- Distributed compute and community mesh protocol in `DISTRIBUTED-COMPUTE.md`.
- All catalogue entries remain PLANNED until code, tests and deployment evidence exist.

## Operating principles

- Existing domain and repositories remain the foundation.
- No user-owned computer or dedicated server is assumed.
- $0 default spend; no paid fallback or upgrade without approval.
- Public contributor devices require explicit opt-in, visible resource limits and immediate revocation.
- Meshtastic is for low-bandwidth communication, not compute hosting.
- AI agents may research, draft and run sandboxed non-sensitive work; high-impact external actions remain gated.
- Do not claim 24/7 uptime until an always-on runtime is actually deployed and monitored.
