# Workload governance and quota foundation

## Implemented in source

- A fixed workload allowlist (`public-build-test`, `synthetic-benchmark`); arbitrary shell commands and user-supplied images are not accepted.
- HMAC-SHA256 signed, short-lived workload manifests bound to one agent identity, a full immutable Git commit SHA, a fixed resource profile, an expiry and a nonce.
- Signature verification rejects altered, expired, future-dated, unknown-profile or incorrectly shaped manifests.
- A SQLite quota ledger provides idempotent reservations, one default concurrent reservation per agent, a rolling 24-hour budget of 1,800 seconds, and settlement that cannot exceed reserved time.
- Artifact-name validation rejects absolute paths, traversal, hidden paths, null bytes and Windows-style separators.

## Important boundary

This is authorization and accounting infrastructure only. It does not dispatch or execute contributor code, download packages, inspect binary contents, or make an untrusted host safe. The current Docker adapter still runs only its fixed public test command. A future artifact pipeline must copy outputs into a quarantine area, reject symlinks and oversized files, scan content, and publish only explicitly approved artifacts.

## Configuration

Set `GHOSTCORP_WORKLOAD_SIGNING_KEY` to a randomly generated secret of at least 32 characters in the backend secret manager. Never commit it, expose it to browser code, or reuse the federation admin token. If it is absent, manifest issuance fails closed.

## Next gates

1. Add authenticated API routes and durable audit events for issuing manifests and reserving/settling quotas.
2. Add per-job temporary workspaces and cleanup/recovery.
3. Add artifact quarantine, file-type inspection, malware scanning and signed provenance.
4. Add rootless/container isolation and security tests before any contributor workload is enabled.
5. Add a public contributor consent portal and a downloadable, signed, transparent node agent only after the above gates pass.
