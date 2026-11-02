"""GhostCorp Web Agency API (FastAPI).

Outbound communications are disabled at this layer too: there is no send
endpoint that can fire. Proposals are drafts for the existing gated
pipelines. Calling/SMS endpoints exist only to return the disabled state.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import __version__
from .audit_site import audit_website
from .comms import CommsDisabled, DisabledCommsProvider
from .config import load_settings
from .governor import SpendGovernor
from .jobs import run_pending
from .proposals import PACKAGES, build_proposal
from .scoring import score_lead
from .store import Store

settings = load_settings()
store = Store(settings.db_path)
governor = SpendGovernor(settings.spend_cap_usd)
comms = DisabledCommsProvider(settings.calling_enabled, settings.sms_enabled)

app = FastAPI(title="GhostCorp Web Agency", version=__version__)


def guard_mutation():
    if settings.paused:
        raise HTTPException(503, "agency is paused by the global kill switch (AGENCY_PAUSED)")


class LeadIn(BaseModel):
    name: str
    email: str
    city: str = ""
    vertical: str = ""
    service: str = ""
    source_url: str = ""
    source: str = "api"


@app.get("/health")
def health():
    return {"ok": True, "version": __version__, "paused": settings.paused}


@app.get("/ready")
def ready():
    return {
        "ok": True,
        "spend_cap_usd": governor.cap_usd,
        "spent_usd": governor.spent_usd,
        "payments_mode": settings.payments_mode,
        "calling_enabled": settings.calling_enabled,
        "sms_enabled": settings.sms_enabled,
        "summary": store.summary(),
    }


@app.get("/api/packages")
def packages():
    return PACKAGES


@app.post("/api/leads")
def add_lead(lead: LeadIn):
    guard_mutation()
    data = lead.model_dump()
    score, reasons = score_lead(data)
    data["score"], data["score_reasons"] = score, reasons
    outcome = store.add_lead(data)
    store.log("api", "lead_add", f"{data['email']}: {outcome}")
    return {"outcome": outcome, "score": score, "reasons": reasons}


@app.get("/api/leads")
def list_leads(limit: int = 200):
    return store.leads(limit)


@app.post("/api/leads/{lead_id}/audit")
def audit_lead(lead_id: int):
    guard_mutation()
    lead = store.lead(lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    audit = audit_website(lead["source_url"])
    store.set_audit(lead_id, audit)
    return audit


@app.post("/api/leads/{lead_id}/proposal")
def draft_proposal(lead_id: int):
    guard_mutation()
    lead = store.lead(lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    import json
    audit = json.loads(lead["audit"] or "{}") or None
    prop = build_proposal(lead, audit)
    pid = store.add_proposal(lead_id, prop["package"], prop["total_upfront_usd"],
                             prop["monthly_usd"], prop["body"])
    return {"proposal_id": pid, **prop}


@app.post("/api/jobs/run")
def jobs_run():
    guard_mutation()
    return run_pending(store)


@app.get("/api/dashboard/summary")
def dashboard():
    return store.summary()


@app.post("/api/comms/call")
def call():
    try:
        comms.place_call("", "", None)
    except CommsDisabled as e:
        raise HTTPException(403, str(e))


@app.post("/api/comms/sms")
def sms():
    try:
        comms.send_sms("", "", None)
    except CommsDisabled as e:
        raise HTTPException(403, str(e))
