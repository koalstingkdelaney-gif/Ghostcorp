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

## Honest status

See `docs/STATUS.md` for what is implemented, tested, deployed, provider-
configured, and still blocked. This agency is **not** described as fully
autonomous or revenue-generating until those capabilities are proven end-to-end.
