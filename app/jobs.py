"""Durable, idempotent job runner over the store's jobs table."""
import json

from .audit_site import audit_website
from .proposals import build_proposal
from .scoring import score_lead


def run_pending(store, limit: int = 50) -> dict:
    done = failed = 0
    for job in store.pending_jobs(limit):
        payload = json.loads(job["payload"] or "{}")
        try:
            if job["kind"] == "audit_lead":
                lead = store.lead(payload["lead_id"])
                audit = audit_website(lead["source_url"] or payload.get("url", ""))
                store.set_audit(lead["id"], audit)
                store.log("jobs", "audit_lead", f"lead {lead['id']}: {audit['evidence']}")
            elif job["kind"] == "draft_proposal":
                lead = store.lead(payload["lead_id"])
                audit = json.loads(lead["audit"] or "{}") or None
                prop = build_proposal(lead, audit)
                pid = store.add_proposal(lead["id"], prop["package"],
                                         prop["total_upfront_usd"], prop["monthly_usd"], prop["body"])
                store.log("jobs", "draft_proposal", f"lead {lead['id']} -> proposal {pid}")
            elif job["kind"] == "rescore_lead":
                lead = store.lead(payload["lead_id"])
                score, reasons = score_lead(lead)
                store.conn.execute(
                    "UPDATE leads SET score=?, score_reasons=? WHERE id=?",
                    (score, json.dumps(reasons), lead["id"]),
                )
                store.conn.commit()
            else:
                raise ValueError(f"unknown job kind {job['kind']}")
            store.finish_job(job["id"], "done")
            done += 1
        except Exception as e:  # recorded, never silently swallowed
            store.finish_job(job["id"], "failed", f"{type(e).__name__}: {e}")
            store.log("jobs", "job_failed", f"job {job['id']}: {e}")
            failed += 1
    return {"done": done, "failed": failed}
