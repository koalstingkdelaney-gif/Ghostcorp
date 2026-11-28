# Oracle Always Free deployment kit (owner setup required)

This directory prepares the existing GhostCorp FastAPI backend for a small Ubuntu ARM64 VM. It does not create an Oracle account, provision cloud resources, set DNS, or deploy a service by itself.

## Files

- `compose.yaml`: existing backend container plus Caddy HTTPS origin proxy.
- `Caddyfile`: serves `api-origin.ghostcorpnet.com` over automatically managed HTTPS and forwards to the internal API container.
- `backend.env.example`: placeholder-only private environment template with $0 spend, payments disabled, calling disabled, and SMS disabled.

## Before provisioning

Oracle's Always Free tier currently lists up to 2 OCPUs and 12 GB RAM of Ampere A1 compute and 200 GB total Always Free block-volume storage (including boot volumes), plus five volume backups. Compute and volumes must be provisioned in the account's home region. Always Free compute can be reclaimed if it meets Oracle's documented idle thresholds over a 7-day period. This is not a guaranteed 24/7 SLA.

Oracle account signup requires credit/debit card details for identity verification and may place a temporary authorization hold. Do not proceed unless the owner accepts this requirement. Never upgrade to Pay As You Go or provision trial-only resources under the $0 constraint.

Official sources:
- https://www.oracle.com/cloud/free/
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

## Owner setup sequence

1. Create or sign in to the owner's existing Oracle Cloud account. Select the home region and confirm the Always Free eligibility label before creating any resource.
2. Create one Ubuntu ARM64 Ampere A1 VM using only the Always Free allocation. A conservative initial allocation is 1 OCPU and 6 GB RAM; keep all other compute and storage within the published free quota.
3. Use an SSH public key. Restrict SSH ingress (TCP 22) to the owner's current public IP. Allow inbound TCP 80 and 443 for Caddy HTTPS. Do not open port 8000.
4. Create a separate Always Free block volume in the same home region, attach it to the VM, format it as ext4, and mount it persistently at `/mnt/ghostcorp-data` using its filesystem UUID in `/etc/fstab`. Confirm the mount survives reboot before starting GhostCorp. Keep total boot + block volumes under the Always Free 200 GB quota.
5. Create a DNS-only A record `api-origin.ghostcorpnet.com` pointing to the VM public IP. Do not proxy this origin hostname through the Cloudflare Worker; Caddy must be able to complete HTTPS certificate validation on ports 80/443.
6. Install Docker Engine and the Docker Compose plugin. Clone the existing backend repository to `/opt/ghostcorp`; do not create a replacement repository.
7. Copy `infra/oracle/backend.env.example` to `/etc/ghostcorp/backend.env`. Set restrictive permissions (root-readable only). Fill the owner OAuth values only after creating a GitHub OAuth App. Generate long random values for `FEDERATION_ADMIN_TOKEN`, `OWNER_SESSION_SECRET`, and `PUBLIC_FEEDBACK_RATE_SECRET`. Do not put populated secrets in Git or chat. Leave Gumroad values blank and commerce disabled.
8. From `/opt/ghostcorp/infra/oracle`, build the API image. Determine the container's runtime UID/GID from the built image and chown `/mnt/ghostcorp-data` to that UID/GID so the non-root app user can write SQLite files.
9. Run `docker compose up -d`. The API is exposed only inside the Docker network; Caddy is the only public application listener. Verify `https://api-origin.ghostcorpnet.com/health` and `/ready`.
10. Verify a test write survives API container restart and full VM reboot. Configure encrypted off-host backups and complete a restore drill before storing real customer data.
11. Deploy the Cloudflare Worker from `infra/cloudflare/ghostcorp-api-proxy.js`, set Worker variable `BACKEND_ORIGIN=https://api-origin.ghostcorpnet.com`, and attach only the documented routes from `docs/CLOUDFLARE-API-PROXY.md`.
12. Register the GitHub OAuth callback exactly as `https://ghostcorpnet.com/auth/github/callback`. Verify owner sign-in, sign-out, private API denial when signed out, CSRF rejection, and same-origin behavior.
13. Open `https://ghostcorpnet.com/vr/` in the actual Meta Quest browser and verify the agent panel updates only after owner authentication.

## Commands after owner has completed steps 1–8

From the cloned repository on the VM:

```sh
cd /opt/ghostcorp/infra/oracle
docker compose build api
docker run --rm --entrypoint sh ghostcorp-backend:local -c 'id -u; id -g'
# Use the UID and GID printed above to chown the mounted host data directory.
sudo chown -R <container-uid>:<container-gid> /mnt/ghostcorp-data
docker compose up -d
docker compose ps
docker compose logs --tail=100 api caddy
```

Do not paste the placeholder angle-bracket values literally. Do not run a paid-plan upgrade or accept usage outside Always Free limits.

## Worker compute

This VM kit deploys the API and HTTPS origin only. The AI worker runner is a separate process and needs a compatible local Ollama build/model plus a provisioned machine token. Do not automatically install a large model or start inference without checking ARM64 support, memory/disk headroom, model licence, and Oracle idle-instance policy. Start with the smallest approved model and a low task cap only after the API is stable.

## Known caveats

- Oracle documents idle-instance reclamation for Always Free compute; this can interrupt a low-traffic service.
- Region capacity for A1 instances is not guaranteed.
- The owner must complete provider signup, identity verification, VM/volume provisioning, DNS, OAuth App creation, and private secret configuration.
- No live service is claimed until the end-to-end verification steps pass.
- The $0 spending cap remains in force. If Oracle requires a paid upgrade or any resource would incur a charge, stop and do not proceed.
