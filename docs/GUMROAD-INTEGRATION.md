# Existing Gumroad checkout and sales verification

## Keep the existing provider

The current public site links buyers to the existing store:
`https://ghostcorpnet.gumroad.com/`. Do not create a duplicate checkout
provider or collect card details in GhostCorp. Gumroad remains responsible for
checkout and its own digital-product delivery.

## Read-only sales verification implemented

The backend now accepts Gumroad Ping form posts at:

`POST /webhooks/gumroad/{GUMROAD_PING_SECRET}`

The webhook does not trust the incoming Ping as proof of payment. It takes the
sale ID and verifies it with the authenticated Gumroad sales API before
recording the event. Only sale IDs for the explicit product allowlist are
accepted. Duplicate events are idempotent. Refund pings update a sale only
when Gumroad's authenticated sale record confirms it is refunded.

Stored fields are limited to sale ID, product permalink, provider status,
raw amount, currency, provider timestamp and verification timestamps. Buyer
email and card details are not stored. Unsupported resource events are
acknowledged but not applied. The current integration does not move money,
change payout settings, issue refunds, publish products, or deliver products
outside Gumroad.

The raw `price` value is deliberately retained without converting it to
dollars/cents until the provider amount-unit contract is confirmed in an
integration test. Revenue reports must not sum or display it as dollars yet.

## Required environment variables

- `GUMROAD_ACCESS_TOKEN`: create an application/token in Gumroad with only
  `view_sales` access where supported.
- `GUMROAD_PING_SECRET`: a random secret of at least 32 characters. Configure
  the same value in the Ping endpoint path and the backend secret manager.
- `GUMROAD_ALLOWED_PERMALINKS`: comma-separated exact product permalinks
  that GhostCorp intends to track.
- `GUMROAD_SERVICE_PACKAGE_MAP`: semicolon-separated package mappings, for
  as `AI Website=confirmed-permalink:raw-price:USD;AI Front Desk=confirmed-permalink:raw-price:USD`.
  The raw amount must exactly match Gumroad's verified API `price` field;
  GhostCorp deliberately does not convert units. Set only after each
  corresponding service product exists in the store and a real test sale
  confirms its exact permalink, raw amount and currency.

The existing public site currently references these Gumroad permalinks:
`ihqce`, `lttjbc`, `tsrwbt`, `hdigmr`, `yzbumc`, `bbxnne`,
`sahva`, `jbngbu`, `cjdkuu`, and `stop-the-bleed-pair`.
This list is derived from current website links; confirm the products are
still published and owned by the GhostCorp store before adding them to the
server-side allowlist.

## Configure Gumroad Ping

In Gumroad's advanced settings, configure the Ping URL to the deployed
backend's HTTPS route, including the secret path. If the static website and
backend use the same origin, route `/webhooks/gumroad/*` through the reverse
proxy to FastAPI. If the backend uses a dedicated API host, use that host's
verified HTTPS URL instead.

## Customer service delivery gate

The website-service workflow requires a customer approval decision and a
provider-verified Gumroad sale whose product permalink matches the package
mapping before an owner can mark delivery in progress. This prevents a sale
for an unrelated product from authorizing a service job.

No automatic customer email is sent. The owner must share the one-time
proposal approval link manually. Payment checkout and service scheduling
remain separate steps. Gumroad's own digital products continue to be
delivered by Gumroad.

## Limits

The current adapter handles `sale` and `refund` Pings. Disputes, chargebacks,
subscriptions, payouts, fees reconciliation, automatic customer fulfilment,
and automatic product publishing are not implemented. The integration has
mocked API tests only; no live Gumroad token or production Ping has been
configured or tested.
