#!/usr/bin/env python3
"""Import prospects from the EXISTING ghostcorpnet agency pipeline.

Read-only on the source files. Dedup: one email = one lead, ever.
Opt-outs from the existing operation are loaded as suppressions first, so a
suppressed address can never enter this system as a lead.
Usage: python3 scripts/import_existing_leads.py [leads.jsonl] [optouts.jsonl]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import load_settings
from app.scoring import score_lead
from app.store import Store

DEFAULT_LEADS = os.path.expanduser(
    "~/workspace/goals/kestrelattice-autonomous-growth/hidden_files/agency/leads.jsonl")
DEFAULT_OPTOUTS = os.path.expanduser(
    "~/workspace/goals/kestrelattice-autonomous-growth/hidden_files/outreach/opt-outs.jsonl")


def main() -> int:
    settings = load_settings()
    leads_path = sys.argv[1] if len(sys.argv) > 1 else (settings.existing_leads_path or DEFAULT_LEADS)
    optouts_path = sys.argv[2] if len(sys.argv) > 2 else (settings.existing_optouts_path or DEFAULT_OPTOUTS)
    store = Store(settings.db_path)

    suppressed = 0
    if os.path.exists(optouts_path):
        with open(optouts_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                email = (row.get("email") or row.get("to") or "").strip().lower()
                if email:
                    store.suppress(email, row.get("reason", "existing opt-out"))
                    suppressed += 1

    counts = {"added": 0, "duplicate": 0, "suppressed": 0, "bad_lines": 0}
    with open(leads_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                counts["bad_lines"] += 1
                continue
            lead = {
                "name": row.get("name", ""),
                "email": row.get("email", ""),
                "city": row.get("city", ""),
                "vertical": row.get("vertical", ""),
                "service": row.get("service", ""),
                "source_url": row.get("source_url", ""),
                "source": f"existing-pipeline:{row.get('found_by', 'unknown')}",
                "status": row.get("status", "ready"),
                "created_at": row.get("at", ""),
            }
            score, reasons = score_lead(lead)
            lead["score"], lead["score_reasons"] = score, reasons
            counts[store.add_lead(lead)] += 1
    store.log("import", "import_existing_leads",
              f"from {leads_path}: {counts}, suppressions loaded {suppressed}")
    print(json.dumps({"counts": counts, "suppressions_loaded": suppressed,
                      "summary": store.summary()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
