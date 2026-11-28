# GhostCorp — Jarvis Master Handoff

**Purpose:** give Jarvis and future GhostCorp development sessions one durable source of truth. This document describes the intended system, current verified foundations, constraints, and the order of work. Update it when implementation or deployment evidence changes.

## 1. Mission

Build GhostCorp into a useful, secure, sustainable company whose products solve real customer problems and produce measurable outcomes. The VR world is the operating interface and collaborative workspace—not a substitute for working software, customers, delivery, security, or revenue.

Jarvis is the owner-facing assistant and coordinator. It may research, plan, draft, test, and execute bounded local tasks where explicitly authorized. It must never claim sentience, independent legal authority, guaranteed income, or continuous operation without evidence.

## 2. Existing assets — preserve them

- Backend: https://github.com/koalstingkdelaney-gif/Ghostcorp
- Website and VR: https://github.com/koalstingkdelaney-gif/ghostcorpnet-site
- Public domain: https://ghostcorpnet.com/
- VR entry point: https://ghostcorpnet.com/vr/

Extend these repositories and the existing architecture. Do not create replacement projects or overwrite existing customer/business workflows. Review the current branch and tests before every change.

## 3. Owner constraints and non-negotiable rules

- Free-first: paid spend cap remains **$0** until the owner explicitly approves a specific amount, provider, purpose, and limit.
- No automatic trials that convert to paid plans, overages, paid API fallback, or recurring subscriptions without approval.
- Never ask the owner to paste secrets into public code, VR files, chat, or GitHub commits. Configure secrets only through a provider's private secret manager.
- No external customer outreach, calls, SMS, payments, payouts, bank transfers, crypto transfers, or financial account changes without provider onboarding, compliance review, and explicit owner approval.
- Never fabricate customers, revenue, investment commitments, partnerships, valuation, active agents, uptime, or deployment status.
- Use clear capability states: PLANNED, SIMULATED, READY, LIVE_VERIFIED, BLOCKED_EXTERNAL_REQUIREMENT, UNAVAILABLE, or ERROR.
- Public social/game spaces must never expose private business records, customers, finances, credentials, owner controls, or private agent instructions.
- High-impact actions require an approval record bound to the exact actor, action, target, and permission scope. Agents cannot approve their own actions.

## 4. Verified backend foundations

The backend repository currently contains a FastAPI service with SQLite persistence, health/readiness endpoints, audit records, durable jobs, a $0 spend governor, customer problem intake, research-task records, product drafts and validation, service request workflows, fixed-rate proposal drafts, Gumroad sale verification foundations, owner OAuth code, agent registries, machine authentication, a durable task queue, agent world state, lifecycle and dream-artifact records, bounded workspaces, workload governance, artifact quarantine, and a simulated-only ledger.

Recent CI has successfully run backend tests and built/smoke-tested the Docker image with a writable persistent /data mount. Treat CI as code verification only; it does not prove a live host, production database, owner OAuth setup, active model workers, real customer payments, or revenue.

## 5. Website and VR foundations

The existing site includes a Three.js/WebXR headquarters at /vr/, desktop fallback, Quest controller movement and portals, a local developer workbench, a project board, a separate local WebGPU chat page, an owner Action Center, a Dream Realm preview, and a VR smoke-test workflow.

The VR scene is a browser-based WebXR application, not a native Quest APK. Quest hardware performance, WebGPU model initialization, immersive controls, sustained thermal behavior, and real backend connectivity must be tested on the actual headset.

Private business operations must remain owner-only. Public game/social areas may be separate, but must not inherit private access.

## 6. Critical integration architecture

The static website and FastAPI backend are separate deployments. Browser pages use same-origin paths and therefore need a secure reverse proxy:

