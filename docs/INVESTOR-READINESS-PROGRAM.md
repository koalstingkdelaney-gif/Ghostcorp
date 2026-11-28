# GhostCorp Investor-Readiness Program

**Purpose:** turn GhostCorp from a promising collection of software and VR foundations into a demonstrably useful, secure, revenue-producing company that can withstand independent technical, commercial, financial, and legal due diligence.

**Valuation discipline:** the owner's stated ambition is to build something extraordinary, with a prospective investor mentioning $100 trillion. That figure is an ambition/claim to verify, not a current valuation, funding commitment, or forecast. No valuation is asserted here. Any valuation must be supported by independently verifiable assets, intellectual property ownership, revenue, margins, growth, market opportunity, customer retention, liabilities, and comparable transactions. A $100T valuation would be far beyond normal venture-scale outcomes and must never be represented as likely or guaranteed.

## Rules that govern every phase

- Preserve the existing Ghostcorp backend and ghostcorpnet-site repositories; extend rather than replace.
- Keep paid spend capped at $0 until the owner explicitly approves a specific budget. No automatic upgrades, trials that roll into billing, or cloud overages.
- Keep payments, payouts, customer outreach, calls/SMS, and external financial actions disabled until provider onboarding, legal/compliance review, secure deployment, and explicit authorization are complete.
- Never claim a feature is live because code or a UI exists. Every capability must be labelled SIMULATED, READY, LIVE_VERIFIED, BLOCKED_EXTERNAL_REQUIREMENT, UNAVAILABLE, or ERROR.
- Never fabricate customers, sales, usage, uptime, partnerships, investment interest, assets, or valuation.
- Keep business systems private to the verified owner and explicitly authorized staff. Public VR/game areas must not expose customer, finance, agent-control, or owner data.
- Require independent review for security, accounting, legal structure, and investment documents.

## Program phases and exit evidence

### Phase 0 — Establish the truth
**Work:** inventory repositories, domains, IP ownership, dependencies, licenses, existing products, external accounts, and all implemented features. Re-run tests and CI; identify drift between code, documentation, and deployed behavior.

**Exit evidence:** dated system inventory; reproducible test results; dependency/license inventory; verified domain and repository ownership; public status page that distinguishes code, CI, deployment, and live integrations.

### Phase 1 — Secure and operate the foundation
**Work:** harden authentication and authorization; validate all private API routes; enforce HTTPS and secure cookies; protect secrets; validate worker target hosts; add rate limits and abuse controls; establish durable database storage, encrypted backups, restore drills, monitoring, incident response, and rollback. Resolve SQLite single-instance limitations before horizontal scaling.

**Exit evidence:** independent threat-model review; passing security tests; successful backup-and-restore drill; measured recovery objectives; verified persistent data across restarts; no exposed admin credentials; CI security checks.

### Phase 2 — Make the product genuinely usable
**Work:** finish the owner sign-in and Action Center; fix sign-in end-to-end; connect the VR client to the authenticated backend using short-lived least-privilege sessions; verify Quest browser compatibility, WebXR, controls, performance, reconnects, and accessibility. Keep the private owner business environment separated from public social/game spaces.

**Exit evidence:** owner can sign in and out reliably; unauthorized users cannot access private data or actions; Quest test report with device/browser versions, test cases, defects, and performance measurements; no secrets in client assets.

### Phase 3 — Prove one valuable customer problem
**Work:** choose one narrow product/service from observed customer problems; interview target users; document alternatives and willingness to pay; build a small reliable MVP; test usability and outcomes; price transparently; publish only after QA and owner approval.

**Exit evidence:** customer discovery notes with consent; working demo; documented acceptance tests; customer feedback; independently checkable usage and support metrics. Do not expand into many divisions before one offer is useful.

