# GhostCorp distributed compute and community mesh

**Status:** protocol and implementation specification. No contributor fleet, public portal, Meshtastic bridge or external compute worker is deployed by this document.

## Goal

Let GhostCorp discover and recruit willing community contributors and organizations, then use explicitly donated computing capacity for eligible workloads. Contributors retain control of their machines. GhostCorp never commandeers public Meshtastic nodes, free cloud accounts, phones, computers or corporate infrastructure.

## Components

1. **Contributor portal** at `ghostcorpnet.com/compute`: explains workloads, resource limits, data handling, software provenance, opt-in consent, revocation and support.
2. **Open-source node agent**: signed releases, narrow job protocol, resource caps, local pause/stop, transparent activity log, automatic update policy and uninstall instructions.
3. **Coordinator**: durable job queue, worker leases, scheduling, health, capacity accounting, retry and dead-letter handling.
4. **Trust and identity**: per-node credentials, short-lived job tokens, mutual authentication, key rotation, revocation and contributor isolation.
5. **Sandbox**: rootless containers or OS sandbox where available; no host filesystem, credentials, browser profile, payment instruments or inbound network access by default.
6. **Verification**: reproducible tasks, checksums, redundant execution for untrusted results, deterministic validation and provenance.
7. **Policy engine**: workload allowlist, data classification, residency restrictions, resource quotas, contributor terms and $0 paid-spend ceiling.
8. **Partnership pipeline**: discover public programs and contact channels; prepare proposals; track responses; require a human-approved binding agreement or paid commitment.

## Meshtastic's role

Meshtastic is a low-bandwidth LoRa communications layer, not a general-purpose compute substrate. Use it only for small status, alerts, gateway discovery and coordination messages where local radio law and network policies permit. Do not send customer data, secrets, model weights, large jobs or database traffic over LoRa. Use authenticated encrypted internet transport for compute jobs. MQTT bridges must be explicitly authorized and configured by the network operator.

## Eligible workloads

- Public, non-sensitive build/test jobs.
- Open-source dependency and licence analysis.
- Synthetic benchmarks and simulations.
- Public dataset transformation where licence permits.
- Redundant verification and non-sensitive research tasks.
- Contributor-selected idle compute with hard CPU, RAM, disk, bandwidth and time ceilings.

## Prohibited by default

- Arbitrary model-generated shell scripts.
- Access to contributor personal files or credentials.
- Crypto mining, stealth persistence, traffic relaying for unknown third parties, proxying, spam, credential harvesting or unauthorized scanning.
- Customer personal data, payment data, secrets, private source code or confidential business data on untrusted community nodes.
- Workloads that evade provider limits or terms.

## Contributor lifecycle

1. Discover a public program or voluntary contributor.
2. Explain exact resource use and data flow before installation.
3. Contributor installs and explicitly enrolls the node.
4. Node remains `PENDING` until policy checks and enrollment complete.
5. Issue a scoped credential once; store only a hash server-side.
6. Assign allowlisted tasks under hard resource limits.
7. Record heartbeats, task provenance, resource use and results.
8. Allow immediate pause, credential revocation and uninstall.
9. Delete contributor data under the published retention policy.

No automated account creation, fake identity, free-trial cycling, bypassing CAPTCHAs, accepting terms, or spending. Corporate infrastructure is used only under a documented agreement and explicit authorization.

## Integration with current GhostCorp foundation

The existing backend already has a division registry, machine identities, a durable division-scoped task queue, leases, retries and dead-letter handling. These are useful foundations, but current machine agents are provisioned identities, not an operating compute fleet. The current API has no public contributor enrollment, resource attestation, sandbox runner, workload scheduler, Meshtastic bridge or production host.

## Delivery sequence

1. Implement contributor records and consent versioning; all new nodes default to pending.
2. Add admin review, revocation, scoped node credentials and heartbeat.
3. Add resource declarations and health/capacity telemetry with strict bounds.
4. Add allowlisted, non-sensitive job types and deterministic result verification.
5. Build the public contributor portal and downloadable signed agent.
6. Add optional Meshtastic gateway adapter for small messages only.
7. Add corporate partnership discovery and a proposal queue.
8. Conduct independent security review and contributor pilot before accepting real workloads.

## Acceptance criteria

- A contributor can see and stop every GhostCorp process.
- No node receives a job before explicit enrollment and approval.
- No arbitrary code executes outside the defined sandbox.
- A revoked node cannot claim new work.
- Resource ceilings are enforced locally, not just requested by the server.
- Untrusted compute cannot read customer records, credentials or private memory.
- Meshtastic traffic contains no sensitive payloads.
- Free-tier or donated capacity never silently upgrades to paid capacity.
