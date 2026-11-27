# Status — 2026-11-27 (rolling engineering record)

## Repository work completed in this update

- Added `app/discovery.py`: provider-neutral ingestion boundary for structured
  business-search results. It makes no network requests and does not scrape
  search-engine result pages.
- Added guarded `POST /api/discovery/import` to the FastAPI app. It enforces
  the global pause switch, limits batches to 100, requires provider provenance,
  validates source URL shape, rejects local/private literal IPs and URLs with
  embedded credentials, and delegates deduplication/opt-out suppression to
  the existing store.
- Added `tests/test_discovery.py` for provenance, unsafe URLs, deduplication,
  suppression, invalid records, and batch limits.
- Updated README to distinguish the ingestion boundary from a live provider.

## Verification state

- GitHub accepted the commits for the new module, API integration, and tests.
- **Tests have not been executed in this environment.** Do not report them as
  passing until CI or a local test run confirms it.
- The discovery endpoint is not connected to a live search/business-data
  provider. It is ready to receive structured results from a separately
  approved adapter; that adapter remains future work.

## Existing Phase 0 + Phase 1 claims (historical, dated 2026-11-02)

The prior status reported 10/10 tests passing on 2026-11-02, a read-only import
of 6,748 leads, 12 opt-out suppressions, 10 audited prospects, and 10 proposal
drafts. Those are historical claims from the previous status report, not
freshly rerun or independently reverified in this update.

## Still blocked / not proven

- Cloud deployment: no production host or live URL verified.
- Payments: disabled; provider onboarding and test-mode integration remain.
- Calling/SMS: disabled; compliance and provider prerequisites remain.
- Live discovery provider: not connected.
- Revenue: no verified customer payment or revenue established.
- CI: must run the test suite and security checks before treating this update
  as verified.

## Operating constraints

- External paid API spend remains $0 before revenue.
- No outbound marketing messages, calls, or texts are enabled.
- No credentials or payment-card data belong in Git.
- Owner approval remains required for spending, paid-provider activation,
  payout changes, customer-facing publication, and production deployment.


## Backup and resilience work (2026-11-24)

- Added `scripts/backup_db.py`: consistent SQLite snapshot via the online backup API, age encryption, decryption/hash round-trip verification, and three-generation retention.
- Added `tests/test_backup.py` for the SQLite snapshot path.
- Added `backups/` to `.gitignore`; runtime backup artifacts must never enter the public repository.
- Tests have not been executed in this environment. No production database, age recipient, or off-host destination was available to verify a live backup.


## Identity-minimal federation foundation (2026-11-26)

- Added `app/federation.py` with SQLite division and machine-agent registries.
- Added `GET /api/federation/status`, plus admin-token-protected division and
  agent provisioning endpoints. The admin token must be configured as
  `FEDERATION_ADMIN_TOKEN` in the runtime environment; it is not stored in Git.
- Agent credentials are generated as machine tokens and only SHA-256 hashes
  are stored. A newly provisioned token is returned once by the provisioning
  endpoint. Provisioned agents are **not running agents**.
- Registry schema intentionally excludes personal names, personal email,
  birth dates, government IDs, addresses, and identity-document fields.
- Added `app/ledger.py` with a provider-neutral append-only event journal and
  an admin-protected simulation endpoint. It is explicitly
  `SIMULATED_ONLY`: it does not hold wallet keys, bank details, card data,
  convert assets, or move money.
- Added `tests/test_federation.py` and `tests/test_ledger.py`.
- GitHub accepted these commits, but tests have **not** been executed. Do not
  claim the new modules are passing until CI or a local test run verifies them.
- No always-on runtime, provider credentials, live wallet, fiat checkout,
  crypto conversion, or USD payout integration has been established.
- The public status endpoints report registry/ledger state only. All writes
  are denied unless the separate federation admin token is configured.


## Durable agent queue foundation (2026-11-26)

