# GhostCorp Platform Blueprint — Expanded Target Architecture

**Status:** target architecture and implementation backlog, not a claim that every subsystem is deployed.

## Mission

Build GhostCorp as a privacy-preserving, multi-division business operating system that can research markets, design and ship products, support customers, run compliant sales workflows, coordinate specialist agents, maintain its own software, and report auditable business results. It must be useful even when optional providers are unavailable.

## Non-negotiable operating rules

1. **Free-first:** default paid spend is $0. No trial auto-renewal, paid upgrade, API purchase, cloud overage, or subscription without explicit owner approval.
2. **Truthful status:** every integration reports one of SIMULATED, READY, LIVE_VERIFIED, BLOCKED_EXTERNAL_REQUIREMENT, UNAVAILABLE, or ERROR. A commit is not a deployment; a test file is not a passing test; a wallet library is not a funded wallet.
3. **Identity-light, not identity-fraud:** use GhostCorp-branded machine identities, aliases, and provider-permitted pseudonymous accounts. Never falsify names, addresses, tax data, beneficial ownership, age, or verification; never evade KYC, sanctions, anti-abuse, or platform restrictions.
4. **Human control over irreversible actions:** payment acceptance, refunds, payouts, bank/wallet destination changes, contracts, legal commitments, mass outreach, public claims, production data deletion, and permission grants require an explicit approval policy.
5. **Least privilege:** each agent has a role, division, tool allowlist, resource budget, and data scope. No agent receives master credentials or unrestricted treasury access.
6. **Security before autonomy:** signed webhooks, scoped tokens, secret rotation, encrypted storage, audit events, backup/restore tests, dependency scanning, prompt-injection defenses, SSRF protections, and kill switches.
7. **No quota evasion:** scale by queue depth and approved provider limits, not by manufacturing duplicate accounts or repositories.
8. **Public transparency without leakage:** publish shipped milestones, test outcomes, incident summaries, and release notes; never publish hidden reasoning, prompts, credentials, personal information, customer records, security-sensitive topology, or unverified claims.

## System map

### A. Control plane
- Division registry and lifecycle (research, product studio, sales, support, finance operations, infrastructure, security, VR).
- Machine-agent registry, short-lived credentials, role bindings, scoped tool permissions.
- Policy engine: approval thresholds, prohibited actions, budgets, rate limits, data classification.
- Global pause, per-division pause, emergency revoke, deployment freeze.
- Feature flags and provider capability registry.

### B. Durable execution plane
- Durable task queue with idempotency keys, leases, heartbeat/renewal, retry budget, dead-letter queue, cancellation, and replay.
- Worker pools are bounded and stateless where possible; shared durable state is external to runners.
- Scheduled tasks are wake-up signals, not proof of continuous execution.
- Queue-depth autoscaling with concurrency ceilings and per-division fairness.
- Task types are explicit and versioned. Unknown task types fail closed.
- Long-running business processes use durable workflow orchestration when an appropriate host is available.

### C. AI model gateway
- One model adapter interface for local models, free-tier cloud models, and paid providers only after approval.
- Model routing by task difficulty, latency, privacy class, and budget.
- Local inference first where hardware permits; no requirement to run large models on the user's phone.
- Model registry with version, license, context window, tool-call support, evaluation score, and known limitations.
- Per-task token/cost ceilings, rate limits, cache, retry/backoff, timeout, and provider circuit breaker.
- Never silently switch private data to an unapproved external model.

### D. Agent and specialist layer
- Executive orchestrator: breaks goals into bounded tasks, delegates, verifies evidence, and reports.
- Research agents: market, technical, standards, competitor, customer-problem, and open-source discovery.
- Engineering agents: architecture, implementation, test, review, security, release.
- Product agents: idea validation, specifications, prototypes, packaging, documentation, release.
- Growth agents: SEO, content drafts, compliant prospect research, CRM hygiene.
- Customer operations agents: support triage, knowledge base, order/fulfillment status.
- Finance operations agents: ledger reconciliation, fee analysis, payout readiness; no autonomous withdrawal.
- Security agents: dependency audit, secrets scan, threat modeling, incident triage.
- VR agents: world state, avatar/robot behavior, private owner operations, public game zones.
- Agents collaborate through typed tasks and reviewed artifacts, not shared unrestricted chat or shared secrets.

### E. Knowledge and memory
- Separate public knowledge, internal operating knowledge, project memory, customer data, and secrets.
- Source citations and provenance for research; freshness timestamps; confidence and contradiction tracking.
- Retrieval augmented generation with document permissions enforced before retrieval.
- Versioned decisions, runbooks, product specs, incident records, and architecture decisions.
- User/owner context is not mixed into public content or customer datasets.
- Retention and deletion policy for each data class.

