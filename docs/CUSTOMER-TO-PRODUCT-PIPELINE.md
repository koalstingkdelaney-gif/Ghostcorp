# Customer-to-product workflow

## Real customer signal

The public website includes a problem-suggestion form. It stores a problem
description and optional context. An email address is retained only when the
submitter explicitly checks permission to receive a reply. Requests are
rate-limited; raw IP addresses are not stored.

The private Action Center lets the owner mark a submission as reviewed or
move it to the roadmap. An owner can then queue a bounded researcher task in
an existing researcher division. Contact details are deliberately excluded
from the agent payload. The current task prompt does not browse the web or
claim external competitor/customer evidence; it produces a validation brief
and labels hypotheses.

## Product draft pipeline

Owner-created product drafts capture the problem, audience, solution,
description, format and proposed price. Validation evidence is recorded as
named checks with explicit pass/fail and evidence notes. Owner approval is
blocked until all recorded checks pass. Approval only changes the draft state
to `APPROVED_FOR_LISTING`; it does not publish to Gumroad.

This registry does not yet create the actual PDF/software package or upload
it to Gumroad. The owner must ensure evidence is genuine; the API records
owner-submitted evidence rather than independently proving interviews or
usability tests.

## Website service workflow

A separate service request form accepts an HTTPS website and contact details
only with explicit permission. An owner triggers the existing SSRF-hardened,
robots-aware audit, drafts a proposal using the existing fixed rate card, and
issues a one-time customer approval link. The owner shares that link
manually; no email is sent automatically.

The customer can accept or decline. Delivery is blocked until the customer
has accepted and the supplied Gumroad sale ID is provider-verified for the
exact mapped service product. The owner then records delivery status and a
public HTTPS deliverable URL. This is a workflow and audit trail, not an
automated website builder or deployment engine.

## Next evidence gates

1. Connect a lawful search/review source for live competitor and customer
   discovery, with source provenance and terms-aware collection.
2. Add interview scheduling and consent-based interview capture only after a
   supported communications provider is configured.
3. Generate actual product artifacts in a restricted build environment.
4. Run automated tests, accessibility checks, package scans and malware
   scanning before release.
5. Connect owner-approved listings to the existing Gumroad products and
   provider-supported publication workflow.
6. Reconcile sales, fees, refunds and payouts using provider data before
   reporting net revenue.
