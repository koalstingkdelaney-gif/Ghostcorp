# Free-first hosting decision — 2026-11-28

## Decision

The existing FastAPI application requires a durable writable filesystem at `/data` because its current persistence layer is SQLite. A sleeping or ephemeral free web service is not an acceptable production host for the current code.

**Best candidate to investigate next:** Oracle Cloud Infrastructure Always Free Ampere A1 VM with a persistent boot/block volume, running the existing Docker image. This is a candidate, not a verified deployment or uptime guarantee.

Official Oracle pages:
- https://www.oracle.com/cloud/free/
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

Oracle currently lists up to 2 OCPUs and 12 GB RAM of Ampere A1 compute (1,500 OCPU-hours and 9,000 GB-hours/month), plus 200 GB total Always Free block-volume storage and five volume backups. These resources must be provisioned in the tenancy home region. Free capacity may be unavailable in a region at a given time.

**Important limitations:**
- Oracle requires payment-card details for identity verification and may place a temporary authorization hold. Do not proceed unless the owner is comfortable with that verification requirement.
- The free compute is subject to idle-instance reclamation. Oracle's documentation defines idle usage over a 7-day period using CPU, network, and (for A1) memory thresholds below 20%. A low-traffic application may therefore be at risk of reclamation; do not promise uninterrupted 24/7 service from this tier.
- Do not upgrade the account to Pay As You Go, provision trial-only resources, or exceed Always Free quotas. Keep billing alerts and compartment quotas in place if the owner chooses this route.
- The instance, volume, backup, firewall, and recovery process still need to be configured and tested.

## Supporting components

### Cloudflare Worker proxy

Cloudflare Workers Free currently lists 100,000 requests/day, 10 ms CPU per request, and 128 MB memory. This is suitable for a small path-routing proxy, not for running the unchanged FastAPI application or local model inference.

Official limits:
https://developers.cloudflare.com/workers/platform/limits/

The scoped Worker source is committed at `infra/cloudflare/ghostcorp-api-proxy.js`. It remains undeployed until the owner has a backend HTTPS origin and the Cloudflare zone/Worker is configured.

### Neon Postgres

Neon's Free plan currently lists 1 GB storage per project and 100 compute-hours/month; compute scales to zero after 5 minutes of inactivity. This may be useful for a future Postgres migration or low-traffic datastore, but it is not an always-on database and the current application is SQLite-based. Do not point the current SQLite app at Neon without a deliberate database-layer migration and integration tests.

Official plan limits:
https://neon.com/docs/introduction/pro-plan

## Current account inspection

- Render: connected workspace exists, but no service is attached to the existing GhostCorp backend repository. The available free services are for unrelated repositories; no service was created or repurposed. Free Render web-service storage is not durable for the current SQLite design.
- Supabase: one organization is visible, but there are no projects. No project was created. A database alone would not host the FastAPI app, and moving the backend to Postgres requires a separate migration.
- Oracle: no Oracle account connection or provisioning action is available in this development session. No VM, volume, DNS record, or cloud secret was created.

## Go-live gate

Do not call GhostCorp deployed until all of the following are true:

1. The owner completes Oracle account verification and confirms the selected resources remain within Always Free limits.
2. A VM and persistent storage are provisioned in the home region.
3. The Docker image starts with `AGENCY_DB_PATH=/data/agency.db`; writes survive container restart and VM reboot.
4. Encrypted off-host backups are configured and a restore drill succeeds.
5. Backend HTTPS origin is reachable and protected; only required ports are public.
6. Cloudflare Worker routes only `/auth/*`, `/api/*`, `/webhooks/*`, `/health`, and `/ready`.
7. OAuth secrets and owner allowlist are configured privately; the verified owner can sign in and sign out.
8. Private APIs reject unauthenticated requests and mutation requests without valid CSRF/origin checks.
9. The VR bridge works in the actual Meta Quest browser.
10. A model host with sufficient compute, installed Ollama model, provisioned machine token, and supervised worker is verified separately.

No paid plan, account upgrade, trial-only service, or overage is authorized by this document.
