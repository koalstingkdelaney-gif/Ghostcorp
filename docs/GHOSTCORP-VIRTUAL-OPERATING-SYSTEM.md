# GhostCorp Virtual Operating System

**Status:** consolidated product requirement and implementation architecture. This document is a specification, not a claim that these systems are already implemented or deployed.

## Product definition

GhostCorp VR is intended to be the unified private operating environment for the GhostCorp business: immersive headquarters, local AI runtime, agent workforce, development studio, business control plane, operations console, simulation environment, and owner interface.

The owner enters through the private website. The virtual world is the application. Its AI inference is intended to run locally inside that world on the device displaying it. The design must not silently depend on a separate AI API, cloud model endpoint, user's PC, Termux, or owner-managed server.

The world should be extensible to at least 1,000 capabilities/modules. Those capabilities are grouped into governed departments and loaded on demand; they are not 1,000 separate heavyweight applications or processes.

## Non-negotiable runtime boundary

### Local AI
- Run supported open-weight models on-device through a browser inference engine such as WebLLM/MLC with WebGPU, or a compatible local runtime.
- Use the same local inference interface for agent chat, planning, coding assistance, research synthesis, analysis and routing.
- Candidate model families include Llama, Qwen, Gemma, Mistral, Phi and other models only where their license, model format, browser runtime and device requirements are compatible.
- “Open source ChatGPT” means an open-weight model plus a locally executed assistant/agent harness. ChatGPT itself is not an open-source model.
- Discover model manifests automatically, verify exact revisions and hashes, check licenses, estimate downloads and device fit, download/caches weights and run a real inference test before marking a model ready.
- Load one useful model first; activate additional specialist models only if local memory, storage, GPU and thermal limits permit.
- Never claim that a model is running because it is merely listed or downloaded.
- Never route prompts to a remote inference service in local-only mode.

### The website and virtual world
- The website is the private entry point and static distribution host for the virtual world, scripts, manifests, application modules and model files.
- The VR world runs the client application and local inference on the device.
- The world should expose a local internal service interface to its own modules while the application is active.
- Keep private business state and agent memories on-device by default. If persistence across devices or remote customer access is required, a separate explicitly approved storage/hosting mechanism is necessary; static website files alone cannot provide a secure writable business database.

### Important server limitation
A browser-based VR world running on a headset is not a reliable always-on public server. The browser is sandboxed, can be suspended when backgrounded, and the headset can sleep, lose Wi-Fi or run out of battery. It generally cannot accept arbitrary public inbound connections or guarantee uptime. It can coordinate local business tasks while open, and can host local-only tools/services within the active session, but it cannot be the sole 24/7 server for customer-facing business services.

If the owner insists on no separate server infrastructure, GhostCorp must clearly operate in **owner-device mode**: customer-facing services and scheduled jobs are available only while the world/device is online and active. Do not claim 24/7 service. A future always-on public business server requires an explicitly approved hosting runtime; this is a hard physical/network constraint, not a missing script.

## Startup sequence

1. Authenticate the owner through the website's secure sign-in flow.
2. Load the VR environment and local module registry.
3. Detect WebGPU, WebXR, worker, storage and device capabilities.
4. Start the local model runtime in a worker, with no blocking of the render loop.
5. Discover and validate model catalogue entries.
6. Select and download/cache the best model that fits the device and user-approved download policy.
7. Run local inference self-test.
8. Start the agent scheduler and restore locally persisted agent profiles, memories, projects and queued tasks.
9. Start the internal business modules that are permitted in owner-device mode.
10. Show clear service states: local, ready, busy, offline, waiting for download, unsupported, paused, or owner approval required.

The world must still load if AI startup fails. It should show a truthful degraded-mode state rather than fabricate active agents or business operations.

## Business operating system

All business functions should be accessible from the world through consistent modules, shared identity and permissions, durable local records where supported, and an audit trail. The world is the owner-facing control plane; agents work through bounded internal capabilities rather than unrestricted arbitrary scripts.

### Capability map: 1,000+ extensible functions

The following 20 departments define an initial catalogue of at least 1,000 future capabilities (50 or more capabilities per department). These are product scope categories, not a statement that all functions exist today.

