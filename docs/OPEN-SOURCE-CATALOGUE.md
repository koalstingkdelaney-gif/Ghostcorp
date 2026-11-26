# Open-Source and Free-Service Research Catalogue

**Purpose:** identify useful infrastructure for GhostCorp without assuming a service is free forever, identity-free, production-grade, or suitable for sensitive data.

## Hosting candidates

### Cloudflare Workers + D1 + Queues + R2
- Docs: https://developers.cloudflare.com/workers/
- Limits: https://developers.cloudflare.com/workers/platform/limits/
- D1: https://developers.cloudflare.com/d1/
- Queues: https://developers.cloudflare.com/queues/
- R2: https://developers.cloudflare.com/r2/
- Fit: edge APIs, event handlers, short tasks, scheduled wake-ups, static assets, durable storage.
- Current documented Workers Free constraints include 100,000 requests/day, 10 ms CPU per request, 128 MB memory, up to 100 Workers, and five Cron Triggers per account. D1/Queues/R2 have their own quotas and limits.
- Not a general-purpose persistent Linux VM or a place to run large model inference continuously.

### GitHub Actions
- Docs: https://docs.github.com/en/actions
- Limits: https://docs.github.com/en/actions/reference/limits
- Fit: CI, tests, builds, scheduled maintenance, release jobs, bounded burst workers.
- GitHub Free standard hosted runner concurrency is documented as 20, with included monthly compute allowance and storage caps. Jobs are temporary; they are not persistent servers.

### Render Free
- Docs: https://render.com/docs/free
- Quickstart: https://render.com/docs/your-first-deploy
- Fit: previews and low-risk prototypes.
- Limitations: free web services spin down after 15 minutes idle; local filesystem is ephemeral; free Postgres expires after 30 days; not suitable as the production durable database or guaranteed 24/7 worker host.

### Deno Deploy
- Pricing: https://deno.com/deploy/pricing
- Fit: edge application hosting and API experiments.
- Evaluate compatibility, quotas, account requirements, and persistent background-task support before choosing it for core workloads.

## Model and agent infrastructure

### Ollama
- Quickstart: https://docs.ollama.com/quickstart
- API: https://docs.ollama.com/api
- GitHub: https://github.com/ollama/ollama
- Fit: local model serving without a cloud API key for local requests. Cloud model usage is a separate service and requires account/API authentication.
- Important: model size is constrained by available RAM/VRAM/storage. The user's phone should not be assumed to be a reliable always-on model server.

### llama.cpp
- GitHub: https://github.com/ggml-org/llama.cpp
- Fit: efficient quantized local inference on supported CPU/GPU hardware.

### LangGraph
- Docs: https://docs.langchain.com/oss/python/langgraph/overview
- Fit: explicit stateful agent graphs, checkpoints, human-in-the-loop workflow design.

### Temporal
- Docs: https://docs.temporal.io/
- Durable execution: https://docs.temporal.io/durable-execution
- Fit: long-running workflows that resume after crashes and infrastructure outages. It requires a running Temporal service or managed hosting; it does not itself provide free compute.

### LiteLLM
- Docs: https://docs.litellm.ai/
- GitHub: https://github.com/BerriAI/litellm
- Fit: model-provider abstraction, routing, key management, budgets, and usage reporting. It does not make paid model inference free.

### n8n
- Docs: https://docs.n8n.io/
- GitHub: https://github.com/n8n-io/n8n
- Fit: integration automation and human-reviewed workflows. Self-hosting transfers maintenance, security, and uptime responsibility to GhostCorp.

## Storage, search, and knowledge

- PostgreSQL: https://www.postgresql.org/ — primary relational database for multi-worker production.
- SQLite: https://www.sqlite.org/ — local development, tests, and single-process deployments; not the shared multi-host production database.
- pgvector: https://github.com/pgvector/pgvector — vector similarity in PostgreSQL.
- Qdrant: https://qdrant.tech/ — vector search service; evaluate hosting cost and access controls.
- MinIO: https://min.io/ — S3-compatible object storage for self-hosted environments; self-hosting requires persistent disks and operations.
- MkDocs Material: https://squidfunk.github.io/mkdocs-material/ — searchable project documentation.

## Identity, email, and secrets

