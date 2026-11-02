# Status — 2026-11-02 (Phase 0 + Phase 1)

## Implemented and tested
- FastAPI service: `/health`, `/ready`, `/api/packages`, lead intake/list,
  per-lead audit + proposal endpoints, job runner, dashboard summary,
  comms endpoints that return the disabled state. Verified live locally
  (uvicorn on port 8791, all endpoints exercised with curl).
- Core: spend governor (cap $0 default, enforced, tested), SQLite store,
  transparent lead scoring, SSRF-hardened website audit, rate-card proposal
  drafts, disabled-by-design calling/SMS adapters, durable idempotent jobs,
  audit log, global pause kill switch.
- Tests: **10/10 passing** (`pytest -q`, 2026-11-02).

## Hands-on with the existing company (verified, real data)
- Imported the existing ghostcorpnet agency pipeline read-only:
  **7,059 rows seen → 6,748 leads added, 311 duplicates skipped,
  12 opt-out suppressions loaded** and enforced.
- Audited the top 10 scored prospects with the safe crawler — all returned
  HTTP 200 with recorded evidence (response time, page weight, content
  type) and real findings, e.g. missing meta descriptions, missing H1,
  slow/heavy homepages.
- Drafted **10 proposals**, all priced strictly from the existing live rate
  card (AI Front Desk $299 + $149/mo for these). Nothing was sent.

## Environment note (honest)
This VM sits behind an egress proxy whose DNS translates public hostnames
into 198.18.0.0/15. The audit crawler's SSRF guard correctly refused those
until the operator flag `AGENCY_TRUST_PROXY_DNS_BENCH=1` was set for this
sandbox (default OFF everywhere else; all other non-public ranges stay
refused). First-pass audit refusals were overwritten with real audits.

## Not done / blocked (owner-side, see PROVIDER_SETUP.md)
- **Cloud deployment**: no host chosen/verified yet — service is deployed
  and proven locally only. Do not call it cloud-live.
- **Payments**: disabled. Needs the owner's Stripe onboarding (identity,
  payout details) in Stripe's dashboard; test-mode integration is Phase 4.
- **Calling/SMS**: disabled. Needs provider onboarding + registrations +
  documented consent + owner-approved scripts + the owner's enable flag.
  Unsolicited automated marketing calls stay off permanently.
- **GitHub Actions CI**: workflow documented in `docs/CI.md`; adding it
  needs the repo token's `workflow` scope (owner re-authorization).
- **Revenue**: $0. This agency has made no sales; proposals are drafts in
  the existing company's review flow, not sent pitches.