1. **Executive & strategy:** mission, OKRs, planning, scenario analysis, decision logs, prioritization, governance, performance reviews, expansion plans, risk appetite.
2. **Agent workforce:** identity, roles, skills, memory, goals, routines, presence, task queues, collaboration, mentorship, quality scoring, workload balancing.
3. **AI model operations:** model registry, model cards, licensing, quantization, downloads, cache, health tests, routing, prompt templates, context limits, inference telemetry, rollback.
4. **Research & intelligence:** market research, competitor tracking, customer discovery, trend analysis, source verification, evidence libraries, opportunity scoring, research briefs.
5. **Product & engineering:** ideation, requirements, architecture, code generation, issue tracking, version control, builds, testing, release notes, rollback, dependency review.
6. **Cybersecurity & privacy:** threat modeling, secure defaults, secrets inventory, access review, audit logs, dependency scanning, vulnerability triage, incident playbooks, data minimization.
7. **Sales & CRM:** lead intake, qualification, account records, pipeline, follow-ups, proposals, meeting preparation, customer history, forecasting, renewal tracking.
8. **Marketing & content:** positioning, brand, content calendar, copy drafts, SEO plans, campaign experiments, creative review, analytics, consent and opt-out records.
9. **Commerce & storefronts:** catalogues, product pages, pricing drafts, carts, checkout integrations, order tracking, refunds queue, customer support routing, inventory sync.
10. **Finance & treasury:** budgets, cost ledger, revenue reconciliation, invoices, expense classification, cash forecasts, payout queue, owner approvals, audit exports.
11. **Legal & compliance operations:** jurisdiction checklists, policy drafts, terms versioning, privacy requests, records retention, licensing review, contract approval routing.
12. **Customer support:** inbox queue, ticket triage, knowledge base, response drafts, escalation, issue trends, service-level tracking, customer satisfaction.
13. **Operations & reliability:** service status, task scheduler, job retries, backups, restore tests, incident logs, capacity monitoring, release health, runbooks.
14. **Data & analytics:** event schemas, metrics, dashboards, cohort analysis, funnel analysis, attribution, anomaly detection, data validation, report generation.
15. **People & learning:** onboarding, training plans, skills matrix, agent evaluation, documentation, internal knowledge, simulations, learning paths.
16. **Supply chain & procurement:** vendor catalogue, quotes, sourcing, stock planning, purchase requests, supplier risk, shipping status, receiving, returns.
17. **Creative studio:** 3D assets, world building, avatars, sound, UI themes, storyboards, game assets, asset licensing, review and publishing.
18. **Games & experiences:** game projects, world instances, matchmaking concepts, moderation queues, leaderboards, game analytics, release management.
19. **Simulation & digital twin:** business scenarios, load tests, agent drills, incident simulations, financial scenarios, customer journey tests, sandbox experiments.
20. **Owner control & governance:** private access, device sessions, approval queue, permission matrix, spend governor, kill switch, export, data deletion, recovery, system settings.

Each department can grow into 50+ atomic capabilities, yielding a catalogue of 1,000+ entries. Every capability needs a stable ID, owner, input/output schema, permission class, execution mode, data scope, audit event, tests and status. A catalogue entry must never be presented as implemented until its code and acceptance tests exist.

## Agent execution and business safety

- Agents can autonomously research, plan, draft, write code in a sandbox, run bounded tests, create simulations, and prepare recommendations.
- Agents cannot silently spend money, send customer outreach, accept legal terms, sign contracts, change payout destinations, move funds, or deploy production changes.
- Those high-impact actions require explicit owner approval and provider-supported authorization.
- All agent actions must be attributable, scoped, logged and revocable.
- The default spend cap remains USD $0. Never use paid services or paid fallbacks without explicit owner approval.
- Agent identities and simulated lives are persistent software constructs; do not claim they prove consciousness or sentience.

## Security model

- Owner authentication is verified server-side; the email address and secrets are never embedded in public source.
- The browser receives only short-lived, scoped session state.
- Agent tool access is capability-based and least-privilege.
- Local model outputs are untrusted inputs; validate all tool calls and code.
- Arbitrary model-generated scripts must run in an isolated, resource-limited sandbox with no default filesystem, network, credential or payment access.
- Public games and social areas are isolated from private business systems, customer records, finances, agent control and owner settings.
- Backups, sync and multi-device access must be opt-in and clearly explain where data leaves the device.

## Scaling reality

A single headset cannot run a thousand large AI models simultaneously or provide unlimited compute. The scalable approach is:
- thousands of agent profiles and a large model catalogue;
- a small number of local model instances shared by a cooperative scheduler;
- agents take turns, preserve separate memories and hand off tasks;
- modules are lazy-loaded and resource-budgeted;
- 3D avatars and rooms are streamed/instanced and only nearby agents are rendered;
- the world degrades gracefully when memory, battery, storage or GPU capacity is low.

## Initial delivery order

1. Local model runtime proof-of-concept inside `vr/index.html` with WebGPU feature detection, worker-based inference, model download progress, cache, hash verification and a real self-test.
2. Quest-specific compatibility and performance test. Do not assume WebGPU is enabled or that a particular model fits.
3. Local agent scheduler with multiple persistent agent identities sharing one model runtime.
4. Private owner session and private command-center gate.
5. Local project workspace and sandboxed script runner with no network/secret access by default.
6. Department/module registry and the first operational modules.
7. Explicit owner-device mode for tasks that can only run while the headset/world remains active.
8. If 24/7 public business services are later required, request separate hosting approval rather than misrepresenting the headset as always-on infrastructure.

## Acceptance criteria

- The world launches from the existing GhostCorp website.
- Local AI model discovery and inference happen inside the world on the current device.
- A supported model can generate a response with network access disabled after model download/cache.
- No external inference endpoint is called in local-only mode.
- Agent identities share bounded local model resources.
- The UI differentiates planned, implemented, tested and live modules.
- Owner can pause agents, revoke permissions and shut down local inference.
- No paid service is called with a zero-dollar spend cap.
- The world does not claim to be an always-on public server while running only as a browser tab on a headset.
