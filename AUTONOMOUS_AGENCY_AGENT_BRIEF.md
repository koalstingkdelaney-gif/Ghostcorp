# GhostCorp Web Agency — Autonomous Build & Operations Handoff

**Purpose:** This document is the execution brief for the AI coding/operations agent authorized by the repository owner to build and launch a separate, cloud-hosted AI web-development agency.

**Owner intent:** Build a capable, commercially useful agency that finds and qualifies business prospects, designs and builds websites, sells affordable services, takes payment securely, deploys customer sites, and supports them after delivery. The owner wants the work carried out directly in GitHub and connected provider accounts wherever authorized—not another high-level proposal.

## 1. Non-negotiable project boundaries

- This agency is a separate product and codebase. Do **not** merge it into, overwrite, or deploy changes to `kestrelattice`, GhostCorp Revenue Ops Bot, or any other existing project.
- Use this repository as the agency's development home. If the owner later creates/renames a dedicated `ghostcorp-web-agency` repository, migrate deliberately and preserve history.
- The owner works from Android but does **not** want the phone or Termux to host or run production services. Production must run in managed cloud infrastructure.
- Keep external paid API spend at **$0 before the agency earns revenue**. Use free tiers, local/mock providers, and provider-authorized free access first. Enforce a hard configurable spend governor. Never silently incur charges or raise the cap.
- Never put credentials, access tokens, passwords, private customer data, or payment data in Git. Use provider secret stores and environment variables. Never ask the owner to paste passwords, OTPs, card details, or secret keys into chat.
- Do not claim a capability is live unless it is implemented, configured, deployed, and tested end-to-end.

## 2. Target business capability

Build toward an end-to-end web agency with these independently testable capabilities:

1. **Prospect discovery:** Find public business websites and business contact channels using compliant search providers/APIs and public sources. Support advanced search operators where the provider permits them. Do not scrape search-engine result pages in violation of terms, bypass CAPTCHAs, evade access controls, or repurpose restricted datasets.
2. **Website audit:** Inspect public sites for mobile usability, accessibility, performance, broken links, SEO basics, missing calls to action, outdated content, and technical issues. Produce evidence-backed reports and suggested improvements.
3. **Lead qualification:** Score prospects transparently using fit, likely need, service relevance, and available public business information. Store source, collection time, and rationale. Provide deduplication and suppression controls.
4. **Sales workflow:** Create affordable, configurable packages and proposals. Keep pricing editable and test margins before publishing. Do not invent testimonials, clients, case studies, guarantees, or performance claims.
5. **Calling and SMS:** Implement provider adapters (for example, Twilio) only after the owner has completed provider onboarding, identity/business verification, required registrations, consent configuration, and legal review. AI-generated/artificial-voice calls and marketing texts are subject to applicable laws and provider rules. No unsolicited automated marketing calls/texts. Default to disabled; require documented lawful basis/consent, approved scripts, calling-hour controls, caller identification, opt-out/STOP handling, suppression lists, and audit logs. Never infer consent from a public phone number.
6. **Website production:** Generate custom, responsive, accessible, secure, fast websites with real content supplied or approved by each customer. Include SEO metadata, structured data where appropriate, forms, analytics consent controls, and tests. Use a repeatable design system and code quality gates.
7. **Quality assurance:** Run automated tests for desktop/mobile layouts, accessibility, performance, links, forms, security headers, dependencies, and deployment health. Failed QA blocks delivery.
8. **Billing and payments:** Use Stripe Checkout or another owner-approved provider. Collect billing address through the provider's secure checkout/invoice flow. Verify payment with signed webhooks and provider API confirmation; never trust browser redirects or client-supplied payment status. Do not collect card numbers or bank credentials directly. Owner payout/bank details must be entered and verified only in the payment provider's official dashboard.
9. **Delivery and hosting:** Deploy customer websites to managed hosting (Cloudflare Pages or another approved provider), support custom domains and DNS guidance, track deployment status, and provide rollback/backup procedures.
10. **Maintenance and reporting:** Monitor uptime, forms, errors, security updates, backups, performance, and revenue. Provide transparent customer reports and support workflows.
11. **Owner dashboard:** Provide a secure dashboard for leads, audits, proposals, approvals, customers, projects, deployments, payments, costs, and revenue. Enforce role-based access and strong authentication.
12. **Continuous improvement:** Measure conversion, delivery time, defect rate, retention, uptime, and unit economics. Test improvements in a sandbox before production. Never let agents grant themselves broader privileges or remove safeguards.

## 3. Recommended architecture (adapt based on verified constraints)

- **Frontend/dashboard:** Next.js + TypeScript.
- **API/backend:** Python FastAPI with typed schemas and explicit authorization.
- **Database:** Managed PostgreSQL in production; SQLite only for local tests if useful.
- **Background work:** Durable managed queue and idempotent workers.
- **Hosting:** Managed cloud platform with persistent services; Cloudflare Pages for generated customer sites where suitable.
- **Object storage:** Managed object storage such as Cloudflare R2.
- **Payments:** Stripe Checkout, signed webhooks, reconciliation jobs.
- **Voice/SMS:** Provider adapter, disabled until all compliance prerequisites are complete.
- **Search:** Approved search/business-data APIs with documented terms and quotas.
- **Observability:** Structured logs, error monitoring, uptime checks, cost and usage metrics.
- **Secrets:** Managed secret store; least-privilege service credentials.
- **CI/CD:** GitHub Actions with tests, lint, dependency/security checks, deployment approvals, and rollback.

Architecture may change if the selected provider's free tier or deployment model makes another secure option materially better. Record the reason and total costs.

