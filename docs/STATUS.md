# Status — 2026-11-23

## Repository work completed in this update

- Added `app/discovery.py`: provider-neutral ingestion boundary for structured
  business-search results. It makes no network requests and does not scrape
  search-engine result pages.
- Added guarded `POST /api/discovery/import` to the FastAPI app. It enforces
  the global pause switch, limits batches to 100, requires provider provenance,
  validates source URL shape, rejects local/private literal IPs and URLs with
  embedded credentials, and delegates deduplication/opt-out suppression to
  the existing store.
- Added `tests/test_discovery.py` for provenance, unsafe URLs, deduplication,
  suppression, invalid records, and batch limits.
- Updated README to distinguish the ingestion boundary from a live provider.

## Verification state

- GitHub accepted the commits for the new module, API integration, and tests.
- **Tests have not been executed in this environment.** Do not report them as
  passing until CI or a local test run confirms it.
- The discovery endpoint is not connected to a live search/business-data
  provider. It is ready to receive structured results from a separately
  approved adapter; that adapter remains future work.

## Existing Phase 0 + Phase 1 claims (historical, dated 2026-11-02)

The prior status reported 10/10 tests passing on 2026-11-02, a read-only import
of 6,748 leads, 12 opt-out suppressions, 10 audited prospects, and 10 proposal
drafts. Those are historical claims from the previous status report, not
freshly rerun or independently reverified in this update.

## Still blocked / not proven

- Cloud deployment: no production host or live URL verified.
- Payments: disabled; provider onboarding and test-mode integration remain.
- Calling/SMS: disabled; compliance and provider prerequisites remain.
- Live discovery provider: not connected.
- Revenue: no verified customer payment or revenue established.
- CI: must run the test suite and security checks before treating this update
  as verified.

## Operating constraints

- External paid API spend remains $0 before revenue.
- No outbound marketing messages, calls, or texts are enabled.
- No credentials or payment-card data belong in Git.
- Owner approval remains required for spending, paid-provider activation,
  payout changes, customer-facing publication, and production deployment.
