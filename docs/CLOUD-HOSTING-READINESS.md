# GhostCorp cloud hosting readiness

## Deployment package

The repository now includes a portable Docker image definition. It starts the
FastAPI service on the hosting provider's assigned `PORT`, runs as a
non-root user, and keeps the existing safety defaults:

- paid spend cap: USD 0
- payments: disabled
- outbound calling and SMS: disabled
- local device/Termux is not required to run the container

## Critical persistence requirement

The application currently stores operational state in SQLite. A cloud host
must mount durable persistent storage at `/var/lib/ghostcorp` and preserve
`/var/lib/ghostcorp/agency.db` across restarts and redeployments. Do not deploy
this container to an ephemeral filesystem and treat it as production: leads,
queue state, audit records, federation identities, and ledger simulation
records could be lost on restart.

A future multi-instance deployment should migrate operational state to a
managed PostgreSQL database and use a durable shared queue. Do not scale the
SQLite-backed service horizontally.

## Required host-side configuration

Set these environment variables in the hosting provider's secret/config UI:

- `AGENCY_DB_PATH=/var/lib/ghostcorp/agency.db`
- `AGENCY_SPEND_CAP_USD=0`
- `PAYMENTS_MODE=disabled`
- `CALLING_ENABLED=0`
- `SMS_ENABLED=0`
- `AGENCY_PAUSED=0` (set to 1 for emergency pause)
- `FEDERATION_ADMIN_TOKEN`: generate a long random secret and store it only
  in the provider's secret manager; never commit it or paste it into chat.

Do not provision machine agents or enable payment providers until the host is
secured with HTTPS, durable storage, backups, access controls, and monitoring.

## What is and is not live

Adding a Dockerfile makes the application deployable; it does not create a
hosting account, provision a cloud machine, attach durable storage, or start
the service. No production host has been connected or verified yet. The owner
must authorize the hosting provider's account connection and any required
terms. Keep the application in the current disabled-payment, zero-spend mode
until that is complete.

## Smoke checks after deployment

1. `GET /health` returns `ok: true`.
2. `GET /ready` reports the configured zero spend cap and disabled payments.
3. `GET /api/runtime/status` is reachable only through the intended access
   policy; do not expose administrative endpoints publicly without auth.
4. Restart the service and verify the database records persist.
5. Restore a backup into a staging instance before declaring recovery ready.