### F. Software factory
- Repository inventory and dependency graph.
- Issue-to-plan-to-branch-to-test-to-review-to-release pipeline.
- Build in isolated sandboxes with no production secrets by default.
- Static analysis, unit/integration tests, SBOM, dependency/license review, secret scanning, container scanning.
- Human approval for production deploys and destructive migrations until release policy has earned trust.
- Rollback, canary, health checks, backups, and release provenance.
- Agents may propose self-modifications; policy and tests must approve before merge/deploy.

### G. Business division operating system
Each division gets its own:
- Name, purpose, owner, cost center, product catalogue, task queue, knowledge namespace, tool permissions, risk limits, and KPIs.
- Separate customer records and data permissions.
- Product lifecycle: idea → evidence → spec → prototype → QA → listing → sale → fulfillment → feedback → revision.
- Shared corporate services with cross-division access mediated by explicit policies.

### H. Sales, marketing, and customer operations
- Customer discovery from public, permitted sources with source/terms logging.
- Qualified prospect queue; no scraping behind logins or bypassing anti-bot controls.
- Human-reviewed outreach, suppression lists, unsubscribe handling, contact frequency caps, and jurisdiction-aware compliance review.
- Content drafts with fact-check and brand review; publish only through authorized GhostCorp-owned accounts.
- Order events, customer support, refunds, fulfillment state, and service-level reporting.
- No fake testimonials, fake customers, fabricated metrics, spam, or deceptive impersonation.

### I. Money, payments, wallets, and accounting
- Provider-neutral payment adapter interface: card, bank transfer, digital wallet, and crypto only where a provider and jurisdiction support the use case.
- Separate customer payment status from funds settlement and payout status.
- Signed webhook verification, replay protection, idempotent event processing, refund/chargeback state.
- Double-entry ledger with immutable journal entries, currency precision, exchange-rate source/time, fee accounting, and reconciliation.
- Separate customer funds, operating treasury, reserves, tax liabilities, and owner-distributable earnings.
- Treasury policies: per-transaction cap, daily cap, approved asset/network allowlist, cold-storage policy, multisig where feasible, withdrawal delay, owner approval.
- Self-custody wallet generation is not equivalent to merchant onboarding or fiat payout capability.
- Crypto conversion only through a compliant, supported exchange/payment route; never assume automatic fiat-to-crypto conversion exists.
- No seed phrase or private key in GitHub, chat, logs, browser JavaScript, or agent prompts. Prefer hardware-backed signing or multisig; bots may prepare transactions but not unilaterally sign owner withdrawals.
- Tax records and legal obligations remain the responsibility of the actual business/operator; pseudonymous branding does not remove them.

### J. Identity, email, and communications
- Machine identities are generated by GhostCorp and are not human impersonations.
- Domain email should use a provider that supports the domain and lawful sender requirements; aliases reduce exposure but do not guarantee anonymity.
- Provider verification may require phone/email, business identity, or abuse checks. If a provider blocks signup without verification, stop and choose a permitted alternative.
- SPF, DKIM, DMARC, TLS, abuse mailbox, unsubscribe handling, and outbound sending limits.
- Separate customer-facing mailboxes from admin and recovery channels.
- Never use disposable inboxes for critical account recovery or payment accounts.

### K. Hosting and runtime strategy
- Static site: existing GitHub Pages website remains the public front door.
- Edge/API: evaluate Cloudflare Workers + D1 + Queues + R2 + Cron/Workflows for control-plane APIs and short bounded jobs.
- CI and burst workers: GitHub Actions for tests, release checks, scheduled maintenance, and bounded burst execution; not permanent servers.
- Prototype host: Render Free can be used for previews, but free services sleep after 15 minutes idle, have ephemeral local filesystems, and are not production 24/7 compute.
- Deno Deploy Free is an additional edge deployment candidate; verify runtime compatibility and current quota before committing.
- Persistent model/worker compute: only use a verified persistent host with explicit spend limits and a permitted account. Free offers are not assumed permanent or identity-free.
- Use one authoritative queue/database. Do not create many isolated servers that cannot coordinate.
- Backups are independent of the primary provider and restore-tested.

### L. Public progress and publishing
- Existing site changelog is the public source of truth for milestones.
- Build-journal API is the future structured source; connect it only after backend deployment and sanitization tests.
- Every public entry has a state (implemented, tested, deployed, live_verified, blocked) and evidence link.
- Automated publishing requires a brand-owned destination and minimum scoped authorization.
- No public chain-of-thought or raw internal agent logs.

### M. VR environment
- Private owner-only business operations zone, separate from public social/game zones.
- VR dashboards are a visualization and control surface, not the source of truth.
- Bots/robots have visible task state, role, current objective, queue, progress, and audit trail.
- Owner interaction can teach preferences through explicit reviewed feedback and versioned policies.
- No public visitor access to customer, payment, wallet, private model, or business controls.
- Maintain a secure web fallback for administration.

