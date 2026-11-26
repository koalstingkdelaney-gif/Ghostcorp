# Queue worker

The worker is a real execution adapter for the durable task API, but it is not an always-on hosted service by itself.

## What it does

- Claims at most one task using a division-scoped machine bearer token.
- Sends only allowlisted task types to the loopback-only Ollama gateway.
- Rejects restricted and financial privacy classes at the model gateway.
- Completes the leased task with a bounded result or visible policy-block result.
- Never runs returned code or invokes tools.

## Required environment

- `GHOSTCORP_API_BASE`: deployed GhostCorp API base URL (defaults to localhost).
- `GHOSTCORP_MACHINE_TOKEN`: token for a provisioned machine agent.
- `GHOSTCORP_LOCAL_MODEL_ENABLED=1`
- `GHOSTCORP_OLLAMA_URL=http://127.0.0.1:11434`
- `GHOSTCORP_OLLAMA_MODEL`: installed local model name.

Run one task with `python scripts/run_worker.py`. A scheduler or supervised process can invoke this one-task entrypoint. Do not expose Ollama publicly or put machine tokens in source, website JavaScript, workflow logs, or chat.

## Not yet operational

This commit does not provision a server, install Ollama, provision machine identities, create a production secret store, or start a persistent worker. The API and model must both be reachable from the worker environment. CI must pass before this is considered verified. No paid model fallback exists; the spend ceiling remains $0.