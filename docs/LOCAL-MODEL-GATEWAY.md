# Local model gateway

GhostCorp now has a first, deliberately narrow model adapter: an Ollama-compatible
local HTTP endpoint bound to loopback. It is an execution adapter, not a hosted
model service and not an autonomous agent.

## Defaults

- Disabled unless `GHOSTCORP_LOCAL_MODEL_ENABLED=1`.
- Model name must be supplied through `GHOSTCORP_OLLAMA_MODEL`.
- Endpoint defaults to `http://127.0.0.1:11434`; only localhost/loopback HTTP
  endpoints are accepted. Remote/cloud endpoints are rejected.
- No cloud fallback, paid API key, external model call, tool execution, or
  external spend is implemented.
- Only `research_summary`, `classify`, `code_review`, and
  `draft_internal` task types are allowed.
- Restricted and financial privacy classes are blocked from submission.
- Prompt and output sizes and request timeout are bounded.

## Enable on a machine that already runs Ollama

Set the environment variables in that machine's private runtime configuration,
not in Git:

```sh
GHOSTCORP_LOCAL_MODEL_ENABLED=1
GHOSTCORP_OLLAMA_URL=http://127.0.0.1:11434
GHOSTCORP_OLLAMA_MODEL=<installed-local-model-name>
```

The gateway does not install Ollama or download a model. Hardware capacity,
model licence, local data protection, and process supervision must be checked
on the host first. A phone/Termux session is not assumed to be a dependable
24/7 inference server.

## Next gates

Before connecting this adapter to the task queue: add task-level privacy
metadata, enforce role permissions at enqueue and claim, add cancellation and
lease heartbeat, record model/version/provenance and token estimates, and
review prompts/results for secret leakage. Do not send customer, financial,
credential, or restricted data to a model until a separately reviewed policy
permits it.


## Bounded queue worker runner

A supervised host can run one bounded worker process with:

```sh
GHOSTCORP_API_BASE=https://your-backend.example
GHOSTCORP_MACHINE_TOKEN=<private-machine-token>
GHOSTCORP_LOCAL_MODEL_ENABLED=1
GHOSTCORP_OLLAMA_URL=http://127.0.0.1:11434
GHOSTCORP_OLLAMA_MODEL=<installed-local-model-name>
python scripts/run_worker_loop.py
```

The runner requires HTTPS for remote API hosts (loopback HTTP is allowed for local development), processes at most 20 tasks and 55 minutes by default, polls idle queues at a bounded interval, backs off after errors, handles SIGTERM/SIGINT, and logs task identifiers/status only—not prompts, tokens, or model output. Limits can be adjusted with `GHOSTCORP_WORKER_MAX_TASKS`, `GHOSTCORP_WORKER_MAX_RUNTIME_SECONDS`, and `GHOSTCORP_WORKER_IDLE_SECONDS` within enforced ranges.

This is a deployable process entry point, not proof of a running worker. It still requires a separately hosted backend, a provisioned machine identity, a host with Ollama and a compatible model installed, and a process supervisor. The worker cannot run the model on GitHub Pages or on the website's static hosting.
