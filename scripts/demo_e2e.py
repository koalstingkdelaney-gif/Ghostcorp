#!/usr/bin/env python3
"""End-to-end demonstration against real imported data.

Audits the top-N scored leads that have a source URL (timeboxed, safe
crawler), drafts proposals for them, and writes data/demo-report.json.
Nothing is sent anywhere — proposals are drafts only.
Usage: python3 scripts/demo_e2e.py [n]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.audit_site import audit_website
from app.config import load_settings
from app.proposals import build_proposal
from app.store import Store


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    offset = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    settings = load_settings()
    store = Store(settings.db_path)
    report = {"audited": [], "proposals": []}
    candidates = [l for l in store.leads(500) if l.get("source_url")][offset:offset + n]
    for lead in candidates:
        audit = audit_website(lead["source_url"])
        store.set_audit(lead["id"], audit)
        prop = build_proposal(lead, audit)
        pid = store.add_proposal(lead["id"], prop["package"], prop["total_upfront_usd"],
                                 prop["monthly_usd"], prop["body"])
        report["audited"].append({"lead": lead["name"], "url": lead["source_url"],
                                  "evidence": audit["evidence"], "findings": audit["findings"]})
        report["proposals"].append({"lead": lead["name"], "proposal_id": pid,
                                     "package": prop["package"],
                                     "upfront_usd": prop["total_upfront_usd"],
                                     "monthly_usd": prop["monthly_usd"]})
    out = os.path.join(os.path.dirname(settings.db_path) or ".", "demo-report.json")
    with open(out, "w") as f:
        json.dump({"report": report, "summary": store.summary()}, f, indent=2)
    print(json.dumps({"demo_report": out, "audited": len(report["audited"]),
                      "proposals": len(report["proposals"]),
                      "summary": store.summary()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
