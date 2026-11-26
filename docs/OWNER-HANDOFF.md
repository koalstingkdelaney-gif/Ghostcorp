# Owner handoff — only the steps GhostCorp cannot complete itself

This is the handoff checklist for the GhostCorp backend and existing ghostcorpnet.com
site. Build work should continue without waiting for these steps. Do not send
passwords, API tokens, recovery codes, bank details, payment-card data, or ID
documents in chat or GitHub issues.

## What is already connected in the project

- Website repository: https://github.com/koalstingkdelaney-gif/kestrelattice
- Backend repository: https://github.com/koalstingkdelaney-gif/Ghostcorp
- Existing public site: https://ghostcorpnet.com/
- Public progress page: https://ghostcorpnet.com/changelog.html
- Backend Actions page: https://github.com/koalstingkdelaney-gif/Ghostcorp/actions

The website remains on its existing GitHub Pages deployment. Do not create a
replacement site or change domain DNS just to publish build progress.

## Handoff 1 — GitHub Actions (check first; no secret needed)

1. Open https://github.com/koalstingkdelaney-gif/Ghostcorp/actions
2. Select **GhostCorp agency tests** in the workflow list.
3. If GitHub shows **Enable workflow**, tap it once.
4. Open the newest run and check whether the test job is green or red.
5. If it is red, send me the run link or a screenshot of the failing step only.
   Do not copy any secret values from logs.

The repository already contains a test workflow. This step is only needed if
GitHub has it disabled or a run is blocked.

Official GitHub help:
https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows

## Handoff 2 — Cloudflare account (needed for a persistent backend deployment)

Use the existing Cloudflare account if GhostCorp already has one. Do not
create a second account just to multiply free quotas.

1. Sign in at https://dash.cloudflare.com/
2. Open **Workers & Pages**:
   https://dash.cloudflare.com/?to=/:account/workers-and-pages
3. Check whether the account already contains GhostCorp-related Workers,
   D1 databases, KV namespaces, or Queues.
4. Do not delete, rename, overwrite, or recreate any existing resources.
5. Send me only the names of the existing GhostCorp Worker and database
   resources, or a screenshot with account IDs, tokens, emails, and other
   private information covered.

I will first adapt the backend to the appropriate Cloudflare storage/runtime
model and prepare the deployment workflow. Only after that will I give you
exact secret names and a direct GitHub settings link. The eventual API token
must be entered directly into GitHub repository Actions secrets — never pasted
into this chat or committed to a file.

Cloudflare official references:
- FastAPI on Python Workers:
  https://developers.cloudflare.com/workers/languages/python/packages/fastapi/
- D1 setup:
  https://developers.cloudflare.com/d1/get-started/
- Workers limits:
  https://developers.cloudflare.com/workers/platform/limits/

Free-tier note: Cloudflare currently documents 100,000 Workers requests/day,
10 ms CPU time per request, and five Cron Triggers per account on Workers Free.
These are bounded serverless resources, not unlimited permanent virtual
machines. D1 also has free-tier query limits. We will scale to actual queue
demand and fail closed rather than create idle workers or surprise charges.

## Handoff 3 — payment provider (only when the payment integration is ready)

The existing site routes customer checkout through Gumroad. The owner must
complete any provider-required seller onboarding and payout verification
inside the provider's own secure dashboard. Do not send identity documents,
bank details, or payout credentials to ChatGPT.

- Gumroad dashboard: https://gumroad.com/dashboard
- Gumroad help center: https://help.gumroad.com/

When the integration is ready, I will provide the exact API credential type,
permission scope, secret name, and GitHub settings page. Keep checkout and
payouts disabled until provider verification, webhook signatures, refunds,
fees, and reconciliation have been tested.

## Handoff 4 — public social publishing (optional; only after the core system)

The public changelog is already part of the existing website. Automated
social publishing is not active. When the core system is ready, choose only
GhostCorp-owned brand accounts that you control. Do not connect a personal
profile or grant broad account permissions just to make posting work.

We will request the minimum provider-supported permissions and store tokens
as encrypted repository/environment secrets. Posts will be drafted and
sanitized first; customer information, credentials, private prompts, hidden
reasoning, and unverified claims must never be published.

## What you do not need to do

- Do not buy hosting, upgrade a plan, or add a payment card for this build.
- Do not create extra GitHub accounts or repositories.
- Do not send me your passwords, API tokens, recovery codes, ID, or bank data.
- Do not change the domain's DNS or existing website structure.
- Do not approve any payment, payout, outreach, or production action until its
  exact scope and effect are shown.

## Current deployment truth

The backend code and tests are committed, and the existing site changelog now
records the work. The backend is not yet deployed to a production host. The
test suite has not yet been confirmed green. No persistent 24/7 AI worker fleet,
live AI executor, payment processor integration, or automated social publisher
is active. These statuses change only after live checks provide evidence.
