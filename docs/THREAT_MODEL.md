# Threat model (Phase 1)

## Assets
Prospect contact data, proposals, audit evidence, provider credentials
(env-only, never in Git), the spend cap, the business's sending reputation.

## Threats and controls
- **Unauthorized API access** → sensitive prospect reads, dashboard data,
  imports, audits, proposal drafts, job execution, and communication routes
  require the owner-only `X-GhostCorp-Admin-Key` header. If
  `AGENCY_ADMIN_TOKEN` is unset, these routes fail closed with HTTP 503;
  missing or incorrect keys receive HTTP 401. Comparison uses
  `secrets.compare_digest`. Health, readiness, and public package pricing
  remain public and do not expose prospect records.
- **SSRF via audit URLs** → scheme allowlist, DNS resolution checked against
  private/loopback/link-local/multicast/reserved ranges, redirects followed
  manually with re-validation, size/timeout/content caps. Tested.
- **Spam / unlawful outreach** → this service sends nothing. Proposals are
  drafts; calling/SMS modules refuse by default and require documented
  consent even when enabled. Suppression (opt-out) list is imported first
  and enforced on insert.
- **Runaway spend** → `SpendGovernor` hard cap, default $0; no paid provider
  is wired. Cap changes are config changes by the owner only.
- **Credential leakage** → secrets only via environment / provider secret
  stores; `.env.example` carries placeholders; `.gitignore` excludes
  `.env` and databases.
- **Duplicate / replayed work** → idempotency keys on jobs; unique email on
  leads; audit log on every mutation.
- **Kill switch** → `AGENCY_PAUSED=1` makes all mutating API endpoints
  return 503; per-feature flags for calling/SMS/payments.
- **Data minimization** → only public business contact data already collected
  by the existing pipeline is imported, with source and collection time.

## Deployment requirement
Set a long random `AGENCY_ADMIN_TOKEN` in the deployment secret store before
using protected API routes. Never commit the token, put it in a URL, or expose
it to browser JavaScript. Prefer a server-side owner dashboard/backend proxy
that attaches the header; rotate the token if it may have been exposed.
