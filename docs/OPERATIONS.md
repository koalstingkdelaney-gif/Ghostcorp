# Operations runbook

## Start / stop
- Start: `uvicorn app.main:app --port 8791`
- Pause everything (kill switch): set `AGENCY_PAUSED=1` and restart —
  mutating endpoints return 503; reads keep working.
- Stop: terminate the process. SQLite state persists in `data/agency.db`.

## Environment note
On hosts behind a DNS-translating egress proxy (this fleet's VM), set
`AGENCY_TRUST_PROXY_DNS_BENCH=1` or the audit crawler will refuse every
URL (its SSRF guard blocks the proxy's 198.18.0.0/15 translations).
Leave it unset on any normal host.

## Daily flow (as operated with the existing company)
1. `scripts/import_existing_leads.py` — pull new prospects + opt-outs from
   the existing pipeline (read-only, deduped, suppressed addresses refused).
2. `POST /api/jobs/run` or the demo script — audit + draft proposals.
3. Proposals are reviewed under the company's existing rules; sending, if
   any, happens only through the existing gated email pipelines and caps.
   This service never sends.

## Backups
Copy `data/agency.db` before upgrades. Restore = put the file back.

## Rollback
Code is in Git; check out the previous commit and restart. Data migrations
in Phase 1 are additive (CREATE TABLE IF NOT EXISTS).

## Monitoring
- `GET /health`, `GET /ready` (includes spend, flags, counts).
- `audit_log` table records every mutation with actor and time.
- Failed jobs land in `jobs` with status `failed` and the error recorded —
  never silently dropped.
