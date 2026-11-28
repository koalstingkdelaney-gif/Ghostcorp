# GhostCorp Web Agency

A separate, cloud-ready AI web-development agency for Ghost Corp — built from
`AUTONOMOUS_AGENCY_AGENT_BRIEF.md`. It works hand-in-hand with the existing
ghostcorpnet operation **without merging into or overwriting it**: prospects
are imported read-only from the existing agency pipeline, and pricing is the
company's existing live rate card.

## Current verified code scope

- **Secure foundation** — FastAPI service with health/readiness endpoints,
  SQLite store, audit log, durable idempotent jobs, hard spend governor
  (default cap **$0** before revenue), feature flags, and global pause switch.
- **Prospect intake** — manual lead intake plus a new guarded
  `POST /api/discovery/import` boundary for structured results from an
  approved search/business-data provider adapter.
- **Discovery provenance** — every imported record must include a business
  name, usable email, and absolute HTTP(S) source URL. The import boundary
  rejects local/private literal hosts and credential-bearing URLs, caps
  batches at 100, records provider provenance, and preserves deduplication
  and opt-out suppression.
- **Important limitation** — the discovery endpoint is an ingestion boundary,
  not a connected live search provider. No provider credentials or external
  search calls are included.
- **Website audit** — SSRF-hardened crawler (private/loopback/link-local/
  metadata IPs refused, redirects re-validated, size/time caps, robots.txt
  honored) producing evidence-backed findings.
- **Proposals** — drafts generated only from the existing rate card. Drafts
  only; sending stays with the existing gated pipelines.
- **Calling/SMS** — adapter interface present and **disabled by design**.
- **Payments** — disabled until the owner completes provider onboarding in
  the provider's own dashboard. No card data is ever collected by this code.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8791
.venv/bin/pytest -q
```

## Layout

- `app/` — config, governor, store, scoring, discovery ingestion, audit,
  proposals, communications, jobs, API
- `scripts/` — existing-pipeline import and end-to-end demo
- `tests/` — core and discovery-ingestion tests
- `docs/` — architecture, threat model, product requirements, provider setup,
  operations runbook, status

## Expanded platform architecture

- [`docs/PLATFORM-BLUEPRINT.md`](docs/PLATFORM-BLUEPRINT.md): full target system design and phased implementation.
- [`docs/OPEN-SOURCE-CATALOGUE.md`](docs/OPEN-SOURCE-CATALOGUE.md): open-source projects, free hosting options, wallet/payment boundaries, and evaluation links.

## Owner handoff

See [`docs/OWNER-HANDOFF.md`](docs/OWNER-HANDOFF.md) for the short list of external account steps, exact official links, and safe secret-handling instructions. Build work should continue without waiting for owner actions.

## Honest status

See `docs/STATUS.md` for what is implemented, tested, deployed, provider-
configured, and still blocked. This agency is **not** described as fully
autonomous or revenue-generating until those capabilities are proven end-to-end.

- [`docs/LOCAL-MODEL-GATEWAY.md`](docs/LOCAL-MODEL-GATEWAY.md): guarded, disabled-by-default local inference adapter; no cloud fallback or paid API.
- [`docs/AGENT-WORLD.md`](docs/AGENT-WORLD.md): persistent VR agent identities, daily routines, authenticated presence, and security boundaries.
- [`docs/MILLION-AGENT-WORLD.md`](docs/MILLION-AGENT-WORLD.md): target architecture for a million persistent agents, pooled workers, memory, VR scaling, budgets, and staged load tests.
- [`docs/OWNER-SIGN-IN.md`](docs/OWNER-SIGN-IN.md): private owner email sign-in requirements and deployment prerequisites.
- [`docs/OWNER-API-SECURITY.md`](docs/OWNER-API-SECURITY.md): owner-admin protection for private business API routes.
- [`docs/STARTUP-MODEL-FLEET.md`](docs/STARTUP-MODEL-FLEET.md): free/open-source model discovery, staged startup, capability routing, resource limits, and safety checks.
- [`docs/GHOSTCORP-VIRTUAL-OPERATING-SYSTEM.md`](docs/GHOSTCORP-VIRTUAL-OPERATING-SYSTEM.md): unified VR-centered business OS specification.
- [`docs/EXPANSION-CATALOGUE.md`](docs/EXPANSION-CATALOGUE.md): 1,200 planned capability entries across 30 departments. Catalogue entries are not claims of implementation.
- [`docs/DISTRIBUTED-COMPUTE.md`](docs/DISTRIBUTED-COMPUTE.md): opt-in community compute, contributor agent, sandbox, trust model, and Meshtastic boundaries.
- [`docs/BUILD-SNAPSHOT-2026-11-27.md`](docs/BUILD-SNAPSHOT-2026-11-27.md): current verified build inventory and missing deployment prerequisites.

- [`docs/PLATFORM-IMPLEMENTATION-2026-11-27.md`](docs/PLATFORM-IMPLEMENTATION-2026-11-27.md): implemented capability tracking and consent-based compute enrollment APIs, plus explicit remaining gaps.

- [`docs/FOUNDATION-ARCHITECTURE.md`](docs/FOUNDATION-ARCHITECTURE.md): expanded system foundation, execution/data/security planes, resource isolation and delivery gates.

- [`docs/SANDBOXING.md`](docs/SANDBOXING.md): fixed-workload Docker sandbox controls, setup requirements and remaining hardening.
- [`docs/WORKLOAD-GOVERNANCE.md`](docs/WORKLOAD-GOVERNANCE.md): signed workload manifests, fixed profiles, per-agent quotas and artifact path policy.
- [`docs/ARTIFACT-QUARANTINE.md`](docs/ARTIFACT-QUARANTINE.md): private, bounded, non-executing artifact intake and inspection.
- [`docs/ENGINEERING-BACKLOG.md`](docs/ENGINEERING-BACKLOG.md): prioritized engineering backlog with dependencies, acceptance criteria and security checks.
- [`docs/REAL-WORLD-PROBLEM-SOLUTIONS.md`](docs/REAL-WORLD-PROBLEM-SOLUTIONS.md): ranked real-world customer problems, product solutions, implementation status and build order.


### Agent workspaces

- [Agent-specific workspace allocation](docs/AGENT-WORKSPACES.md) — owner-gated empty workspace lifecycle, expiry and cleanup. This is not a code-execution or host-isolation service.

- [Dream-realm business research, product pipeline, and owner approval](docs/AGENT-WORLD.md)
- [GhostCorp GitHub organization and product distribution plan](docs/GITHUB-ORGANIZATION-AND-COMMERCE.md)
