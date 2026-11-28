# Cloudflare same-origin API proxy

This repository contains `infra/cloudflare/ghostcorp-api-proxy.js`, a small Worker that forwards only GhostCorp API paths to the FastAPI backend while leaving the existing static GitHub Pages website untouched.

## Why this is needed

The website uses same-origin browser paths for owner sign-in and private APIs. Static GitHub Pages cannot execute FastAPI. A Worker on narrowly scoped routes can forward those requests to a separately hosted backend and preserve secure same-site cookies.

## Required deployment values

Configure the Worker environment variable:

- `BACKEND_ORIGIN`: the HTTPS origin of the deployed FastAPI service, with no path, query, credentials, or trailing route.

Do not put OAuth secrets, admin tokens, machine tokens, or session secrets in this Worker. They belong only in the backend host's secret manager.

## Exact Worker routes

Attach the Worker only to these routes on the existing domain:

- `ghostcorpnet.com/auth/*`
- `ghostcorpnet.com/api/*`
- `ghostcorpnet.com/webhooks/*`
- `ghostcorpnet.com/health`
- `ghostcorpnet.com/ready`

Do not attach it to `ghostcorpnet.com/*`; the static website and VR files must continue to be served by the existing Pages deployment.

## Deployment sequence

1. First deploy the FastAPI backend to a host with durable writable storage mounted at `/data`. Do not use an ephemeral filesystem for the SQLite database.
2. Verify the backend's `/health` and `/ready` endpoints directly over HTTPS.
3. Create a Cloudflare Worker from `infra/cloudflare/ghostcorp-api-proxy.js`.
4. Set `BACKEND_ORIGIN` to the verified backend HTTPS origin.
5. Add only the five route patterns above.
6. Verify `https://ghostcorpnet.com/health` returns the backend health JSON and that `https://ghostcorpnet.com/vr/` still serves the static VR page.
7. Configure the GitHub OAuth callback exactly as `https://ghostcorpnet.com/auth/github/callback`.
8. Test owner sign-in, CSRF-protected mutations, logout, and private API denial from a signed-out browser.

## Security behavior

- Only the explicitly allowed paths are forwarded.
- The backend origin must be HTTPS and cannot contain credentials or a path.
- Browser cookies and response Set-Cookie headers are preserved for same-origin sessions.
- The Worker does not add permissive CORS headers.
- Responses are marked `no-store`.
- A missing backend origin returns 503; an upstream failure returns 502.
- The Worker does not make private endpoints public or add authentication. The FastAPI owner/admin authorization remains authoritative.

## Current state

The Worker source is committed but **not deployed**. The backend origin, Cloudflare zone access, Worker binding, and DNS route are not yet verified. Do not report the proxy as live until the direct health and end-to-end sign-in checks pass.
