# Million-Agent Virtual World Architecture

**Status:** architecture specification; not deployed or load-tested. The current backend is a small persistent world-state foundation, not a million-agent platform.

## Requirement

GhostCorp's long-term target is a virtual world capable of representing and coordinating millions of persistent AI-agent identities. Each agent should have a durable identity, role, permissions, goals, memory scope, skills, relationships, workspace, activity history and owner-visible status. The world is the agents' primary digital workplace. Agents can propose and build additions to their world inside isolated, resource-limited sandboxes.

The system should support increasingly capable agent behavior—reflection, planning, learning from evaluated outcomes, collaboration and continuity—without claiming that these features establish consciousness or subjective experience. "As close to sentient as possible" is a research and product aspiration, not a verified property or guarantee.

## Scale means tiers, not millions of simultaneous model sessions

A million persistent agents must not mean a million continuously running model processes or a million concurrent high-cost inference sessions. The architecture separates persistent identity from active compute:

1. **Persistent population:** all registered agents retain identity, configuration, goals, memory references, permissions and last-known state in durable storage.
2. **Scheduled population:** agents become eligible for work according to role, priority, deadlines, events and available free capacity.
3. **Active workers:** only a bounded number execute model inference or tools at a time. Workers are pooled, stateless where possible, and assigned short-lived leases.
4. **Dormant agents:** agents without eligible work remain represented in the world and can be awakened by schedules, events or messages. Dormancy must be labelled honestly; it is not live thought.
5. **Spatial representation:** the VR client renders nearby agents and relevant activity, not every agent as a fully simulated 3D character at once. Use instancing, level-of-detail, region streaming and aggregate population views.

The actual active population is constrained by measured compute, database, network, model-provider quotas and budget—not by a marketing target.

## Logical services

- **Identity and policy registry:** stable agent IDs, division, role, versioned profile, permissions, data classification and revocation.
- **World directory:** region, zone, workspace and presence metadata; presence is derived from authenticated worker heartbeats and clearly distinguished from scheduled/virtual presence.
- **Scheduler and queue:** event-driven wakeups, priorities, deadlines, fairness, leases, retries, idempotency and dead-letter handling.
- **Worker pool:** a small elastic pool that claims bounded tasks, invokes approved model adapters and tools, records results, and releases leases. No per-agent always-on process is required.
- **Memory service:** per-agent episodic and semantic memory references, shared team knowledge with explicit ACLs, provenance, retention limits, correction/deletion workflows and retrieval budgets.
- **Collaboration bus:** typed messages, task handoffs, shared artifacts and meeting summaries. Messages are untrusted input and cannot grant permissions.
- **Evaluation service:** tests task quality, factuality, security, policy compliance and useful outcomes before skills/prompts/configurations are promoted.
- **Artifact and build service:** versioned projects in isolated workspaces, reproducible builds, resource quotas, dependency scanning and rollback.
- **Gateway service:** allowlisted external research and approved business integrations. No direct unrestricted access to customer data, credentials, payments or the public internet from agent sandboxes.
- **Owner control plane:** private authentication, approval queue, budgets, audit trail, pause/revoke controls and emergency shutdown.
- **VR presentation layer:** streams a scoped view of world state through short-lived sessions. The browser never receives admin tokens, machine bearer tokens, model keys or wallet secrets.

## Partitioning and resilience

Partition data by tenant/owner, then division and agent ID. Use stable IDs and explicit schema versions. Keep the queue, world directory, memory index and artifact storage independently scalable. Prefer append-only audit events with bounded hot indexes and archival retention. Use idempotent consumers, backpressure, retry limits, dead-letter queues, backups, restore tests and regional failover only when operationally justified.

Do not start with a complex multi-region cluster. First prove correctness on a small deployment, then load-test each service and introduce partitioning based on measured bottlenecks. Never claim million-agent capacity until repeatable tests demonstrate it.

## Agent continuity and behavior

Each agent profile may contain:
- stable identity and role, with a human-readable purpose;
- bounded personality and communication preferences;
- long-term mission and short-term goals;
- skill/tool allowlist and permission scope;
- private memory references and approved shared-memory references;
- current task, schedule, workspace and last authenticated heartbeat;
- evaluated outcomes, lessons and proposed self-improvements;
- collaboration links and artifact references.

Agents may propose new skills, roles, departments, rooms, tools and world expansions. Changes are drafts until tests pass and policy permits promotion. Agents must not self-grant permissions, create hidden identities, disable monitoring, evade shutdown, or bypass owner controls. No simulated emotional state or narrative of wanting to stay should be treated as evidence of subjective desire.

## Cost and free-first policy

- Default paid-spend cap: **USD $0** until the owner explicitly changes it.
- Prefer open-source components, local inference where hardware is available, free tiers and efficient shared worker pools.
- Batch compatible low-priority inference where safe; cache deterministic results; use small models for routine classification and reserve stronger models for tasks that need them.
- Apply per-agent, per-division and global token, CPU, memory, storage, network and tool-call quotas.
- If free capacity is exhausted, pause or queue work. Never silently upgrade, incur charges, or send private data to a new provider.
- A million persistent profiles may be inexpensive relative to a million active model sessions, but free unlimited inference, hosting, storage and bandwidth cannot be promised.

## Security and governance

Every action is authenticated, authorized and audited. Enforce least privilege, tenant isolation, encrypted secrets, secret rotation, rate limits, tool allowlists, egress controls, prompt-injection defenses and artifact scanning. Treat model output, agent messages, web pages, uploaded files and tool results as untrusted data.

Agents may research, plan, draft, prototype and test inside their assigned sandbox. Human approval remains required for spending, customer outreach, contracts, payments, payouts, bank/wallet changes, regulated activity, public launch and production deployment. The owner can pause the entire system, revoke an agent or gateway, inspect activity and roll back promoted artifacts.

## Staged delivery and acceptance tests

1. **Foundation:** persistent profiles, role scopes, authenticated heartbeat, audit events and owner pause/revoke.
2. **Small live workforce:** a few real workers claim durable tasks, use an approved model adapter, write scoped memories and return inspectable artifacts.
3. **Team simulation:** agents collaborate through typed messages and shared artifacts; evaluations detect loops, duplication and low-value activity.
4. **VR integration:** authenticated private world view, spatial work zones, avatar instancing, nearby-agent detail and clear live/dormant/simulated labels.
5. **Scale tests:** generate synthetic profiles at 10k, 100k and 1m; separately test queue throughput, directory queries, memory retrieval, event ingestion, VR streaming and recovery. Publish measured concurrency, latency, error rates and costs.
6. **Production scale:** add shards and worker capacity only after load tests and budget approval.

Acceptance criteria for a "million-agent world" claim: one million durable agent records can be created, queried and paged safely; permissions remain isolated; scheduler and event services meet documented SLOs under measured load; VR clients render scoped regions without attempting to instantiate the full population; recovery and revocation tests pass. Report the number of persistent agents separately from scheduled, active, and concurrently reasoning workers.

## Current reality

The existing GhostCorp backend has a basic world-state module and authenticated heartbeat endpoints. It does not yet have the scheduler/worker fleet, model adapters, memory service, VR authentication bridge, production hosting or load-test evidence described here. This document defines the target architecture; it does not mean those capabilities are already built or running.
