# Architecture

## Shape

- **API**: FastAPI (`app/main.py`) — health/readiness, packages, leads,
  audits, proposal drafts, job runner, dashboard summary, comms (disabled).
- **Core (framework-free)**: `config`, `governor` (spend cap), `store`
  (SQLite; managed PostgreSQL is the production target behind the same
  interface), `scoring`, `audit_site`, `proposals`, `comms`, `jobs`
  (durable, idempotent job table with traceable audit log entries).
- **Integration with the existing company**: one-way, read-only import from
  the existing ghostcorpnet agency pipeline (`scripts/import_existing_leads.py`).
  The existing operation (kestrelattice site, Gumroad/Payhip stores, gated
  email pipelines) is never modified by this codebase, per the brief.
- **Specialist-agent model** (brief §4) maps onto job kinds: prospecting =
  import + scoring; inspection = `audit_lead`; sales drafting =
  `draft_proposal`; each job is idempotent, logged, and budget-checked.

## Decisions

- SQLite for Phase 1 local operation: zero cost, zero setup, durable.
  Migration to managed Postgres is a config change when a cloud host is chosen.
- Zero paid APIs: audits use direct fetches of public pages; no search API
  keys, no paid AI calls. The spend governor defaults to a $0 cap.
- CI workflow is documented in `docs/CI.md`; the workflow file itself is
  added when the repo token gains the `workflow` scope (currently the fleet
  GitHub token has gist/read:org/repo only — pushes of `.github/workflows/*`
  are rejected by GitHub).
