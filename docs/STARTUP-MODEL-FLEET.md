# GhostCorp VR-Local AI Model Runtime

**Status:** owner requirement clarified; architecture specified, not yet implemented or tested on a headset.

## Non-negotiable requirement

AI inference must run inside the GhostCorp virtual-world experience, in the browser/runtime on the device displaying the world. The website is only the entry point and static delivery source for the world, runtime code, model manifests and model files.

Do not require a separate AI server, hosted inference API, cloud GPU, user's PC, Termux, or owner-operated infrastructure. Do not route prompts to a remote model provider. The default and intended mode is local-only inference.

The private website sign-in controls access to the private GhostCorp world. It does not provide compute. Authentication must not expose passwords, session secrets or model-management secrets to agent prompts or public assets.

## Startup behavior

1. Owner signs in to the private GhostCorp website and opens the VR world.
2. The world feature-detects WebGPU, Web Workers, storage capacity and WebXR support at runtime. Do not assume support based on user-agent strings.
3. The world loads its local inference engine and signed/verified model manifest from the website's static assets.
4. It checks the device's available memory, GPU capability, storage quota and thermal/battery conditions where exposed.
5. It selects a compatible model profile automatically. Start with a small quantized model; offer Llama-family models only where a compatible browser build and model license exist.
6. It downloads the selected model weights directly to browser-managed persistent storage/cache, with progress, pause/resume where supported, integrity verification and an explicit storage estimate.
7. It initializes inference in a Web Worker using WebGPU where supported, without blocking VR rendering.
8. It runs a real local inference self-test before showing the model as ready.
9. It caches models for subsequent visits and loads them from local storage when available.
10. The world opens even if model download or WebGPU initialization fails; show a truthful local-AI unavailable or limited-mode state.

## Where everything runs

- VR scene, agent interface, orchestration and inference execute in the browser/runtime on the user's current device.
- Model weights are downloaded from GhostCorp's static website or a configured public model-file source, then cached by the browser on that device.
- Prompts, completions, agent memories and inference context stay on-device in local browser storage unless the owner separately enables a clearly disclosed sync feature. No such sync is part of the local-only default.
- GitHub is for source code and release assets, not model execution.
- No remote inference endpoints or cloud AI APIs are permitted in local-only mode.

A static website can distribute model files and code, but cannot provide extra CPU/GPU/RAM. The headset itself performs the computation. The world must never imply otherwise.

## Model fleet: catalogue vs. active models

GhostCorp can maintain a catalogue containing thousands of model entries and variants. It must not attempt to download or load thousands at once. A headset has finite memory, storage, GPU throughput, battery and thermal capacity.

The runtime should:
- automatically discover models from a versioned manifest;
- filter by license, runtime compatibility, quantization, size and device capability;
- load one primary model first;
- optionally load small specialist models sequentially or on demand if memory allows;
- unload inactive models and release GPU buffers;
- enforce a strict local memory and storage budget;
- allow the owner to choose whether additional model downloads are permitted over the current connection.

Report these separately: catalogued, compatible, downloaded, cached, loaded, actively generating, unavailable. A catalogue entry is not a running model.

## Implementation direction

Use an in-browser inference runtime such as WebLLM/MLC with WebGPU, or another permissively licensed runtime that supports the target browser. Keep the engine behind a small provider interface so a future runtime can be substituted without changing agent identities or the VR world.

Use Web Workers for inference. Keep the render loop responsive. Feature-detect capabilities at runtime and gracefully fall back to a smaller CPU/WASM model only if performance is acceptable. Do not silently fall back to cloud inference.

Model manifest entries must include source, exact revision, cryptographic hash, license, quantization, required runtime version, estimated download size and minimum device requirements. Verify hashes before loading. Do not execute arbitrary remote model code.

## Quest and hardware constraints

Meta Quest Browser release notes list WebGPU support in WebXR in Browser 156.0, but actual availability and usable memory vary by headset, OS/browser version, experimental flags and device state. Runtime feature detection and real Quest testing are mandatory.

A Quest headset is not a data center. Large Llama models may not fit or may run too slowly. Start with a small model and measure real performance before increasing model size. Do not claim that millions of agents can each run their own independent LLM on one headset.

The million-agent world concept must use simulated/persistent agent identities and a scheduler that shares a small number of local model instances across agents. Agents can take turns and keep separate memories/goals; they do not each require a separate model process.

## Privacy and controls

- No prompts, memories or completions leave the device in local-only mode.
- No remote telemetry containing user content.
- No provider API keys or cloud inference credentials.
- Clear owner controls for model downloads, local data deletion, pause and shutdown.
- Separate private GhostCorp business data from public game/social spaces.
- External business actions remain unavailable from the local model unless a separately designed, owner-approved gateway is added later.

## Acceptance tests

- Open the private website and launch the VR world without a separate server or user-installed app.
- Verify WebGPU/WebXR and storage capabilities on the actual target headset.
- Download a compatible small model from the world and verify its hash.
- Generate a response locally with network access disabled after the model is cached.
- Confirm inference runs in a worker and does not freeze VR rendering.
- Confirm prompts and outputs are not sent to a remote inference endpoint.
- Confirm model readiness only after a real local generation test.
- Confirm the world remains navigable when local AI is unsupported or model download fails.
- Confirm model counts distinguish catalogue, cached, loaded and actively generating.
- Confirm multiple agent identities share the local runtime under bounded scheduling rather than spawning one model process per agent.

## Current reality

The existing GhostCorp backend has a basic agent-world state foundation, but the VR website does not yet have a working local model runtime, model manifest, browser cache manager, local agent scheduler or Quest-tested inference integration. This document specifies the target architecture; it is not evidence that local Llama inference is already working.
