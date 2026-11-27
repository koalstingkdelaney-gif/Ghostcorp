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