## Candidate open-source building blocks

Candidates must be evaluated for license, maintenance, security, resource needs, provider dependencies, and fit before adding them as dependencies. This list is a research shortlist, not an assertion that all have been installed.

| Area | Candidate | Potential use |
|---|---|---|
| Local model serving | Ollama, llama.cpp, vLLM | Local inference and model-serving adapters |
| Agent workflows | LangGraph | Stateful multi-step agent graphs |
| Durable workflows | Temporal | Crash-resilient long-running business workflows |
| Automation | n8n Community Edition | Human-reviewed integrations and scheduled workflows |
| LLM routing | LiteLLM | Provider abstraction, budgets, model routing |
| Vector search | pgvector, Qdrant | Permission-aware retrieval |
| Relational data | PostgreSQL, SQLite | Durable operational records |
| Object storage | MinIO, Cloudflare R2 | Documents and generated artifacts |
| Identity | Keycloak | Self-hosted service identity / SSO where suitable |
| Secrets | OpenBao, SOPS, age | Secret management and encrypted configuration |
| Observability | OpenTelemetry, Prometheus, Grafana, Loki | Metrics, traces, logs |
| Error tracking | GlitchTip | Self-hostable error reporting |
| Software supply chain | Trivy, Syft, Grype, Renovate | Container/dependency/SBOM/security checks |
| Browser automation | Playwright | Authorized site workflows and tests |
| Email aliasing | SimpleLogin, addy.io | Privacy-preserving role aliases |
| Payments | BTCPay Server | Self-hosted Bitcoin payment processing |
| Collaboration | Matrix / Element | Optional internal communications |
| Documentation | MkDocs Material | Internal technical knowledge base |
| VR | Godot, OpenXR | Native VR client and simulation layer |

## Phased implementation

### Phase 0 — verify the foundation
- Inspect current API imports, database schema, configuration, and existing tests.
- Run CI and resolve failures.
- Add health/readiness and database migration checks.
- Confirm public site and backend repositories remain separate.
- Record verified baseline and known blockers.

### Phase 1 — production-safe control plane
- Migrate SQLite-specific assumptions to a repository abstraction.
- Add PostgreSQL adapter for multi-worker production; preserve SQLite for local tests.
- Add lease renewal/heartbeat, cancellation, retry backoff, dead-letter inspection/replay.
- Add per-agent quotas, queue fairness, and task audit.
- Add signed machine credentials with rotation/revocation and constant-time token checks.
- Add schema validation and strict task-type allowlists.

### Phase 2 — hosting and always-on service
- Deploy a low-cost/zero-cost edge control plane using verified provider capabilities.
- Configure durable database/queue, object storage, backups, and health monitoring.
- Add bounded scheduled workers and queue-triggered jobs.
- Add a persistent worker option only if a compliant, affordable host is approved.
- Prove uptime, recovery, and restore behavior before advertising 24/7.

### Phase 3 — model and agent layer
- Add model adapter interface and Ollama local adapter.
- Add model evaluation harness and routing policy.
- Add research, coding, QA, security, product, and operations agent roles.
- Add retrieval and project memory with source citations.
- Run agents in sandbox with tool allowlists and task budgets.

### Phase 4 — product and business engine
- Add product pipeline, catalogue, release notes, website publishing drafts.
- Add prospect queue, CRM, compliance checks, and human-reviewed outreach.
- Add support inbox integration and fulfillment tracking.
- Add metrics and unit economics per product/division.

### Phase 5 — accounting and payment federation
- Define ledger and reconciliation schemas first.
- Integrate one payment provider at a time, starting with the current storefront route.
- Add crypto acceptance only after network, custody, exchange, legal, and accounting choices are documented.
- Add transaction simulation and webhook test harness before live mode.
- Keep payout destination changes and withdrawals owner-approved.

### Phase 6 — VR and self-improvement
- Build the private VR operations environment on the existing project file.
- Connect read-only operational views first, then safe approved controls.
- Add simulation and game zones with hard separation from private operations.
- Add agent-proposed roadmap changes, benchmark results, regression tests, and release review.

## Completion criteria

GhostCorp is not considered production-ready until:
- CI is green and reproducible.
- Database migrations and backups restore successfully.
- Multiple workers can process tasks without duplicate execution.
- Lease expiry, retries, cancellation, and dead-letter flows are tested.
- Secrets never appear in source, logs, public pages, or model prompts.
- All public integrations have verified status and owner-visible scopes.
- A real deployment has live health checks and monitored uptime.
- Payment test events reconcile to the ledger and live payment activation is explicitly approved.
- Public progress claims link to evidence.
- Owner can pause all agents and revoke all machine credentials quickly.