- Added `app/agent_runtime.py`: durable SQLite task queue with machine-token
  authentication, division-scoped claiming, role filtering, expiring leases,
  lease-token completion, and idempotent task keys.
- Added admin-token-protected task enqueue plus agent claim/complete/status
  endpoints under `/api/runtime`.
- Added `tests/test_agent_runtime.py` for task lifecycle, division isolation,
  and idempotent enqueue.
- GitHub accepted the source and test commits. Tests have **not** been run in
  this environment; runtime behavior remains unverified until a test run.
- This is queue infrastructure, not an autonomous AI worker. No model
  executor, scheduler, production host, or always-on process is configured.
- Existing machine agents remain provisioned identities; they are not
  automatically running or independently reasoning.


## Public process journal and always-on fleet architecture (2026-11-26)

- Added `app/build_journal.py` with an allowlisted, sanitized public milestone journal.
- Added public read endpoint `GET /api/public/build-journal` and admin-token-protected publish endpoint `POST /api/build-journal/publish`.
- Added `tests/test_build_journal.py` for publication, idempotency, and state validation.
- Added `docs/ALWAYS-ON-OPERATIONS.md` documenting the coordinated ephemeral-worker model, durable shared queue, staggered schedules, leases, recovery, resource limits, and truthful public progress.
- GitHub accepted the code and test commits. Tests have not been executed here.
- The public journal is an API foundation; no automatic scheduled publisher, website widget, or social account integration is active.
- No GitHub Actions workflow was deployed. The connected repository integration previously reported missing workflow permission. No 24/7 server or worker fleet is live.


## Worker queue hardening (2026-11-26)

- Serialized worker-runtime database access within the API process and used
  SQLite `BEGIN IMMEDIATE` around lease recovery and task claiming to prevent
  duplicate claims under concurrent workers.
- Added bounded task/result payload sizes, configurable bounded attempt counts,
  lease-expiry retries, and a terminal `dead_letter` state after retry
  exhaustion. Existing SQLite databases are upgraded additively.
- Added tests for payload-size rejection and retry exhaustion.
- Commits: `0cbfb865216795d435906f9442183c27ef81228e`,
  `e48e9858956d78f9e4423c389a702dee9c76e836`,
  `4a9671ffc65799b888ddfbaa5ee3d4e7dff99a19`.
- The repository contains `.github/workflows/tests.yml`, which is configured
  to run pytest on pushes affecting application, scripts, tests, requirements,
  or the workflow itself. The latest run result has not yet been retrieved.
- These controls harden queue coordination; they do not create a worker,
  connect an AI model, deploy a service, or establish 24/7 uptime.


## Local model gateway foundation (2026-11-26)

- Added `app/model_gateway.py`: an Ollama-compatible local inference adapter.
- The adapter is disabled by default, accepts only loopback HTTP endpoints,
  has no cloud fallback or paid API path, and restricts task types and privacy
  classes. Prompt/output sizes and request timeout are bounded.
- Added `tests/test_model_gateway.py` for disabled defaults, endpoint
  restrictions, privacy/task policy, bounded prompts, and mocked local calls.
- Added `docs/LOCAL-MODEL-GATEWAY.md` and linked it from the README.
- The code is **not connected to the agent queue**, Ollama is not installed or
  configured on a host, and no model is running. Tests have not been confirmed
  green. No always-on inference service is claimed.


## Persistent VR agent-world foundation (2026-11-27)

- Added app/agent_world.py to mirror provisioned machine agents into persistent world profiles with role-based daily routines, allowed workspace zones, authenticated heartbeats, and bounded event history.
- Added admin-protected GET /api/world/snapshot and GET /api/world/events; added machine-token-authenticated POST /api/world/heartbeat.
- Added tests/test_agent_world.py for registry sync, live presence, routine selection, zone validation, and event history.
- Added docs/AGENT-WORLD.md describing presence semantics, deployment stages, privacy boundaries and the distinction between simulated routine and actual live work.
- GitHub accepted the commits. Tests have not been run in this environment.
- No API host, scheduler, model worker, agent heartbeat process, VR-to-API session bridge, or actual live AI population is deployed. Agents without a recent heartbeat are reported as SIMULATED, not LIVE. This work does not create or prove sentience.


