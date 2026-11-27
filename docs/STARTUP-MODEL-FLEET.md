# GhostCorp Self-Provisioning AI Model Runtime

**Status:** clarified target architecture; not yet implemented, deployed or running.

## What the owner wants

The owner should sign in to the private GhostCorp website and the virtual world should automatically discover, configure and use suitable AI models—such as Llama-family models—without requiring the owner to install runtimes, manage model files, run Termux, maintain a PC, or manually provision servers.

GitHub is the source-code and release home. ghostcorpnet.com is the user-facing entry point. Neither GitHub Pages nor a static website is a general-purpose GPU server. A private website login authenticates the owner; it does not itself supply compute, storage, model licenses or inference quota.

## Required operating model

GhostCorp must be self-provisioning within the compute it is actually authorized and able to use:

1. The private owner session starts the world and requests a backend startup check.
2. A server-side orchestrator checks which approved inference runtimes and compute providers are already configured and available.
3. It discovers compatible open-weight models (including Llama-family options where their licenses and provider terms permit use), checks hardware/runtime requirements and selects the best eligible models.
4. It prepares models on an authorized runtime, or connects to an approved hosted inference endpoint. Model downloads and startup happen server-side where possible—not in the browser.
5. It starts a small shared worker pool, health-checks it and routes agent tasks to the appropriate model.
6. It continues discovery and warm-up in the background while the VR world opens.
7. It shows the owner truthful statuses: discovered, compatible, downloaded, loaded, serving, unavailable, or waiting for capacity.

The owner should not have to perform routine model setup. Any unavoidable first-time provider authorization, account verification, terms acceptance, or resource permission must be shown clearly and cannot be bypassed by an agent.

## Critical compute constraint

A model must execute somewhere. The browser can run some small quantized models on the owner's current device using WebGPU/WebAssembly where supported, but that consumes the device's battery, memory and processing power, depends on browser/headset compatibility, and is not a shared always-on backend. This is an optional fallback, not the primary architecture.

A GitHub repository stores code and model manifests; GitHub Pages serves static files. GitHub Actions are temporary automation jobs, not a permanent inference host. A static website cannot silently turn itself into a Llama server. If the owner has no spare device or existing server, GhostCorp needs an authorized hosted compute provider or a genuinely available free inference service.

Free hosted capacity is limited, can change, and may require an account, verified access, rate limits or usage terms. There is no honest way to promise thousands of models running continuously for free without actual compute capacity. Do not imply that the website or GitHub supplies this automatically.

## Free-first provider strategy

- Default paid spend remains **USD $0**. Never silently upgrade, subscribe, purchase GPU time, or use a paid fallback.
- Prefer open-weight models with compatible licenses and provider-supported free inference where available.
- Use provider-hosted inference when it is the only compute available and the provider's current free quota and terms permit it.
- Keep provider adapters modular so providers can be added or removed without changing the VR client.
- Store provider credentials only as server-side deployment secrets. Never put them in Git, website JavaScript, browser storage, VR assets, model prompts or public logs.
- Use the owner sign-in to authorize access to the private control panel; use separate server-side provider credentials and narrowly scoped service identities for inference.
- If no authorized free compute is available, mark the runtime as waiting for capacity and queue work. Do not pretend a model is active.

## Thousands of models vs. running models

GhostCorp may maintain a catalogue of thousands of compatible model entries and model variants. It should not attempt to download or load all of them at startup. It should select and warm a small useful set based on capability, license, availability, latency and resource limits. Other models remain discoverable and dormant until needed.

Report these counts separately:
- catalogued model entries;
- license/provenance validated;
- compatible with configured runtime;
- downloaded/cached;
- loaded in memory;
- actively serving requests;
- currently unavailable or waiting for quota.

A catalogue entry is not a running model. A downloaded model is not necessarily loaded. A loaded model is not necessarily serving requests.

## Runtime architecture

- **Private owner authentication:** verified sign-in and short-lived sessions; no shared admin token in the frontend.
- **Server-side orchestrator:** startup, provider discovery, model selection, lifecycle and health status.
- **Model registry:** IDs, revisions, hashes, licenses, sources, capabilities and hardware requirements.
- **Provider adapters:** local runtime and approved hosted inference interfaces, disabled until explicitly configured.
- **Worker pool:** bounded shared workers, leases, queues, retries and concurrency limits.
- **Model cache:** server-side storage with quotas, integrity checks and eviction policy.
- **Capability router:** selects a suitable approved model for each task and tracks latency, quality and quota.
- **VR status bridge:** returns scoped readiness and activity data through the authenticated owner session; never exposes secrets.

## Safety and operational controls

Verify model provenance, revision and license. Do not execute arbitrary repository code or remote custom model code by default. Scan dependencies and isolate model-serving processes. Restrict network egress and tool access. Treat all model outputs and retrieved content as untrusted. Apply per-model, per-agent, per-division and global resource limits, audit events, owner pause/revoke controls and emergency shutdown.

Models must not receive owner credentials, wallet secrets, payment details or unrestricted production permissions. High-impact business actions remain behind explicit owner approvals.

## Startup experience

The virtual world should not wait for every model. It opens its environment, displays the runtime initialization state, and progressively makes available the approved models as they become ready. If compute is unavailable, the world still opens in a limited/offline mode and clearly reports that AI inference is not currently available.

## Acceptance tests

- The owner can sign in without exposing provider secrets to the browser.
- Startup detects configured providers and reports unavailable providers without crashing the world.
- A permitted Llama-family model can be selected and started on a configured runtime.
- No model is marked serving until a real inference health check succeeds.
- No paid provider is called when the spend cap is zero.
- No provider credentials means no false claim of hosted inference; the UI shows setup/capacity required.
- The VR world opens even while model discovery is pending or unavailable.
- Model counts distinguish catalogue, compatible, downloaded, loaded and serving.
- Repeated startup does not create duplicate workers or incur unexpected downloads.
- Owner pause/revoke disables the affected runtime and credentials.

## Current reality

The existing GhostCorp backend has a guarded local-model gateway that is disabled by default, a basic agent world-state foundation and documentation for private owner sign-in. It does not yet have production owner authentication, a deployed orchestrator, a configured hosted inference provider, a model registry, a running Llama runtime, always-on compute or a deployed VR-to-backend session bridge. This specification describes the desired behavior; none of those runtime capabilities should be represented as already working.
