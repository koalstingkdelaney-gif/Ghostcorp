# Product requirements (summary of the brief, as built)

1. Prospect discovery — via the existing company's pipeline import (compliant,
   public business data, provenance recorded). Direct search-API prospecting
   is a later phase behind an adapter.
2. Website audit — implemented (`app/audit_site.py`), evidence-backed.
3. Lead qualification — implemented, transparent scoring + dedup + suppression.
4. Sales workflow — proposal drafts from the existing live rate card only.
5. Calling/SMS — interface only, disabled; prerequisites in PROVIDER_SETUP.md.
6. Website production — later phase (Phase 3 of the brief); the existing
   company already delivers sites through its client-work flow.
7. QA — automated tests in `tests/`; audit findings gate proposals (findings
   are quoted in the draft, never invented).
8. Billing — disabled until owner provider onboarding (Stripe Checkout in
   test mode is the Phase 4 step).
9. Delivery/hosting — later phase; deploy config added with the cloud host.
10. Maintenance/reporting — dashboard summary endpoint + audit log today.
11. Owner dashboard — summary API today; the owner already has the company
    admin panel for approvals.
12. Continuous improvement — job/audit logs provide conversion inputs.
