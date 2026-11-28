# Provider setup — owner-only steps

Nothing below can be done by an agent. Each step happens in the provider's
own official dashboard, by the owner. No passwords, codes, keys, or card
numbers ever go through chat.

## Existing Gumroad checkout — no new payment processor
1. Keep the existing GhostCorp Gumroad storefront and product checkout links.
   Customers continue to pay through Gumroad's enabled payment methods.
2. If the owner wants server-side sale tracking, create a Gumroad API token
   with read-only `view_sales` access in Gumroad's official dashboard.
3. Configure the Gumroad Ping URL to the deployed backend's secret route,
   then set `GUMROAD_ACCESS_TOKEN`, `GUMROAD_PING_SECRET`, and the exact
   `GUMROAD_ALLOWED_PERMALINKS` in the host's private secret store.
4. For service delivery, set `GUMROAD_SERVICE_PACKAGE_MAP` only after a
   test sale confirms each service product's exact permalink, raw API price
   value and currency. Do not assume price units or map an unrelated product.
5. Gumroad remains responsible for checkout and digital-product delivery.
   GhostCorp's integration is read-only verification and an internal ledger;
   it does not change payout settings, move money, refund customers or
   introduce Stripe as another checkout provider.

## Voice/SMS (e.g. Twilio) — unlocks calling, only when ALL are true
1. Owner completes provider onboarding and business/identity verification.
2. Required voice/SMS registrations are approved.
3. A lawful basis / documented consent exists for each recipient —
   a public phone number is **not** consent, and unsolicited automated
   marketing calls/texts stay off, permanently.
4. Owner-approved scripts, calling-hour controls, caller ID, opt-out/STOP
   handling, and suppression lists are active and tested.
5. Owner flips `CALLING_ENABLED` / `SMS_ENABLED` in configuration.
Until then `app/comms.py` refuses every call and text.

## GitHub Actions CI — unlocks automated test runs on push
The fleet GitHub token currently has scopes `gist, read:org, repo` (no
`workflow`). After the owner re-authorizes the token with the `workflow`
scope, add the workflow in `docs/CI.md`.

## Cloud hosting — unlocks a public deployment
Owner picks/approves a managed host (e.g. Cloudflare Pages for customer
sites + a managed app host for this API) and completes any account
verification there. Deploy config is added at that point; until then the
service runs locally and is fully testable.
