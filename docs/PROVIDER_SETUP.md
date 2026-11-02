# Provider setup — owner-only steps

Nothing below can be done by an agent. Each step happens in the provider's
own official dashboard, by the owner. No passwords, codes, keys, or card
numbers ever go through chat.

## Payments (Stripe) — unlocks charging customers
1. Owner signs in at stripe.com, completes business/identity verification
   and payout (bank) details there.
2. Owner creates the account in **test mode** first; Phase 4 integration is
   tested against test checkout + signed webhooks before any live charge.
3. Keys are placed in the deployment's secret store by the owner; the app
   reads `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` from the environment.

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
