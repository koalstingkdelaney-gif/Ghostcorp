# Artifact quarantine and inspection

**Status: IMPLEMENTED IN CODE · DISABLED UNTIL HOST CONFIGURATION · NOT DEPLOYED**

## Purpose

Artifacts are copied only from an active, unexpired agent workspace into a separate private quarantine directory. Quarantine is a holding and inspection boundary, not a malware-clean verdict or a release pipeline.

## Implemented controls

- Owner-admin-only POST /api/artifacts/quarantine and GET /api/artifacts/quarantine routes; public GET /api/artifacts/status reports configuration only.
- Requires the workspace ID to exist in the SQLite workspace registry, remain ACTIVE, and not be expired.
- Uses strict relative artifact paths; rejects absolute paths, hidden components, traversal, empty/dot components, repeated separators and Windows separators.
- Opens the workspace and each directory component with no-follow semantics. Rejects symlinks, non-regular files and hard-linked files.
- Requires private workspace and quarantine roots (mode 0700 or stricter) and stores opaque quarantine objects with mode 0600.
- Enforces a default 1 MiB file limit (hard constructor ceiling 10 MiB), hashes content with SHA-256, checks for source mutation during copy, and stores metadata rather than file contents in SQLite.
- Performs bounded signature/UTF-8 classification for executable/script-like content, archives, PDF, images, JSON, text and unknown binary data.
- Every item remains QUARANTINED and review_required; automatic extraction, execution and release are always false.
- Writes an audit event containing the artifact ID only. No artifact contents or source filesystem path are logged.

## Host configuration

Set these only in the trusted backend runtime environment:

- GHOSTCORP_WORKSPACE_ROOT: the existing private agent-workspace root.
- GHOSTCORP_ARTIFACT_QUARANTINE_ROOT: a separate private directory for quarantined objects.
- FEDERATION_ADMIN_TOKEN: existing owner-admin gate, managed outside Git.

Both roots must be pre-created real directories with permissions 0700 or stricter. The API does not create the quarantine root automatically. Do not put either path on the public website. Status reports enabled only when both roots exist and are private; intake remains disabled if either root is missing or too permissive.

## Important limitations

- No antivirus/malware scanner is configured. The inspector is a small format classifier only; it cannot establish that a file is safe.
- Archives are never extracted. HTML, scripts, binaries, PDFs and images are never rendered or executed.
- There is no approval/rejection or promotion endpoint, retention scheduler, restore workflow, or orphan reconciliation yet.
- No Docker host, trusted scanner image, production backend, or live API configuration is verified.
- The quarantine feature does not authorize contributor compute or permit arbitrary workload execution.

## Verification

The automated test suite covers normal text intake, hashing, private file mode, archive/executable flags, traversal, symlinked files/directories, expired workspaces, hard links, size limits and default-deny API behavior. See the current CI run linked from the repository's Actions page; only a completed successful run is verification evidence.
