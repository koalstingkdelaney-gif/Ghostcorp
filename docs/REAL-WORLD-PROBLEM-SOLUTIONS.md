# Real-world problems GhostCorp can solve

This is a product and engineering backlog, not a claim that every service is
already operational. Items are ranked by customer value, safety, low-cost
feasibility and fit with the existing GhostCorp/Gumroad operation.

## Priority 1 — Protect small-business prospect and customer data

**Problem:** Small businesses often collect lead names, email addresses,
website details and sales notes in tools that are exposed through weak APIs,
shared spreadsheets or public dashboards.

**GhostCorp solution:** Private owner-only lead records, least-privilege
access, audit trails, opt-out suppression, and a clear split between public
status pages and private business data.

**Implementation status:** The backend now applies the existing
`FEDERATION_ADMIN_TOKEN` gate to lead intake/listing, discovery import,
website audits, proposal drafting, job execution and dashboard summaries.
Missing credentials fail closed. Automated access-control tests were added.
This is an API admin gate, not yet the final verified-email owner sign-in.

## Priority 2 — Help local businesses find and fix website problems

**Problem:** A business can lose customers when its website is slow, broken,
hard to use on a phone, unclear about its services, or missing a clear next
step.

**GhostCorp solution:** Evidence-based website checks, prioritized repair
recommendations, a fixed transparent price menu, and customer-approved
implementation.

**Implementation status:** The repository already contains an SSRF-hardened
website audit and proposal-drafting foundations. A live customer workflow,
accessibility test suite, and customer-approved delivery process still need
to be completed. No automatic customer contact is enabled.

## Priority 3 — Stop missed inquiries from becoming lost sales

**Problem:** Small teams miss calls and form submissions while serving
customers or outside business hours.

**GhostCorp solution:** An opt-in inquiry inbox, source/time tracking,
duplicate detection, response-draft suggestions, escalation rules and a
human-approved reply queue.

**Implementation status:** Durable jobs and communications-disabled
adapters exist. A real inbox integration, consent-aware messaging provider,
and owner-reviewed response workflow are not yet connected. No calls or SMS
are sent.

## Priority 4 — Make digital products easier to discover and buy

**Problem:** Independent creators can have useful products but struggle with
product research, descriptions, packaging, release notes and consistent
promotion.

**GhostCorp solution:** Research customer needs, draft useful products and
software, prepare product pages and release assets, route checkout through
the existing Gumroad storefront, then reconcile verified sales and delivery.

**Implementation status:** The existing site links to the GhostCorp Gumroad
store. The backend does not yet verify Gumroad sale events or reconcile
provider fees/refunds/payouts. GitHub can host source code and releases;
Gumroad remains the existing checkout/delivery route. Publication and
customer-facing claims require owner approval.

## Priority 5 — Reduce repetitive back-office work

**Problem:** Small businesses repeatedly perform intake, sorting, research,
drafting, status updates and follow-up preparation manually.

**GhostCorp solution:** A durable queue, role-limited agents, clear task
ownership, retries, reviewable outputs and a visible operations dashboard.

**Implementation status:** Queue, lifecycle and dream-artifact foundations
exist in code. There is no deployed scheduler, connected AI worker fleet or
always-on host yet. Agent output is not treated as verified work until
validated.

## Priority 6 — Prevent unsafe AI-generated files and code from reaching production

**Problem:** AI-generated files can contain malware, secrets, destructive
commands or broken code.

**GhostCorp solution:** Per-agent workspaces, bounded artifact intake,
hashing, quarantine, scanning, owner review and isolated test execution before
any release.

**Implementation status:** Workspace bookkeeping and non-executing artifact
quarantine foundations exist. Malware scanning, hostile-code isolation,
review UI and safe promotion are still missing. Quarantined files are not
declared safe.

## Priority 7 — Protect business data from device loss and accidental deletion

**Problem:** A phone, laptop or database can be lost, damaged or corrupted,
taking customer records and business work with it.

**GhostCorp solution:** Encrypted, verified backups, multiple generations,
off-device storage and documented restore drills.

**Implementation status:** A SQLite backup script and tests exist in the
repository. No production database, encryption recipient or off-host backup
destination has been configured or restore-tested.

## Priority 8 — Keep automation affordable and predictable

**Problem:** AI and hosting costs can consume a small business's cash before
it has reliable revenue.

**GhostCorp solution:** $0 default paid-spend cap, free/local-first execution,
quota tracking, per-task budgets, alerts and owner approval before paid
upgrades.

**Implementation status:** The spend governor defaults to $0 and local model
gateway foundations are disabled by default. No local model host or
always-on free hosting is configured. Free services have quotas and may
change; do not promise unlimited free compute.

## Priority 9 — Make AI work understandable and accountable

**Problem:** Owners cannot safely delegate if they cannot see what the
system did, why it did it, what evidence it used and what still needs approval.

**GhostCorp solution:** An owner action center with task history, evidence,
cost, risk, approval queue, rollback notes and honest live/simulated status.

**Implementation status:** Audit records, build journal, lifecycle state and
owner-reviewed dream artifacts provide backend foundations. The finished
owner dashboard and VR-to-backend authenticated session are not deployed.

## Build order

1. Close and test private-data access (implemented in code; CI verification
   tracked separately).
2. Finish owner sign-in and connect the VR command surface without exposing
   admin secrets in browser code.
3. Complete the website-audit-to-approved-delivery customer workflow.
4. Add lawful, provider-approved discovery and opt-out-safe lead qualification.
5. Connect the existing Gumroad storefront to verified sale/reconciliation
   events; do not add a duplicate checkout provider.
6. Build the owner review queue and validated artifact-to-product pipeline.
7. Add real model workers and scheduling only after a host, quotas, isolation,
   monitoring and $0 spend controls are verified.
8. Add backup destination configuration and a successful restore drill.

## Non-negotiable safeguards

- Never place credentials, payment-card data, customer secrets or owner
  session tokens in public repositories or VR browser assets.
- No outbound contact, public product release, spending, refunds, payout
  changes or production deployment without the required owner authorization.
- Do not infer sensitive traits or use private customer data for dream
  research.
- Distinguish planned, implemented, tested and deployed states in every
  dashboard and public claim.