## 4. Agent design and authority model

Use a coordinator with narrowly scoped specialist agents, such as:

- Research/prospecting
- Website inspection and SEO
- Lead scoring
- Proposal and sales drafting
- UX/design
- Frontend engineering
- Backend engineering
- Accessibility/performance/security QA
- Deployment and maintenance
- Billing reconciliation
- Cost and compliance monitoring

Every agent must have an explicit tool allowlist, data access scope, budget, and action policy. Use durable job records, retries, idempotency keys, trace IDs, and human-readable audit logs.

**Autonomy rules:**
- Agents may autonomously research public sources, audit sites, draft proposals, generate code, run tests, and prepare deployments in a sandbox.
- Require owner approval before spending money, increasing budgets, activating paid services, publishing marketing campaigns, making outbound sales calls/texts, accepting legally binding terms, changing payout destinations, issuing refunds, or taking irreversible/high-impact actions.
- Customer-approved routine fulfillment can proceed within the agreed scope and budget.
- Keep outbound communications disabled until lawful consent and provider configuration are verified.
- Provide a global pause/kill switch and per-agent disable controls.
- No self-replication, privilege escalation, credential harvesting, deceptive identities, spam, or evasion of platform limits.

## 5. Security and privacy requirements

- Validate every URL and resolve DNS before crawling. Block loopback, private, link-local, multicast, reserved, and cloud metadata IP ranges. Revalidate after redirects and DNS changes. Limit redirects, response size, content types, timeouts, concurrency, and crawl depth. Prevent SSRF.
- Respect robots.txt, site terms, rate limits, and applicable privacy/data-protection law. Identify the crawler where appropriate.
- Minimize prospect data; record source and collection purpose; define retention and deletion procedures.
- Encrypt secrets and sensitive data in transit and at rest. Use least privilege, secure sessions, CSRF protections, rate limiting, input validation, and audit trails.
- Verify Stripe webhook signatures against the raw request body. Make event processing idempotent and reconcile disputed/missing events.
- Never store raw card data, bank login details, or authentication codes.
- Add dependency scanning, secret scanning, static analysis, and security tests to CI.

## 6. Execution plan — work in small, verifiable increments

### Phase 0 — Inspect and establish the project
- Inspect the entire repository, current branches, workflows, and existing code before modifying anything.
- Preserve existing work. Create a dedicated feature branch if repository state is non-empty.
- Add architecture, threat model, product requirements, environment template, and setup documentation.
- Identify the available GitHub/provider permissions accurately; do not assume access to services not connected.

### Phase 1 — Secure foundation
- Implement backend configuration, health/readiness endpoints, database migrations, authentication/authorization, audit logging, job queue abstraction, cost governor, and feature flags.
- Add unit/integration tests and CI.
- Ensure the service starts locally and in a free/low-cost managed environment without paid AI keys.

### Phase 2 — Prospect intelligence
- Integrate one permitted search source behind an adapter; support mocked fixtures.
- Implement safe crawling and website audit, lead scoring, deduplication, provenance, suppression, and a review queue.
- Test SSRF defenses, robots handling, timeouts, malformed URLs, redirects, and duplicate leads.

### Phase 3 — Website factory
- Build design templates and reusable components.
- Generate customer-specific drafts from approved briefs.
- Add accessibility, responsiveness, performance, SEO, security, and functional QA.
- Preview and test in a sandbox before any customer-facing publication.

### Phase 4 — Sales, billing, and delivery
- Add proposal generation and CRM/project states.
- Integrate Stripe test mode first. Test checkout, signed webhook validation, duplicate events, refunds/disputes handling, invoices, and reconciliation.
- Integrate hosting test deployments and custom-domain workflow.
- Keep production payment and customer deployment activation gated until owner/provider setup is complete.

### Phase 5 — Communications and controlled operations
- Add voice/SMS provider adapters in disabled mode.
- Document and verify required consent, registration, caller ID, opt-out, and compliance controls before enabling any outbound communication.
- Add owner dashboard, approval queue, alerts, monitoring, backup/restore, and operational runbooks.

### Phase 6 — Launch readiness
- Run all tests and security checks.
- Verify deployment, DNS, TLS, health checks, backups, monitoring, payment reconciliation, cost cap, and emergency pause.
- Produce a launch report separating: implemented, tested, deployed, provider-configured, and still blocked.
- Do not describe the agency as fully autonomous or revenue-generating until those capabilities are actually proven.

## 7. Required deliverables

- Working source code in this repository.
- Clear README with architecture, setup, operations, and limitations.
- `.env.example` containing names and safe placeholders only.
- Database migrations and seed/demo data.
- Automated tests and CI workflow.
- Threat model and privacy/compliance notes.
- Provider integration guide and explicit list of required owner-side setup steps.
- Deployment configuration and rollback instructions.
- Owner dashboard and operating runbook.
- A final status report with commit links, test results, deployed URLs (only if verified), provider connection status, and outstanding blockers.

## 8. Definition of done

A feature is done only when code exists, tests pass, security implications are reviewed, configuration is documented, and its status is reported truthfully. A cloud deployment is not proof that payments, calling, texting, search, or revenue collection work. Each provider integration must be tested independently in sandbox/test mode before production activation.

**Start now:** inspect this repository and its permissions; then implement Phase 0 and Phase 1. Continue through later phases without waiting for the owner for routine coding decisions. Stop only for genuine owner-only actions such as identity/KYC verification, accepting provider/legal terms, entering payout/bank information, approving spend above the $0 pre-revenue cap, or authorizing regulated outbound communications.
