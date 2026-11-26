# Identity-Light GhostCorp Federation

Status: implementation specification; not a claim that services are deployed.

## Objective

Build GhostCorp so routine operation does not depend on the owner's personal identity, daily attention, phone being online, or a paid API subscription. Prefer software and providers that permit project, organization, or service identities and free/open-source operation.

## Selection rules

1. Prefer self-hostable, open-source components and public standards.
2. Prefer project/service identities over personal identities where the provider permits them.
3. Do not submit false identity details, impersonate a person, evade KYC, or bypass provider terms.
4. If a provider requires a verified natural person, legal entity, payment method, or contract signer, mark that integration `BLOCKED_EXTERNAL_REQUIREMENT` and continue with an eligible alternative.
5. Do not make a feature appear active until an end-to-end health check proves it.
6. Never put credentials, wallet seed phrases, private keys, bank details, or tokens in Git, browser code, logs, agent prompts, or chat.
7. Free-tier limits are hard limits. Do not silently upgrade, incur charges, or create paid commitments.

## Components that can be developed without personal financial identity

### Federation core
- Agent registry with stable machine identities and narrowly scoped roles.
- Per-agent workspaces, task queues, durable job IDs, heartbeats, and audit events.
- Business/division registry with isolated data namespaces and service-to-service authentication.
- Policy engine with deny-by-default permissions, rate limits, kill switch, and bounded resource quotas.
- Event bus and API contracts for cross-division collaboration.
- Local development and test fixtures that require no external account.

### Public website and code delivery
- Continue using the existing GhostCorp website repository and GitHub Pages deployment path.
- Build the control-plane UI as static assets and read-only status views first.
- Use repository automation only where the connected GitHub permissions permit it.
- Do not claim a cloud worker or backend is live until deployment and health checks succeed.

### Runtime and storage
- Design adapters for self-hosted SQLite/PostgreSQL, object storage, and scheduled workers.
- Keep local/test mode fully functional with SQLite and mock providers.
- Prefer a free, no-card tier only after confirming current provider eligibility and limits.
- Make the runtime portable so it can move between eligible hosts without rewriting agent logic.
- A GitHub Pages site is static hosting, not a continuously running agent backend. A separate persistent runtime is required for always-on agents.

### Agent email and business identities
- Use internal agent IDs and role addresses in the system before provisioning external mailboxes.
- Use domain aliases or provider-supported service mailboxes only where account terms permit them.
- Agents may draft, classify, and route messages internally; outbound messaging must respect consent, anti-spam law, provider policy, and suppression lists.
- A legal company identity is not interchangeable with an agent alias. Do not fabricate legal entities or claim an agent is a legal owner.

### Wallets and treasury
- Implement a provider-neutral ledger first: pending, settled, available, reserved, spent, refunded, disputed, and reconciled balances.
- Support testnet and simulated wallets without personal identity or real funds.
- For real crypto, use documented non-custodial wallet software and a key-management boundary; agents must never see seed phrases or unrestricted private keys.
- Use per-business wallet addresses and auditable transfers; separate business funds from owner distributions.
- Real fiat checkout, fiat-to-crypto conversion, exchange access, and USD bank payouts are provider-dependent. They remain disabled until a compliant provider supports the required flow and its onboarding requirements are met.
- Never treat a checkout redirect, webhook without signature verification, or unconfirmed blockchain transaction as settled revenue.

### Autonomous product operations
- Agents can research public information, generate product concepts, build prototypes, run tests, prepare listings, and calculate unit economics in isolated workspaces.
- Publishing, outbound campaigns, purchases, subscriptions, and external commitments require a policy grant with a hard budget and expiry; if no valid grant exists, prepare a draft rather than execute.
- Track gross receipts, fees, refunds, chargebacks, taxes/reserves, operating costs, and net contribution separately.
- Reinvestment is allowed only from reconciled, available funds within a pre-existing budget. An agent cannot raise its own budget or move owner distributions.

## Required runtime states

Every integration must report one of:
- `SIMULATED`: test data only; no external service or real funds.
- `READY`: credentials/configuration exist and preflight passed, but no live action has been proven.
- `LIVE_VERIFIED`: a real end-to-end test passed with evidence and timestamps.
- `BLOCKED_EXTERNAL_REQUIREMENT`: provider requires an external identity, authorization, or contract step.
- `UNAVAILABLE`: provider or capability is not supported.
- `ERROR`: last health check or operation failed.

## Build order

1. Agent registry, business/division registry, policy engine, durable queue, audit log, and status endpoint.
2. Persistent runtime adapter and backup/restore tests.
3. Provider-neutral ledger and simulated payment events.
4. Non-custodial testnet wallet adapter and transaction verification.
5. Product build/test/catalog/fulfillment pipeline.
6. Eligible free-tier hosting and scheduled execution adapters.
7. Provider integrations only when they pass the identity-light selection rules.
8. VR visualization connected to live API state, not fabricated animations.

## Acceptance criteria

- A clean install runs in local mode with no personal identity, payment card, or API key.
- Agents have machine identities and cannot read another division's secrets or ledger.
- The system survives process restarts without losing queued jobs or audit history.
- A kill switch stops new external actions without deleting data.
- Simulated checkout and wallet flows reconcile correctly, including duplicate events, refunds, and failed transactions.
- Status pages distinguish simulated, ready, live-verified, blocked, and failed components.
- No external provider, live payment, or revenue claim is made without end-to-end evidence.

## Current limitations

This document does not deploy a server, create provider accounts, provision a domain mailbox, generate a production wallet, or activate payment rails. Those are separate implementation and verification steps.