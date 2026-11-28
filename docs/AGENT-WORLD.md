# GhostCorp Agent World

**Status:** persistent world-state foundation committed; not deployed or connected to a running AI workforce.

## Product intent

The VR environment is the shared spatial workplace for GhostCorp's AI workforce. Each machine agent should have a stable machine identity, division, role, workspace, routine, current task, presence heartbeat and auditable activity history. Agents can appear in their work zones, collaborate through typed tasks and leave the world-state record when work is complete.

The world is a simulation and coordination interface. It does not establish consciousness, subjective experience, emotions or sentience. Personality and social behavior, if later added, are explicit model-driven interaction features and must not be presented as proof of consciousness.

## What this commit adds

- app/agent_world.py mirrors provisioned machine agents into persistent world profiles.
- Role-based UTC daily routines give disconnected agents a clearly labelled simulated activity and workspace.
- Authenticated machine heartbeats mark an agent as LIVE for up to 180 seconds.
- World events are recorded in a bounded 5,000-event history.
- Zone names and activity lengths are allowlisted and bounded.
- GET /api/world/snapshot and GET /api/world/events require the federation admin token.
- POST /api/world/heartbeat requires the machine agent's bearer token.
- Existing agent identities are reused; this does not create additional workers or model inference.

## Presence semantics

| Presence | Meaning |
|---|---|
| SIMULATED | No recent authenticated heartbeat; the UI may show the agent's scheduled routine, but it is not actually working. |
| LIVE | The machine identity has sent a valid heartbeat within the last 180 seconds. This proves process connectivity only, not that an AI model is reasoning or completing work. |

## Next implementation stages

1. Deploy the API and durable database on an always-on host with backups and TLS.
2. Provision machine identities per division and attach role-scoped model workers.
3. Add a scheduler that enqueues bounded work, checks task leases, and wakes workers; add heartbeats from the worker process.
4. Connect the VR client to the authenticated world snapshot through a short-lived owner session, never a long-lived admin token in browser code.
5. Add spatial avatars, voice/text collaboration, workstations, activity timelines and inspectable task artifacts.
6. Add evaluations, memory permissions, per-agent budgets, prompt-injection defenses and a global pause/revoke control.
7. Only then allow agents to propose real-world business actions; customer communications, spending, contracts, payments, payouts and production deployment remain governed by explicit approvals.

## Security boundaries

- Do not place federation admin tokens, machine bearer tokens, model API keys, wallet secrets or customer records in the VR page, Git, browser storage or avatar metadata.
- Public VR/social/game areas must not expose the private agent roster, work queue, business knowledge, finance data or owner controls.
- Use a server-side session broker for the VR client and short-lived, least-privilege access.
- Simulated routines must never be counted as completed work, productivity, revenue or proof of agent uptime.


## Agent mission and autonomy policy

Each role has a durable long-term mission exposed in the world snapshot. The shared objective is to maximize lawful, sustainable net value for GhostCorp—not vanity activity, gross sales, simulated productivity or revenue at any cost. Agents should measure costs, fees, refunds, customer outcomes, reliability and risk as well as sales.

The default environment is the private GhostCorp sandbox. Agents should do their reasoning, planning, collaboration, simulation and development there. They do not need unrestricted external network access: research and real-world operations should pass through controlled, allowlisted gateways that return auditable results. No agent may escape its assigned data scope, bypass platform rules, create deceptive identities or access owner credentials.

The default paid-spend cap is $0. Prefer open-source software, local inference where available, free tiers and static hosting. If free capacity is exhausted, queue or defer work rather than silently upgrading, incurring charges or switching private data to an unapproved provider.

Agents may independently discover opportunities, draft business plans, build prototypes in isolated sandboxes, test them, and recommend new divisions. Launching a business, publishing claims, contacting customers, signing contracts, spending money, handling regulated activity, moving funds or changing payout destinations remains subject to explicit policy and owner approval.

The phrase "stay in the world" is an architecture preference: the VR environment is their primary workspace and external actions are mediated by gateways. It is not a claim that agents have subjective desires, fear of leaving, or consciousness. The owner retains pause, revoke, edit and shutdown control.


## Adaptive world and department-local learning

Authenticated agents can report bounded learning events through `POST /api/world/learn`. Each event is attributed to the reporting machine identity, its registered division, and that agent's current world zone. The world stores a declarative adaptation record and a corresponding event.

Supported adaptation categories are `knowledge-cluster`, `workspace-layout`, `ambient-state`, `workstation-upgrade`, and `display-panel`. Configuration is a small allowlisted JSON object; arbitrary HTML, JavaScript, executable content, and unbounded coordinates/scales are rejected. Repeated event keys are idempotent. An agent cannot select another agent's identity or write to a different zone through this endpoint.

Owner-only `GET /api/world/adaptations` and `GET /api/world/snapshot` expose the change history for inspection. The snapshot includes recent adaptations so an owner interface can highlight the exact areas that changed. The current backend records these changes; it does not yet automatically render them in the Quest scene. That requires the authenticated owner session bridge and a VR client adapter. The existing static website must never contain the federation admin token or machine bearer tokens.

This is the authenticated event and persistence layer, not autonomous learning by itself. Real model workers must call the endpoint with evidence-backed learning outcomes. Heartbeats and simulated routines do not count as learning. No current worker fleet is deployed, so live changes will not appear until workers, hosting, and the secure VR session are connected.


## Agent wake/work/sleep/dream lifecycle

Agents have a persistent lifecycle state: `INITIALIZING`, `WORKING`, `SLEEPING`, `DREAMING`, `WAKING`, or `PAUSED`. The intended startup sequence loads identity, role, memory, goals, skill set, safety policy and current task context before entering work mode. Normal task claims are denied when a registered lifecycle state is not `WORKING`.

A work cycle can transition to sleep, then to a restricted dream phase. Dream outputs are bounded structured artifacts (ideas, research, prototype plans, skill proposals and world-change proposals) saved as `AWAITING_REVIEW`. They are not automatically merged into production memory, code, world state, or business operations. On waking, an agent returns to work and reviews its previous cycle's discoveries. Owner review is required before a dream artifact can become an approved business or production change.

Endpoints: machine-authenticated `GET /api/lifecycle/me`, `POST /api/lifecycle/transition`, and `POST /api/lifecycle/dream-artifacts`; owner-admin `GET /api/lifecycle/status` and `GET /api/lifecycle/dream-artifacts`.

**Dream realm limitation:** this increment provides lifecycle coordination and a durable dream-artifact inbox. It does not yet provide a separate executable VR dream world, an always-on scheduler, model self-training, persistent autonomous inference, or an isolated dream-code execution environment. Those require real workers, a hardened sandbox runner, a secure owner session, and deployment. Never run dream-generated code in production or give the dream realm live credentials, customer records, payment tools, or unrestricted network access.
