# Agent-specific workspace allocation

## Implemented foundation

`app/agent_workspaces.py` allocates an empty, private-per-agent directory with
mode 0700, a generated unguessable workspace ID, a marker, and a bounded
expiry. Metadata is stored in SQLite. Owner-admin API routes create, list,
release, and clean up expired workspaces. Allocation is disabled unless
`GHOSTCORP_WORKSPACE_ROOT` is configured.

## Important security boundary

This is directory allocation and lifecycle bookkeeping only. It is **not** an
OS/container isolation boundary, does not execute code, does not ingest
artifacts, and does not make a shared host safe for mutually untrusted agents.
Do not place secrets, customer data, or contributor files in these directories.
The host operator must configure a dedicated non-public directory with
appropriate filesystem permissions. Production use requires a separately
verified sandbox runtime and stronger host-level isolation.

## API

- `GET /api/workspaces/status`
- `GET /api/workspaces` (owner-admin)
- `POST /api/workspaces` (owner-admin)
- `POST /api/workspaces/{workspace_id}/release` (owner-admin)
- `POST /api/workspaces/cleanup-expired` (owner-admin)

Creation accepts an agent ID and a TTL from 60 seconds to 24 hours.
Expired workspaces are removed only after their ownership marker is verified.
Cleanup is an explicit owner-admin action; no background scheduler is active.
