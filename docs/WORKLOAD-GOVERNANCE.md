# Workload governance and quota foundation

## Implemented in source

- A fixed workload allowlist (`public-build-test`, `synthetic-benchmark`); arbitrary shell commands and user-supplied images are not accepted.
- HMAC-SHA256 signed, short-lived workload manifests bound to one agent identity, a full immutable Git commit SHA, a fixed resource profile, an expiry and a nonce.
- Signature verification rejects altered, expired, future-dated, unknown-profile or incorrectly shaped manifests.
- A SQLite quota ledger provides idempotent reservations, one default concurrent reservation per agent, a rolling 24-hour budget of 1,800 seconds, and settlement that cannot exceed reserved time.
- Artifact-name validation rejects absolute paths, traversal, hidden paths, null bytes and Windows-style separators.

## Artifact quarantine increment

The backend now includes a bounded, owner-admin-gated artifact intake path. It copies regular files only from active, non-expired agent workspaces into a separate private quarantine root, rejects symlinks/hard links and unsafe relative paths, enforces size limits, hashes content, and classifies common text/archive/executable/document formats. All objects remain QUARANTINED and pending review.

See ARTIFACT-QUARANTINE.md for the API, configuration and limitations. This is not antivirus scanning: no malware scanner is configured, archives are not extracted, and there is no approval, export or promotion endpoint. The intake routes remain unavailable until both private storage roots and the owner-admin token are configured.

This is still authorization, accounting and quarantine infrastructure only. It does not dispatch or execute contributor code, download packages, or make an untrusted host safe. The Docker adapter still runs only its fixed public test command.

## Configuration

Set `GHOSTCORP_WORKLOAD_SIGNING_KEY` to a randomly generated secret of at least 32 characters in the backend secret manager. Never commit it, expose it to browser code, or reuse the federation admin token. If it is absent, manifest issuance fails closed.

## Next gates

1. Add an owner review decision ledger; keep all quarantined files non-executable and non-public.
2. Add a pinned, offline malware-scanner adapter that fails closed when unavailable.
3. Add retention, interrupted-copy recovery and orphan reconciliation; protect workspaces referenced by unresolved artifacts.
4. Add rootless per-job isolation and cross-agent/race security tests before any contributor workload is enabled.
5. Add a public contributor consent portal and a downloadable, signed, transparent node agent only after the above gates pass.