### Phase 4 — Prove repeatable revenue
**Work:** connect a permitted payment provider in test mode first; implement signed webhook verification, idempotent order handling, refunds, fulfillment, fee accounting, customer support, privacy/retention rules, and tax/accounting records. Launch only after provider approval and owner authorization.

**Exit evidence:** end-to-end test-mode proof; then real customer transactions with receipts and settlement reconciliation; net revenue after fees/refunds; gross margin; repeat purchase/retention; customer acquisition cost; support burden; refund/chargeback rate. Gross sales alone are not proof of a healthy business.

### Phase 5 — Scale what works
**Work:** use measured demand to prioritize infrastructure, model routing, worker pools, database migration, product expansion, and distribution. Add cost ceilings, queue fairness, service-level objectives, capacity tests, and disaster recovery before increasing load.

**Exit evidence:** sustained service reliability; measured unit economics; positive contribution margin where applicable; repeatable acquisition and fulfillment; capacity/load-test reports; no uncontrolled spend.

### Phase 6 — Independent investor due diligence
**Work:** prepare a secure data room containing corporate formation and cap table, IP assignments, domain/repository ownership, contracts, financial statements, tax records, bank/payment reconciliation, customer metrics, security reports, privacy/compliance records, material risks, and a realistic operating plan.

**Exit evidence:** independent legal/accounting review; clean cap table; chain-of-title for all material IP; verified financial records; investor materials reconcile to source records; signed term sheet reviewed by the owner's independent counsel. No one should transfer control, IP, equity, or money based on an informal promise.

## Core operating scorecard

Report these monthly from source systems, with date ranges and definitions:

| Area | Required measures |
|---|---|
| Product | active customers, activation, task success, customer outcome, retention |
| Revenue | gross sales, refunds, fees, net revenue, recurring revenue, concentration |
| Economics | gross margin, contribution margin, acquisition cost, payback period |
| Reliability | uptime, latency, error rate, queue age, recovery time |
| Security | open critical/high findings, patch age, access reviews, backup restore status |
| Delivery | release frequency, change failure rate, escaped defects, support resolution |
| VR | successful sign-ins, Quest test coverage, frame rate, crashes, session duration |
| AI operations | verified task completion, evaluation score, cost per successful task, human override rate |
| Governance | approvals, exceptions, incidents, spend against cap, unresolved compliance items |

Do not publish a metric until its source, calculation, date window, and limitations are documented.

## Current known blockers from repository records

- No production host or live backend URL has been verified.
- Static website routing to the FastAPI backend and secure owner-session bridge remain deployment prerequisites.
- Durable production storage, backups, and restore verification are not yet established on a production host.
- Owner OAuth configuration and live browser sign-in are not activated.
- The agent queue and world-state foundations do not prove that a model worker fleet is running.
- VR/Quest end-to-end testing is not verified.
- No live payment processor, verified customer revenue, or payout integration is established.
- Several repository status entries explicitly say tests have not yet been executed; current CI results must be retrieved before claiming pass status.

## Immediate engineering order

1. Retrieve latest CI runs and run the full backend test suite; fix failures before feature expansion.
2. Audit every private API route and the worker's configured API destination; fail closed on missing auth, unsafe origins, or non-HTTPS remote targets.
3. Reconcile deployment docs so they agree on the database mount path and Docker defaults.
4. Complete owner login and same-origin routing on a staging deployment with durable storage.
5. Add an authenticated, read-only VR health/status panel and test it on the actual headset.
6. Select one customer problem and build the smallest paid product that can be delivered reliably.
7. Only after the above, expand AI workforce autonomy within bounded, auditable permissions.

## Definition of investor-ready

GhostCorp is not investor-ready merely because it has a large VR world, many agents, a large roadmap, or impressive projections. It becomes investor-ready when an independent reviewer can reproduce the product demo, verify ownership, inspect secure operating controls, reconcile revenue and costs, speak with real customers, validate retention and margins, and understand the risks without relying on unsupported claims.
