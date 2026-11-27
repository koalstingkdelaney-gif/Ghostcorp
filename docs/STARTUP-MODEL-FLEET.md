# GhostCorp Startup Model Fleet

**Status:** startup architecture requirement; not yet implemented or running.

## Product requirement

When the GhostCorp virtual world starts, it should automatically initialize its free/open-source AI model ecosystem. The target is to discover and manage thousands of model options over time, with a useful subset ready for work immediately. The system must not falsely claim that thousands of models are loaded or running when they are only catalogued.

## Startup sequence

1. Load the signed/versioned model catalogue and approved provider registry.
2. Check host CPU, RAM, GPU/VRAM, disk, network, runtime versions and current budget.
3. Discover available local model runtimes and free provider endpoints. Verify license, provenance, model format, supported hardware, context limits, quota and terms before enabling a model.
4. Build a capability index (coding, reasoning, summarization, embeddings, vision, speech, classification, translation, safety checks, etc.).
5. Run lightweight health and capability tests; quarantine models that fail validation.
6. Start a small, resource-bounded warm pool for essential services. Keep other models registered but dormant.
7. Route each task to the smallest suitable approved model; use fallback models only when available and allowed.
8. Scale workers gradually based on queue demand and resource headroom. Apply backpressure and stop safely when limits are reached.
9. Publish honest startup status: discovered, validated, available, warming, active, failed, and dormant counts, with timestamps and source/license details.

## Thousands of models: correct interpretation

"Thousands" is a catalogue and orchestration target, not a requirement to load thousands of large model weights into RAM or run thousands of inference servers simultaneously. Many model entries may be alternate checkpoints, quantizations, specialist models or provider-hosted endpoints. Model weights may be downloaded only when needed and only if storage, license and budget policies permit. Concurrent inference is separately capped by measured capacity and free quotas.

No assumption of unlimited free hosted inference. Public model downloads, provider endpoints and free tiers can change, rate-limit, require accounts, or impose usage terms. Paid spend remains USD $0 by default; do not silently subscribe, upgrade, or incur charges. If no eligible free capacity is available, queue or defer work.

## Safety and supply-chain controls

- Maintain an allowlist of registries and sources; record exact model ID, revision/hash, license, source and retrieval time.
- Verify artifact hashes where available; scan downloaded files and dependencies; isolate model-serving processes.
- Do not run arbitrary model repository code, custom extensions, tools or remote code by default.
- Keep inference workers sandboxed with restricted filesystem, network egress and tool permissions.
- Never pass owner secrets, payment credentials, private customer data or unrestricted production access to a model.
- Treat model output as untrusted; require policy checks and human approval for high-impact external actions.
- Provide per-model, per-agent, per-division and global resource ceilings, kill switches and audit events.

## Scaling design

Use a model registry, capability router, worker pool, download/cache manager, health monitor, quota tracker and scheduler. Prefer shared inference servers and batching where compatible. Separate model metadata from model weights. Use quantized variants only when evaluation shows acceptable quality. Evict cold weights using a safe LRU/priority policy; preserve pinned critical models. Avoid duplicating identical weights across workers when sharing is supported.

Startup is staged and asynchronous. The world UI can open while model discovery and warming continue. It must display partial readiness and never block the whole VR world waiting for every model.

## Metrics

Track model catalogue size, validated model count, warm/active worker count, queue depth, task latency, success/error rate, tokens per task, CPU/RAM/VRAM/disk, network transfer, cache hit rate, quota remaining and actual spend. Distinguish model records from model processes, active workers and concurrent inference sessions.

## Acceptance tests

- Cold start works with no network and correctly reports cached models only.
- Startup succeeds when some registries are unavailable.
- A model with an incompatible license, invalid hash, unsafe runtime requirement or failed health test is not enabled.
- Resource limits prevent overcommit and the world remains responsive.
- Free quota exhaustion queues work without switching to paid service.
- Repeated startup is idempotent and does not duplicate workers.
- Owner pause/revoke disables affected workers and credentials.
- Dashboard counts distinguish catalogued, validated, warmed and actively serving models.

## Current reality

GhostCorp currently has no implemented model registry or startup fleet manager. Its existing local-model gateway is guarded and disabled by default. This document is a requirement and design, not evidence that thousands of models have been downloaded, initialized, or made available.
