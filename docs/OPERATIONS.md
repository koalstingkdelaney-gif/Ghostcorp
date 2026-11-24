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

Use the encrypted backup utility; do not copy a live WAL database file by ordinary file copy.

1. Install the `age` encryption utility on the authorized host.
2. Set `AGE_RECIPIENT` to the owner's age **public** recipient (the private identity stays offline and outside Git).
3. Run: `python scripts/backup_db.py`.
4. The script uses SQLite's online backup API, checks integrity, encrypts with age, decrypts into a temporary directory to verify the round trip, and retains the newest three encrypted snapshots.
5. Backups are written to `backups/`, which is gitignored. Copy encrypted snapshots to a separate authorized off-host destination when one is configured.

Restore: decrypt an encrypted snapshot into a protected temporary location, verify `PRAGMA integrity_check`, stop the service, replace the database, and restart. Practice on a disposable copy first.

The backup script is implemented but has not yet been run against a production database or an owner-configured encryption recipient. No off-host backup destination is currently verified.

## Rollback
Code is in Git; check out the previous commit and restart. Data migrations
in Phase 1 are additive (CREATE TABLE IF NOT EXISTS).

## Monitoring
- `GET /health`, `GET /ready` (includes spend, flags, counts).
- `audit_log` table records every mutation with actor and time.
- Failed jobs land in `jobs` with status `failed` and the error recorded —
  never silently dropped.