### SimpleLogin
- Website: https://simplelogin.io/
- GitHub: https://github.com/simple-login/app
- Fit: durable role-based email aliases and forwarding; supports self-hosting.
- An alias hides the destination address from correspondents but is not a separate fully independent mailbox and does not guarantee that upstream providers will accept signup without verification.

### Proton human verification
- Policy: https://proton.me/support/human-verification
- Proton may require CAPTCHA, phone, or email verification depending on signup risk signals. Do not automate repeated account creation or attempt to bypass anti-abuse checks.

### OpenBao
- GitHub: https://github.com/openbao/openbao
- Fit: self-hosted secrets management. Requires secure deployment, backups, and key management.

### SOPS + age
- SOPS: https://github.com/getsops/sops
- age: https://github.com/FiloSottile/age
- Fit: encrypted configuration/secrets in controlled repositories and deployment pipelines.

### Keycloak
- Website: https://www.keycloak.org/
- GitHub: https://github.com/keycloak/keycloak
- Fit: self-hosted identity and access management for internal applications; not a replacement for third-party KYC.

## Wallets and payments

### MetaMask
- Create wallet: https://support.metamask.com/start/creating-a-new-wallet/
- Self-custody explanation: https://support.metamask.com/start/metamask-is-a-self-custodial-wallet
- Fit: user-controlled self-custody wallet. A self-custody wallet can be created without opening a custodial exchange account, but it does not provide fiat on/off ramps or merchant card processing. Recovery phrase security is entirely critical.

### BTCPay Server
- Website: https://btcpayserver.org/
- Docs: https://docs.btcpayserver.org/
- Deployment FAQ: https://docs.btcpayserver.org/FAQ/Deployment/
- GitHub: https://github.com/btcpayserver/btcpayserver
- Fit: free/open-source self-hosted Bitcoin payment processor; can let a merchant receive Bitcoin directly.
- Hosting, node operation, wallet security, accounting, customer refunds, exchange to fiat, and compliance remain separate responsibilities. It does not accept ordinary card payments by itself.

### Gumroad
- Payout settings: https://gumroad.com/help/article/260-your-payout-settings-page
- Current help content describes US payout details and a PayPal payout path that may not require ID documents in that specific flow, but still asks for name, address, phone, and an active PayPal account email. This is not anonymous payout and is not a promise that every seller/account will qualify.
- Any seller onboarding, tax reporting, payment processor verification, and payout controls must be completed truthfully in the provider dashboard.

### Stripe
- Verification overview: https://support.stripe.com/questions/payouts-or-charges-not-enabled-for-custom-connected-accounts
- Stripe says verification requirements vary by country, business type, and payment capabilities. Do not design the platform around avoiding required verification.

## Observability and security

- OpenTelemetry: https://opentelemetry.io/
- Prometheus: https://prometheus.io/
- Grafana: https://grafana.com/oss/
- Loki: https://grafana.com/oss/loki/
- Trivy: https://github.com/aquasecurity/trivy
- Syft: https://github.com/anchore/syft
- Grype: https://github.com/anchore/grype
- Renovate: https://github.com/renovatebot/renovate
- Playwright: https://playwright.dev/

## VR and simulation

- Godot: https://godotengine.org/
- Godot OpenXR: https://docs.godotengine.org/en/stable/tutorials/xr/openxr.html
- OpenXR: https://www.khronos.org/openxr/
- Fit: native VR environment, simulation, avatar/robot visualization, and private owner control surfaces. Keep the business backend authoritative; VR is a client.

## Selection policy

Before adding any candidate to production:
1. Confirm the project is active and review its security/advisory history.
2. Confirm license compatibility for the intended commercial use.
3. Confirm exact runtime, architecture, memory, storage, and network requirements.
4. Confirm whether it needs an account, phone, payment card, identity verification, or paid plan.
5. Confirm its free-tier quotas and what happens when quotas are exceeded.
6. Confirm data location, retention, export, backup, and deletion options.
7. Add it behind an adapter and feature flag.
8. Run tests and a rollback/exit test before routing real customer or financial data.

## Identity and payment boundary

GhostCorp can use pseudonymous business branding, internal machine identities, email aliases, and self-custody crypto wallets where permitted. It cannot use fake personal details, borrowed identities, fabricated tax information, multiple accounts to bypass limits, or automation that evades KYC/AML or platform anti-abuse systems. If a provider requires real-world verification for merchant services or payouts, that step remains external and owner-controlled. Until it is completed, the integration stays disabled or simulation-only.
