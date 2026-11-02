# GhostCorp Web Agency

A separate, cloud-ready AI web-development agency for Ghost Corp — built from
`AUTONOMOUS_AGENCY_AGENT_BRIEF.md`. It works hand-in-hand with the existing
ghostcorpnet operation **without merging into or overwriting it**: prospects
are imported read-only from the existing agency pipeline, and pricing is the
company's existing live rate card.

## What is live today (Phase 0 + Phase 1, verified locally)

- **Secure foundation** — FastAPI service with `/health` and `/ready`,
  environment-based config, SQLite store (leads, suppressions, proposals,
  durable idempotent jobs, audit log), a hard **spend governor** (default cap
  **$0** before revenue), feature flags, and a global pause kill switch
  (`AGENCY_PAUSED=1` blocks all mutating endpoints).
- **Prospect intelligence** — transparent lead scoring with written reasons,
  one-email-one-lead dedup, opt-out suppression imported from the existing
  operation, and provenance (source URL + collector) on every lead.
- **Website audit** — SSRF-hardened crawler (private/loopback/link-local/
  metadata IPs refused, redirects re-validated, size/time caps, robots.txt
  honored) producing evidence-backed findings.
- **Proposals** — drafts generated only from the existing rate card:
  AI Website **$499** (+ optional $99/mo care), AI Front Desk **$299 + $149/mo**
  (web chat + email only), Property Video Walkthroughs **$199** (4-pack $599).
  No invented prices, testimonials, or guarantees. Drafts only — sending stays
  with the existing gated pipelines.
- **Calling/SMS** — adapter interface present and **disabled by design**. No
  unsolicited automated marketing calls/texts; see `docs/PROVIDER_SETUP.md`.
- **Payments** — disabled until the owner completes provider onboarding in the
  provider's own dashboard. No card data is ever collected by this code.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8791
# import the existing company's prospects (read-only on the source):
.venv/bin/python scripts/import_existing_leads.py
# audit top leads + draft proposals (nothing is sent):
.venv/bin/python scripts/demo_e2e.py 5
.venv/bin/pytest -q
```

## Layout

- `app/` — config, governor, store, scoring, audit, proposals, comms, jobs, API
- `scripts/` — existing-pipeline import, end-to-end demo
- `tests/` — unit + API tests
- `docs/` — architecture, threat model, product requirements, provider setup,
  operations runbook, status

## Honest status

See `docs/STATUS.md` for what is implemented, tested, deployed, and still
blocked. This agency is **not** described as fully autonomous or
revenue-generating until those capabilities are proven end-to-end.
