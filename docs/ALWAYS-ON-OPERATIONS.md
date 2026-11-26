# Always-On Operations and Worker Fleet

Status: architecture and public progress journal committed 2026-11-26. No hosted worker fleet is deployed by this document.

## What "24/7" means

GhostCorp should be available continuously, with durable work surviving gaps between worker executions. A worker does not need to run continuously for every task: the queue persists tasks, and scheduled or event-triggered workers claim them when compute is available. For latency-sensitive operations, a continuously running host is required.

## GitHub Actions role

Use GitHub Actions as a free-first CI/CD and burst-worker layer where repository visibility, current plan allowances, terms, and usage limits permit:
- Run tests on every code change.
- Run short scheduled maintenance and queue-drain jobs.
- Launch bounded parallel worker jobs using a matrix or reusable workflow.
- Publish build status and release evidence.
- Use a single shared queue and idempotency keys so staggered runs never duplicate side effects.

GitHub-hosted runners are ephemeral job environments, not permanent servers. Current GitHub documentation states hosted jobs have a six-hour execution ceiling, scheduled workflows have a five-minute minimum interval, and standard hosted runner concurrency on GitHub Free is 20. Included compute and storage are limited; limits can change. Do not create extra accounts or repositories to evade quotas or billing.

## Fleet topology

- One authoritative control plane and durable database.
- One scheduler that writes due work into the queue.
- N bounded worker slots, each a separate ephemeral runner job.
- Every worker authenticates with a machine identity and claims a lease for one division and role.
- A worker renews its lease while active; expired leases return work to the queue.
- Completion is idempotent and emits an audit event.
- Workers never use local disk as authoritative shared state.
- Backpressure, max attempts, dead-letter queue, per-division concurrency, and global kill switch prevent runaway loops.

Do not deploy the maximum number of runners just because it is technically possible. Scale to measured queue depth, throughput, failure rate, and available free compute. The target is reliable service, not idle runner count.

## Staggered schedule and synchronization

- Use scheduled jobs as wake-up signals, not as the source of truth.
- Stagger queue-drain jobs to reduce start-time collisions.
- Use database leases and a single authoritative clock; never assume cron starts exactly on time.
- Use UTC internally, store timestamps, and tolerate delayed or missed schedules.
- Reconcile queue state at each wake-up; recover expired leases.
- Use event triggers for immediate work where available.
- If a strict 24/7 process is required, move the scheduler/control plane to a persistent host that meets the identity-light/free-tier requirements. GitHub Actions alone cannot promise an always-running process.

## Public process publishing

The public build journal endpoint is:
- `GET /api/public/build-journal`: read sanitized entries.
- `POST /api/build-journal/publish`: authenticated publication using the existing federation admin token.

Publish only approved engineering facts: milestone, release, test, resolved incident, or research. Never publish private prompts, customer information, secrets, credentials, personal identity, internal URLs, raw logs, or unreleased security details. Mark a feature "tested" only after tests actually ran; "deployed" only after deployment; and "live_verified" only after end-to-end verification.

The journal is an API-backed publishing foundation. It is not yet wired to a scheduled publisher or a social-media account. Social posting should use a GhostCorp-owned brand identity and documented platform APIs, never the owner's personal identity or scraped automation.

## Deployment gates

Before enabling any scheduled production worker:
1. Confirm repository visibility, GitHub Actions permissions, plan limits, and remaining included minutes.
2. Add least-privilege workflow permissions and pin third-party actions to immutable commit SHAs.
3. Run CI and security checks; tests must pass.
4. Configure durable storage, backup/restore, and monitoring.
5. Configure machine credentials as encrypted runtime secrets; no secrets in source.
6. Add concurrency groups, timeouts, cancellation, rate limits, and a global pause.
7. Deploy staging and verify queue claim, lease expiry, completion, and duplicate delivery.
8. Confirm the worker cannot cross division boundaries or increase its own quota.
9. Publish a truthful deployment status with evidence.

## Current verified state

Implemented in source: machine-agent registry, division-scoped durable task queue, task claim/complete endpoints, sanitized build-journal storage, public read endpoint, admin-protected publish endpoint, and test files.

Not yet verified: execution of the newly added tests, workflow-file deployment, a live scheduler, hosted workers, shared production database, 24/7 uptime, public website integration, or social publishing. The connected GitHub repository integration previously reported that its token lacked the workflow permission needed to modify Actions workflow files. Therefore no GitHub Actions deployment is claimed here.
