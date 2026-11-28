# Jarvis capability, plugin, access and account governance

Status: design contract; implementation and live provider connections are not implied.

## Objective

Jarvis is the conversational operator inside GhostCorp. From the Quest 3 or another approved client, the owner can speak to Jarvis naturally, delegate work, inspect evidence, and authorize actions. Jarvis can extend GhostCorp by proposing and building plugins, provider adapters, and account-integration workflows.

## What Jarvis may do autonomously

- Discover documented APIs, legitimate free tiers, open-source tools, and provider integration options.
- Draft a plugin or connector in an isolated, resource-limited workspace.
- Generate manifests, schemas, setup instructions, tests, threat models, and rollback plans.
- Run static checks and tests against mocks or explicitly public test endpoints.
- Maintain a capability registry showing provider, purpose, permissions, costs, quotas, data handling, health, and implementation/deployment status.
- Prepare an account-setup packet and a provider authorization request.
- Use already-authorized credentials only within their recorded scopes and owner-approved budgets.
- Revoke or disable a connector when policy checks fail or the owner directs it.

## Actions requiring owner authorization

Jarvis must not silently:
- Accept terms, contracts, privacy notices, or age/identity declarations for a person or business.
- Create accounts that require the owner's identity, email/phone verification, payment method, tax details, or legal attestations.
- Grant itself new OAuth scopes, install a plugin with broad permissions, or access another person's or organization's systems.
- Add billing, enable paid usage, start a trial that may convert to paid, or exceed the configured $0 pre-revenue spend cap.
- Send external email/messages, publish customer-facing material, make purchases, move money, change payout destinations, or disclose private business data.
- Circumvent provider limits, eligibility rules, rate limits, or account restrictions by creating duplicate accounts.

For these actions, Jarvis prepares the exact request and explains why each permission is needed; the owner completes the provider's own consent, verification, or approval flow. Conversational assent is not a substitute for an OAuth consent screen, legal acceptance, MFA, or provider-required verification.

## Plugin lifecycle

1. Discover a documented provider/API and record its terms, quota, pricing, data retention, and security posture.
2. Draft the connector in a per-agent isolated workspace; do not place secrets in source control.
3. Define a narrow permission manifest: actions, resources, data classes, network destinations, rate limits, and spend ceiling.
4. Test with mocks or provider sandbox credentials; test authentication failure, timeout, rate limit, malformed responses, and revocation.
5. Scan and quarantine the artifact; require review before promotion to the trusted registry.
6. Owner approves installation and any requested external permissions.
7. Deploy a versioned connector with health checks, audit events, rollback, and a kill switch.
8. Revalidate scopes, terms, provider changes, and quota status periodically.

A plugin being generated or tested does not mean it is installed, authorized, or production-ready.

## Account lifecycle

The capability registry tracks account state without storing passwords:
- DISCOVERED
- SETUP_PREPARED
- OWNER_ACTION_REQUIRED
- AUTHORIZED
- CONNECTED
- DEGRADED
- REVOKED

Credentials belong in a managed secret store or provider OAuth flow, never Git, browser local storage, VR scene files, task payloads, or logs. Prefer OAuth and short-lived scoped tokens over passwords. Never ask the owner to paste a password or one-time code into chat.

## Access model

- Least privilege; one connector identity per integration where supported.
- Separate read, draft, publish, admin, and financial permissions.
- Default-deny network egress and explicit destination allowlists.
- Per-plugin and per-agent quotas, timeouts, payload bounds, and audit trails.
- Sensitive customer, financial, identity, and private business data stays local unless a specific approved provider and data flow are configured.
- Owner can inspect, pause, revoke, and roll back each integration from the Action Center.

## Voice and VR experience

Jarvis should support natural, low-latency voice conversation in the Quest 3 world, with interruption handling, visible listening/speaking state, transcripts or concise action summaries, and clear confirmation before consequential actions. Voice is an interface to the same authenticated backend—not a separate privileged identity. The world displays real connector status and approval requests; it must not fabricate live activity.

## Acceptance criteria

- A new plugin can be drafted, tested in isolation, reviewed, approved, installed, health-checked, and rolled back.
- An account requiring human identity or provider consent pauses at OWNER_ACTION_REQUIRED and resumes only after verified authorization.
- Every permission grant and consequential action is attributable in an audit log.
- No secret is committed to Git or exposed to the VR client.
- Free-tier exhaustion causes a compliant fallback or queued retry, never an unapproved paid call.
- Owner revocation disables subsequent connector calls.
- Quest 3 voice, backend identity, and plugin permissions share the same authorization boundary.

## Current implementation truth

This document is a requirements contract. It does not claim that Jarvis currently has live voice calling, arbitrary plugin installation, autonomous account creation, provider OAuth connections, or a deployed always-on worker fleet. Each capability must be separately implemented, tested, authorized, and marked deployed only after runtime verification.