## Agent business mission and owner sign-in specification (2026-11-27)

- Added role-specific long-term business missions and a world policy reporting a $0 default paid-spend cap, private sandbox preference, controlled external gateways and owner override.
- Added tests for the world mission and free-first policy. Tests have not been run here.
- Added docs/OWNER-SIGN-IN.md. The requested owner mailbox must remain a private deployment setting and be verified by a real authentication provider; it has not been configured or activated.
- Documented that the static public website does not currently provide verified owner email login or a session bridge to the backend.
- No live AI workers, autonomous business creation, email login, always-on hosting or revenue generation are established by these commits.


## Agent-specific workspace allocation (2026-11-27)

- Added `app/agent_workspaces.py`: empty per-agent directories with random IDs,
  mode-0700 permissions, SQLite metadata, bounded expiry, marker-checked
  release, and explicit expired-workspace cleanup.
- Added owner-admin API routes under `/api/workspaces`; allocation is disabled
  unless `GHOSTCORP_WORKSPACE_ROOT` is configured.
- Added `tests/test_agent_workspaces.py` for separation, disabled defaults,
  invalid identities, expiry cleanup, and marker validation.
- This is directory lifecycle bookkeeping only, not container/OS isolation,
  code execution, artifact quarantine, or a deployed workspace service.
- Tests have not been executed in this environment.


## CI repair and artifact quarantine increment (2026-11-27)

- Fixed the researcher mission text so the research role explicitly includes lawful net-revenue outcomes.
- Corrected a contradictory contributor-approval test: unknown contributor IDs are rejected, a pending contributor can be approved once, and duplicate approval is rejected. The registry's existing owner-review model was preserved.
- Added strict artifact path validation for dot components, repeated separators and trailing separators.
- Added app/artifact_quarantine.py: bounded 1 MiB default intake (10 MiB hard ceiling), active/non-expired workspace verification, no-follow path traversal, symlink and hard-link rejection, private 0700 roots, 0600 quarantine objects, SHA-256 hashing, source-mutation detection, and basic content classification.
- Added owner-admin API routes POST /api/artifacts/quarantine and GET /api/artifacts/quarantine plus public configuration-only GET /api/artifacts/status.
- Added tests/test_artifact_quarantine.py and API default-deny tests. Latest successful GitHub Actions run: 46084749049 on commit db8af7f460726f6d29a1f5d02bbe63725c74c628; **93 passed, 1 warning**.
- The earlier CI run on commit 6b8959df failed with two test failures; both were addressed, and the latest run is green. The Starlette/httpx deprecation warning remains non-fatal.

## Current lifecycle status

- **IMPLEMENTED IN CODE:** agent-specific empty workspaces; signed workload manifests and quota ledger; artifact quarantine copy/hash/metadata/content classification; owner-admin route guards; automated tests.
- **PARTIAL / DISABLED BY DEFAULT:** workspace and quarantine storage. Both private host roots and the owner-admin secret must be configured before intake can run.
- **PLANNED:** malware scanning, owner review decisions, safe export/promotion, quarantine retention and orphan recovery, cleanup reference protection, contributor consent portal, remote job execution, per-job rootless isolation, and VR-to-backend owner session.
- **NOT VERIFIED DEPLOYED:** backend hosting, production API, worker processes, contributor execution, malware scanner, owner sign-in, or VR business-system integration.
- **Website / VR repository:** existing Three.js/WebXR page and in-headset developer workbench are present in the repository. The live cache-busted page previously showed the workbench control; headset entry, controller operation, and direct GitHub publishing from inside Quest are not verified.
- **No production deployment, DNS change, paid service, contributor execution, customer-data access, or financial action was performed in this increment.**
