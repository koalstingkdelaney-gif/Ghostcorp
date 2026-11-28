# Owner protection for private business API

## Problem

The prospect API exposed customer and prospect contact records and allowed
mutations without an owner credential. A public website or an exposed API URL
must not be sufficient to read, import, audit, or modify private business data.

## Implemented control

The private lead, discovery-import, website-audit, proposal-draft, job-run and
dashboard-summary routes require the existing deployment-only
`FEDERATION_ADMIN_TOKEN` in the `X-Federation-Admin` request header.
Federation, VR-world, lifecycle, workspace, quarantine and other existing
owner-admin routes continue to use the same gate.

- If the secret is absent, private owner routes fail closed with HTTP 503.
- If the secret is wrong or missing, they return HTTP 403.
- Public health, package catalogue, and explicitly public build-journal routes
  remain public.
- The secret must never be committed to Git or placed in browser JavaScript,
  a public VR asset, or a URL.
- This is a server-to-server/admin API gate, not the finished verified-email
  owner sign-in experience. Do not expose this raw header credential directly
  to an ordinary public browser frontend.

## Deployment prerequisite

Set a long, random `FEDERATION_ADMIN_TOKEN` in the backend host's private
environment/secret manager before using private admin routes. Keep it separate
from public site configuration. Rotate it if it may have been exposed.
