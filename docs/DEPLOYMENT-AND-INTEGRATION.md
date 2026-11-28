# Deployment and live integration readiness

## Deployment artifact

The repository includes a container build for the existing FastAPI application.
It expects a persistent volume mounted at `/data` and sets
`AGENCY_DB_PATH=/data/agency.db`. The process runs as the non-root
`ghostcorp` user, so the mounted volume must be writable by that container
user. SQLite is not safe to keep on an ephemeral
container filesystem: replacing or restarting an instance without persistent
storage can lose customer submissions, audit records, approvals, task queues,
agent lifecycle state and verified sales.

The site is currently a static GitHub Pages-style site. The private browser
flows assume a same-origin reverse proxy from `https://ghostcorpnet.com`:

- `/auth/*` -> FastAPI backend
- `/api/*` -> FastAPI backend
- `/webhooks/gumroad/*` -> FastAPI backend
- static paths such as `/vr/*`, `/website-audit.html` and
  `/service-approval.html` -> static website

Without that proxy, the browser pages cannot reach the backend at the
relative API paths and the secure owner cookie/session will not be available
to them. Do not expose admin headers or secrets in browser code.

## Required private runtime configuration

At minimum:

- `AGENCY_DB_PATH=/data/agency.db`
- `FEDERATION_ADMIN_TOKEN`: long random server-to-server/admin secret
- `OWNER_SESSION_SECRET`: long random HMAC signing secret
- `GITHUB_OAUTH_CLIENT_ID`
- `GITHUB_OAUTH_CLIENT_SECRET`
- `OWNER_GITHUB_LOGIN`: exact allowed GitHub account login
- `GHOSTCORP_OWNER_EMAIL`: exact email that must be verified by GitHub
- `GITHUB_OAUTH_REDIRECT_URI`: exact HTTPS callback registered in the OAuth app
- `GHOSTCORP_SITE_ORIGIN=https://ghostcorpnet.com`
- `PUBLIC_FEEDBACK_RATE_SECRET`: at least 32 random characters
- `GUMROAD_ACCESS_TOKEN`, `GUMROAD_PING_SECRET`, and
  `GUMROAD_ALLOWED_PERMALINKS` after the owner configures Gumroad
- `GUMROAD_SERVICE_PACKAGE_MAP` after the corresponding service products
  exist in the existing Gumroad store and their exact permalinks, raw API
  amounts and currencies are confirmed (format:
  `AI Website=permalink:raw-price:USD`)

Never put these values in Git, the static website, VR assets, query strings,
or user-visible logs.

## Cost and durability

The paid spend cap remains $0 by default. A free web-service tier that sleeps,
has ephemeral disk, or lacks background-worker support is not equivalent to
reliable persistent hosting. Do not deploy the SQLite backend to an ephemeral
filesystem. A durable disk or external database may cost money; obtain owner
approval before selecting a paid tier or enabling automatic upgrades.

## Live integration prerequisites

- A hosting account and production service must be selected and explicitly
  connected. The Render connection has been suggested but is not confirmed.
- Configure a persistent volume, HTTPS, domain routing and private secrets.
- Register a GitHub OAuth application with the exact callback URI.
- Configure the owner allowlist and verified email.
- Configure Gumroad API access with read-only `view_sales` scope, Ping URL,
  webhook secret and product allowlist.
- Add package-to-Gumroad-permalink mappings for the service products.
- Verify DNS, TLS, health/readiness, persistent database writes, restarts,
  webhook delivery, customer approval, payment matching and backups.
- Open the deployed VR pages in the actual Quest 3 browser and test WebXR,
  WebGPU model initialization, controller use, thermal load, memory and
  sustained operation.

## Current state

The Dockerfile has passed CI image-build and container-start smoke tests
with a writable `/data` mount and successful `/health` response. This proves
the container can start in CI; it is not a live deployment. No production
host, production persistent volume, OAuth credentials, Gumroad token, Ping
configuration, reverse proxy, or Quest 3 test session has been verified.
Do not call the backend or VR world fully operational until the above checks
pass.


## Same-origin proxy implementation

A narrowly scoped Cloudflare Worker source is now available at
`infra/cloudflare/ghostcorp-api-proxy.js`; deployment instructions are in
`docs/CLOUDFLARE-API-PROXY.md`. Configure Worker routes only for
`/auth/*`, `/api/*`, `/webhooks/*`, `/health`, and `/ready`, and set
`BACKEND_ORIGIN` to the verified HTTPS backend origin. Do not route all of
`ghostcorpnet.com/*` through the Worker, because that would intercept the
existing static site. The Worker is source-only until the Cloudflare zone,
secret binding, route attachment, and live health checks are completed.

## Hosting account inspection (2026-11-28)

The connected Render workspace was inspected. It contains free services for
other repositories, but no service connected to the existing GhostCorp
backend repository. No service was created or repurposed. A free sleeping
service with ephemeral filesystem is not acceptable for the current SQLite
backend: the `/data` volume must survive restarts and deployments. Do not
proceed on ephemeral storage or select a paid plan without owner approval.

The connected Supabase account has an organization but no existing project.
No project was created. A persistent Postgres project alone would not host
the FastAPI application, and the current backend is SQLite-based; any
Postgres migration must be separately designed, tested, and backed up before
using it as production storage.

The worker runner `scripts/run_worker_loop.py` is now available for a host
with a provisioned machine token and local Ollama model. It has bounded task
and runtime limits, HTTPS enforcement for remote API calls, backoff, and
graceful shutdown. It is not deployed or running; it cannot execute model
inference without a host that actually runs Ollama and a compatible model.
