# GhostCorp foundation architecture

**Status:** architecture baseline; individual components carry their own implementation and deployment status. This document does not imply that hosting, workers or integrations are live.

## System shape

GhostCorp is one platform with a website gateway, a VR operating console, a persistent backend control plane, independently deployable services, durable storage, and optional contributor-operated edge nodes.

### 1. Experience and access plane
- Existing domain remains the canonical entry point.
- Public site, private owner console, VR headquarters and contributor portal are separate access surfaces.
- Authentication is centralized; each service receives scoped identity, not shared passwords.
- Public VR/social spaces are isolated from private business operations.

### 2. Control plane
- Service registry and capability catalogue.
- Agent and division identity registry.
- Durable task queue with idempotency, leases, retry and dead-letter handling.
- Approval queue and policy evaluation.
- Resource inventory, health and capacity reporting.
- Global pause switch and owner override.
- Audit log and deployment inventory.

### 3. Execution plane
- Local browser inference in VR when hardware supports it.
- Persistent hosted workers for 24/7 tasks when an always-on host exists.
- Contributor workers only after explicit opt-in and review.
- Sandboxed build/test workloads with local resource enforcement.
- No arbitrary model-generated shell execution.

### 4. Data and memory plane
- Durable source-of-truth records.
- Vector index for semantic recall.
- Knowledge graph for relationships and provenance.
- Event/episodic memory for agent actions and outcomes.
- Summaries and deduplication as derived indexes; never destroy original records to save space.
- Retention, export, deletion, encryption and backup policies.
- Memory tiers: hot cache, operational database, vector index, archival object storage.

### 5. Communications plane
- Authorized email provider connection with persistent OAuth/token refresh where supported.
- Templates, recipient suppression, delivery events and audit history.
- Meshtastic only for low-bandwidth, non-sensitive alerts and coordination.
- Authenticated TLS transport for actual business data and compute jobs.
- No spam, scraping of private communities or use of public radio nodes without operator permission.

### 6. Distributed infrastructure plane
- Discover providers and programs using public documentation and approved APIs.
- Compare quotas, terms, uptime, persistence, CPU, RAM, storage and egress.
- Contributor enrollment, transparent terms, explicit consent, local pause/stop and immediate revocation.
- Signed agent releases, scoped credentials, resource ceilings and workload allowlists.
- Corporate compute requires written permission and documented scope.
- Free-tier availability is best-effort; no provider is treated as guaranteed 24/7 capacity.

### 7. Business plane
- Research, products, marketing, sales, CRM, support, commerce, fulfilment and analytics.
- Finance ledger, budgets, reconciliation and payout queue.
- Provider-managed payments; no custody of customer card credentials.
- Owner approval for spending, payouts, bank changes, binding contracts, sensitive outreach and production releases until standing authorization is deliberately configured.

### 8. Security and trust plane
- Least privilege, service identities and short-lived credentials.
- Secrets stored only in deployment secret stores.
- Encryption in transit and at rest.
- Input validation, SSRF protection, dependency and license checks.
- Threat modeling, vulnerability triage, incident response and recovery exercises.
- Untrusted compute gets synthetic/public workloads only; no customer PII, private source or secrets.

### 9. Reliability plane
- Health/readiness checks and dependency monitoring.
- Backups with restore tests.
- Job retry and dead-letter inspection.
- Provider outage handling and degraded modes.
- Deployment rollback and version pinning.
- Uptime claims require independent monitoring from the deployed host.

## Resource isolation

The website must not share an unbounded process or resource pool with model inference. Apply hard ceilings and separate queues for:
- website/API request handling;
- VR asset delivery and session services;
- model inference;
- background agents;
- database and memory indexes;
- contributor workloads.

If hosting does not expose enforceable CPU/RAM quotas, isolate services across separate free-tier services or processes where available. If quotas are exhausted, pause low-priority work; never silently buy capacity.

## Capability contract

Every module must publish:
- stable capability ID and version;
- owning department and responsible agent role;
- input/output schema;
- permission class and data classification;
- execution target and resource ceiling;
- idempotency and retry behavior;
- audit event schema;
- tests and acceptance criteria;
- dependencies and failure mode;
- implementation lifecycle status.

## Deployment truth

A GitHub commit is source code, not a running service. A domain is an address, not compute. A VR world is an interface, not inherently an always-on server. Persistent operation requires an always-on runtime supplied by a hosting provider or a consenting contributor. The current project has no verified production host or 24/7 worker fleet.

## Delivery gates

1. Make the existing API start reliably and pass CI.
2. Establish secure owner authentication and secret management.
3. Deploy a minimal always-on backend within a confirmed free quota.
4. Connect VR to authenticated status and task APIs.
5. Implement persistent memory and backups.
6. Implement local model inference proof-of-concept and test on Quest.
7. Build a safe software factory and sandbox.
8. Complete contributor portal, worker sandbox and security review before running external jobs.
9. Add Meshtastic adapter for low-bandwidth messages.
10. Connect email provider with persistent authorization and policy-bounded sending.
11. Complete business workflows, finance ledger and payment-provider onboarding.
12. Add independent monitoring, recovery tests and staged rollout.

## Non-negotiable operating policy

- Paid spend remains $0 unless explicitly changed by the owner.
- Never create accounts, accept terms, bypass verification or use third-party infrastructure without permission.
- Agents may autonomously research, draft, classify, test and execute bounded sandbox work.
- External side effects must be authorized by a provider-supported standing permission or explicit approval.
- Every action must be attributable and reversible where technically possible.
