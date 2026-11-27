# GhostCorp engineering backlog

**Purpose:** a reviewable, dependency-aware engineering queue that expands the existing 1,200-item capability catalogue toward the 50,000-idea ambition without duplicate filler. Each record is an atomic deliverable with a testable acceptance condition and explicit security check. Catalogue ideas remain PLANNED until implementation, tests and deployment evidence exist.

## Priority order

### P0 — Artifact quarantine completion and recovery

#### GC-SEC-ART-01 — Owner review decision ledger
- **Status:** PLANNED
- **Dependencies:** artifact quarantine metadata table; federation owner-admin gate.
- **Acceptance:** owner can mark an item REJECTED or APPROVED_FOR_MANUAL_EXPORT; repeated decisions are idempotent; original hash and decision history remain immutable; no endpoint executes or publishes the file.
- **Security checks:** require owner authorization on every write; never return storage paths or file contents; audit actor, artifact ID, prior/new state and timestamp; reject transitions from terminal states.

#### GC-SEC-ART-02 — Offline malware-scanner adapter
- **Status:** PLANNED
- **Dependencies:** private quarantine root; pinned scanner binary/container digest; scanner timeout and output caps.
- **Acceptance:** scanner availability is explicit; only locally installed, pinned scanner versions are invoked; timeout, crash, unknown result or missing scanner leaves artifact quarantined.
- **Security checks:** scanner has no network, no secrets, read-only artifact access and bounded CPU/RAM/time; no paid API fallback; never equate a clean scan with guaranteed safety.

#### GC-OPS-REC-01 — Quarantine retention and safe deletion
- **Status:** PLANNED
- **Dependencies:** artifact decision ledger; quarantine metadata.
- **Acceptance:** dry-run reports eligible objects; owner-approved cleanup deletes only expired, unreferenced objects; metadata records deletion outcome; failed deletions remain retryable.
- **Security checks:** no-follow file operations; marker/hash verification before deletion; bounded batch size; never delete unknown files or workspace content.

#### GC-OPS-REC-02 — Interrupted-copy recovery and orphan reconciliation
- **Status:** PLANNED
- **Dependencies:** artifact quarantine storage.
- **Acceptance:** copy uses temporary names and atomic finalization; startup/maintenance scan identifies stale partial files and metadata-without-file/file-without-metadata cases; dry-run and repair modes are separately exposed.
- **Security checks:** never auto-promote; verify generated filename, file type, size and hash; no recursive deletion; owner gate for destructive repair.

#### GC-OPS-REC-03 — Workspace cleanup reference protection
- **Status:** PLANNED
- **Dependencies:** workspace lifecycle; artifact quarantine metadata.
- **Acceptance:** expired workspace cleanup refuses removal while unresolved artifacts reference it; owner can archive or explicitly resolve references; repeated cleanup is safe.
- **Security checks:** marker and path checks remain mandatory; no symlink following; report blocked cleanup rather than deleting uncertain paths.

### P1 — Contributor consent and bounded workload controls

#### GC-COMPUTE-01 — Public contributor consent portal
- **Status:** PLANNED
- **Dependencies:** contributor registry; current terms/version endpoint; revocation endpoint.
- **Acceptance:** page explains exact workloads, CPU/RAM/disk/network ceilings, data accessed, duration, pause/revoke behavior and uninstall steps; enrollment records affirmative versioned consent; no opt-in by default.
- **Security checks:** no execution permission on enrollment; no sensitive identity collection; rate-limit enrollment; clear withdrawal and token revocation.

#### GC-COMPUTE-02 — Enforced resource declaration contract
- **Status:** PLANNED
- **Dependencies:** consent portal; workload profiles; local node agent.
- **Acceptance:** contributor-selected ceilings are stored separately from observed metrics; scheduler never exceeds the smaller of owner policy and contributor ceiling; paused or stale nodes receive no jobs.
- **Security checks:** treat declarations as untrusted; enforce limits locally and server-side; no arbitrary workloads or inbound shell.

#### GC-COMPUTE-03 — Signed contributor agent release
- **Status:** PLANNED
- **Dependencies:** consent portal; immutable workload manifests; isolated runtime.
- **Acceptance:** reproducible, versioned release includes source, checksum, signature, uninstall instructions and a local pause control; agent verifies manifest signature before accepting a job.
- **Security checks:** no embedded secrets; short-lived node credentials; outbound-only control channel; revocation and update rollback tests.

### P1 — Isolation and API assurance

#### GC-SEC-ISO-01 — Per-job rootless execution boundary
- **Status:** PLANNED
- **Dependencies:** fixed workload profiles; signed manifests; per-agent workspaces; trusted host.
- **Acceptance:** each job receives a fresh rootless container/user namespace, read-only source, no network by default, fixed image digest and hard resource ceilings.
- **Security checks:** no Docker socket, host home, credentials, writable source mount or privilege escalation; deny unsupported hosts.

#### GC-SEC-ISO-02 — Cross-agent isolation and race test suite
- **Status:** PLANNED
- **Dependencies:** per-job runtime; workspace and artifact quarantine APIs.
- **Acceptance:** tests exercise concurrent claims, symlink swaps, hard links, stale leases, path traversal, quota races and revocation during execution.
- **Security checks:** assert no cross-agent read/write, no network egress and no resource-limit bypass; fail closed on unsupported OS primitives.

#### GC-API-01 — Scoped owner and machine authorization
- **Status:** PLANNED
- **Dependencies:** owner sign-in provider; machine-agent registry.
- **Acceptance:** owner sessions and machine tokens have separate scopes, expiry, rotation, revocation and audit trails; public read endpoints expose no private business data.
- **Security checks:** constant-time secret comparison, hashed-at-rest machine tokens, CSRF protection for browser writes, rate limits and no secrets in logs.

### P2 — VR integration and operational visibility

#### GC-VR-01 — Authenticated VR operations panel
- **Status:** PLANNED
- **Dependencies:** verified owner login/session bridge; read-only backend status APIs.
- **Acceptance:** Quest panel shows API readiness, agent presence, queue depth, quarantine counts and recent sanitized build milestones; unavailable data is labelled unavailable, not zero.
- **Security checks:** private routes require owner session; no tokens in browser storage or public bundles; read-only by default; all mutations remain outside VR until separately approved.

#### GC-VR-02 — Quest browser compatibility and performance matrix
- **Status:** PLANNED
- **Dependencies:** existing ghostcorpnet-site/vr/index.html scene and developer workbench.
- **Acceptance:** documented Quest Browser tests cover WebXR entry, controller/hand input, virtual keyboard, editor textarea, local save, download, preview sandbox and graceful non-WebXR fallback.
- **Security checks:** preview remains sandboxed; downloaded drafts are not auto-published; no business secrets in browser-local drafts.

## Catalogue growth rules toward 50,000

- Give every capability a stable unique ID, one owner, one bounded outcome and one measurable acceptance criterion.
- Split broad ideas into non-overlapping API, UI, data, security, test, operations and documentation capabilities only when each has independent value.
- Record dependencies and security checks before status can advance from PLANNED.
- Deduplicate by outcome and affected boundary, not just by wording.
- Do not create placeholder counts, duplicate variants, or mark an idea implemented because it appears in a catalogue.
- The 12 records above are the next engineering slice, not a claim that the 50,000-item target has been reached.
