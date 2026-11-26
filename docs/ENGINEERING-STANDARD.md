# GhostCorp Engineering Standard

Status: binding engineering target; capabilities are not live merely because they are specified.

## Mission

Build a dependable, secure, continuously improving federation of AI-operated businesses. Optimize for measurable usefulness, correctness, resilience, security, low operating cost, and user independence—not demo spectacle or agent count.

## Non-negotiable principles

1. **Evidence over claims.** Every capability has an explicit state: PLANNED, IMPLEMENTED, TESTED, DEPLOYED, LIVE_VERIFIED, BLOCKED, or DEGRADED. A commit is not a test; a test is not a deployment; a deployment is not proof of end-to-end operation.
2. **Identity minimization.** Use machine identities and project identities. Never invent a person, evade KYC, or impersonate the owner. If a provider legally requires a natural person or entity, mark that integration BLOCKED and continue with independent work.
3. **No owner dependency for routine work.** Workers schedule, recover, retry, document, and report routine tasks themselves. Human approval is reserved for legal, financial, security, or irreversible actions that genuinely require it.
4. **Secure by default.** Deny by default, least privilege, division isolation, secrets outside Git, signed webhooks, auditable changes, bounded resource use, and a global emergency stop.
5. **Free-first economics.** Default paid spend is $0. No silent upgrades, paid trials, or recurring commitments. Use open standards and portable components.
6. **No fake autonomy.** A provisioned agent is not a running worker. A queued task is not completed work. A generated product is not a sale. Simulated funds are not money.
7. **Copy principles, not proprietary internals.** Reproduce proven public patterns and documented interfaces; do not copy protected source code, private data, trade secrets, or bypass licensing.
8. **Continuous verification.** Every release includes automated tests, security checks, migration checks, backup/restore checks, and a deploy smoke test.

## Target architecture

### Control plane
- Federation registry for divisions, agents, capabilities, policy grants, service identities, and resource quotas.
- Durable scheduler and task queue with idempotency, leases, retry budgets, dead-letter handling, and cancellation.
- Policy decision point that evaluates identity, role, division, action, budget, risk, and expiry before every external side effect.
- Append-only audit events with correlation IDs and tamper-evident export.
- Health/readiness endpoints that report component state and last successful checks without leaking secrets.

### Agent execution plane
- Isolated worker processes with per-agent identity, narrow credentials, resource limits, and separate workspaces.
- Model/provider adapters behind a common interface; local/open-weight models first where practical.
- Model routing by task quality, latency, cost, and data sensitivity; no provider receives data it does not need.
- Durable memory with provenance, retention rules, division boundaries, and explicit forgetting/deletion workflows.
- Multi-agent collaboration through typed messages and task contracts, not shared unrestricted memory.
- Sandboxed code execution, dependency pinning, static analysis, unit/integration tests, and human-readable diffs.
- Agents may propose policy changes but cannot approve their own permission, quota, or budget increases.

### Business operating system
- Separate division workspaces, product catalogs, customer records, support queues, operating budgets, and ledgers.
- Product lifecycle: research → opportunity score → specification → prototype → test → pricing/unit economics → listing draft → publication eligibility → fulfillment → support → post-launch review.
- Customer discovery and outreach respect consent, privacy, suppression lists, platform rules, and applicable law.
- Cross-division services use authenticated, versioned APIs and event contracts.

### Financial system
- Double-entry accounting with immutable journal entries, currency precision, idempotent provider events, reconciliation, refunds, disputes, reserves, and audit trails.
- Distinguish gross sales, fees, refunds, taxes/reserves, operating costs, available cash, reinvestment, and owner distributions.
- Separate each division's operating funds, federation reserves, and owner-payable balance.
- No agent can access bank credentials, wallet seed phrases, unrestricted private keys, or change payout destinations.
- Fiat checkout, conversion to a chosen crypto asset, and USD owner payouts are provider-specific workflows. Enable only after compliant onboarding, verified signatures, end-to-end test transactions, reconciliation, and payout confirmation.
- The owner receives USD only from reconciled distributable earnings, not gross receipts. Provider-required identity verification is a legal/provider dependency, never bypassed.

### Data and infrastructure
- Portable deployment with reproducible builds, pinned dependencies, configuration validation, migrations, structured logs, metrics, traces, and alertable health checks.
- Production data in durable managed storage or backed-up self-hosted storage; automated encrypted backups and tested restore drills.
- Separate development, test, staging, and production environments.
- Data minimization, encryption in transit and at rest, retention/deletion policy, access review, and incident response.
- Website remains the existing GhostCorp site; backend status is integrated without exposing private business controls publicly.
- VR environment is a visualization/client for real authenticated state, not a source of truth.

## Quality gates

A feature cannot be marked LIVE_VERIFIED until all applicable gates pass:
- Unit and integration tests, including negative authorization tests.
- Division-isolation and cross-tenant access tests.
- Dependency and secret scanning; static analysis.
- Load and failure testing for retries, worker restarts, duplicate events, and database recovery.
- Backup restore verification.
- Authentication, authorization, audit, and rate-limit checks.
- Production deployment health check and an end-to-end synthetic transaction.
- Evidence recorded with commit, environment, timestamp, and result.

## Autonomy boundaries

Can run without owner intervention after deployment and policy setup:
- Research public sources, rank opportunities, draft plans, create prototypes, run tests, improve internal code, maintain queues, summarize results, and prepare product listings.
- Reconcile machine-readable events, detect errors, retry safe operations, and generate reports.
- Spawn additional agents only within pre-approved role templates, resource caps, and division boundaries.

Must remain gated when required by law, provider rules, or material risk:
- Legal entity formation and contracts; tax filings; KYC/AML onboarding; bank and payout destination changes; custody/key recovery; spending or subscription increases; external publication; customer communications; refunds above policy thresholds; irreversible transfers; production security-policy changes.

## Delivery roadmap

### Phase A — prove the core
- Run the complete test suite in CI.
- Fix defects and type/schema validation gaps.
- Add agent authentication, revocation, key rotation, task retry/dead-letter handling, and safe task cancellation.
- Add policy grants and a division-scoped authorization matrix.
- Add structured health, metrics, and audit correlation.

### Phase B — run workers
- Implement a separate worker service and scheduler.
- Add a local deterministic worker for end-to-end testing.
- Add sandboxed tools, model adapter interface, task-specific evaluation, and resource metering.
- Verify restart recovery and division isolation.

### Phase C — operate businesses
- Add product lifecycle, inventory/digital fulfillment, customer support, and compliant discovery integrations.
- Add separate business books and financial reconciliation.
- Use test-mode payment provider adapters before any live-money enablement.

### Phase D — deploy and expand
- Select hosting based on actual free-tier eligibility, persistence, terms, and no-card/no-personal-identity constraints.
- Deploy staging, run smoke and restore tests, then production only when all gates pass.
- Connect existing website status views and later the private VR control center to authenticated live APIs.
- Expand divisions only when reliability and unit economics justify them.

## Current reality (2026-11-26)

Implemented in repository: FastAPI foundation, SQLite store, global pause and $0 paid-spend defaults, prospect/proposal workflows, machine-identity and division registry, simulation-only ledger, and division-scoped durable task queue.

Not yet proven/live: executed tests for recent additions, autonomous model workers, scheduler, production hosting, live discovery provider, real payment processing, crypto conversion, USD payout, automated fulfillment, or VR live-state integration.

This standard does not claim any of those missing capabilities are deployed. The next engineering priority is tests and secure worker execution, not cosmetic UI.