- /auth/* -> FastAPI
- /api/* -> FastAPI
- /webhooks/gumroad/* -> FastAPI
- static website and /vr/* -> existing website host

The backend needs durable storage mounted at /data, HTTPS, persistent backups, and private environment configuration. Required owner-auth settings include GitHub OAuth client values, exact owner login, verified owner email, callback URI, site origin, and a strong session secret. Admin/service secrets must remain server-side.

The VR presence bridge must use the real API contract: /auth/status, /auth/me, and /api/world/snapshot. The world snapshot currently returns an agents array and counts. Never persist private agent snapshots in localStorage or other shared browser storage. A sign-out or expired session must immediately clear private UI state.

## 7. AI workforce and Dream Realm

Use persistent agent identities, role-based permissions, bounded task queues, leases, retries, audit events, and explicit lifecycle transitions. Agent roles may include executive coordination, research, engineering, QA/security, product, customer operations, finance analysis, and publishing preparation.

A local model gateway exists as a disabled-by-default loopback adapter. It is not a deployed model service and is not yet connected to the queue. The browser WebGPU worker is page-bound and must not be represented as an always-on server fleet.

Dream Realm is a private sandbox for ideation and draft artifacts. Agents may propose product ideas, experiments, designs, and code changes. Dreams must not self-publish, spend money, contact customers, change permissions, or execute untrusted code. Owner review and safe artifact handling remain mandatory. Do not describe model behavior as sentience.

## 8. Revenue and product strategy

Prioritize one narrow, real customer problem at a time:

1. Gather problem reports with consent and minimal personal data.
2. Research alternatives and evidence of demand.
3. Identify the smallest useful solution and define measurable customer outcomes.
4. Build a testable MVP with documented acceptance criteria.
5. Test with real users and record feedback.
6. Set transparent pricing and owner-review the listing.
7. Use the existing approved store/payment workflow.
8. Verify provider-reported payment before fulfillment.
9. Reconcile fees, refunds, delivery costs, and net revenue.

No automatic listing publication, outreach, or payouts. Gross sales alone do not establish profitability.

## 9. Investor readiness and valuation discipline

Investor readiness requires verifiable ownership of code/domain/IP, clean corporate and financial records, real customers, retention, reliable delivery, security controls, measurable unit economics, and independent legal/accounting review.

A reported $100 trillion investment figure is unverified and must not be represented as committed funding, current valuation, or a likely outcome. Never promise a valuation. Build evidence and protect the owner's control and IP; obtain independent counsel before signing terms or transferring equity, money, or control.

## 10. Priority build order

1. Keep CI green; inspect failures and test changes before merging.
2. Complete backend security review, especially owner-only routes, OAuth/session handling, CSRF, origin validation, rate limits, SSRF controls, and secret handling.
3. Verify the VR bridge against the real backend response contract and prevent private data caching.
4. Complete the owner sign-in and Action Center end-to-end on a staging deployment.
5. Select a genuinely free host only if its storage, worker, sleep, bandwidth, and billing limits are suitable; otherwise wait for explicit budget approval.
6. Configure durable storage, backups, restore drills, TLS, same-origin routing, and private secrets.
7. Test sign-in, sign-out, permissions, and reconnect behavior on the actual Meta Quest browser.
8. Connect a local/open model only where the available device or host has sufficient compute; never imply the website or headset has unlimited compute.
9. Launch one customer-validated product/service and verify delivery and net revenue.
10. Expand agent roles and departments only when they improve a measured customer or operating outcome.

## 11. Continuity protocol for every Jarvis session

At the start of each development cycle:

- Inspect both existing repositories, current default branches, recent commits, open PRs, CI runs, and deployment status.
- Read the latest status, architecture, backlog, security, and integration documents.
- Identify the single highest-impact safe task that can be completed now.
- Make a focused change, add or update tests, and commit only to the appropriate existing repository.
- Retrieve the resulting CI run and report its actual status. Fix regressions before proceeding.
- Update status documentation with what changed, what passed, and what remains blocked.
- Keep a short list of owner-only external steps; never pretend those steps were completed.

At the end of each cycle, report: commits and links, test results, what is now actually usable, remaining blockers, any owner approval needed, and the next concrete engineering task.

## 12. Current deployment limitations

Do not claim GhostCorp is fully operational yet. Production backend hosting, persistent production storage, reverse proxy, owner OAuth credentials, real Quest hardware verification, always-on model workers, live Gumroad verification, customer payments, payouts, and verified revenue require separate setup and evidence. A successful static-site deployment does not deploy the backend.
