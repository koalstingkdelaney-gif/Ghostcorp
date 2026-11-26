"""GhostCorp Web Agency API (FastAPI).

Outbound communications are disabled at this layer too: there is no send
endpoint that can fire. Proposals are drafts for the existing gated
pipelines. Calling/SMS endpoints exist only to return the disabled state.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .audit_site import audit_website
from .comms import CommsDisabled, DisabledCommsProvider
from .config import load_settings
from .discovery import DiscoveryRecordError, ingest_results
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


class DiscoveryImportIn(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    results: list[dict] = Field(max_length=100)


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


@app.post("/api/discovery/import")
def import_discovery_results(payload: DiscoveryImportIn):
    """Import structured results from an approved provider adapter; no scraping."""
    guard_mutation()
    try:
        return ingest_results(store, payload.results, payload.provider)
    except DiscoveryRecordError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/leads")
def list_leads(limit: int = 200):
    return store.leads(max(1, min(limit, 5000)))


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


# Identity-minimal federation registry. Provisioning requires a separate
# admin token supplied by the runtime environment; no personal identity data.
import os
import secrets as _secrets
from fastapi import Header
from .federation import FederationRegistry

federation = FederationRegistry(settings.db_path)
FEDERATION_ADMIN_TOKEN = os.environ.get("FEDERATION_ADMIN_TOKEN", "")


def require_federation_admin(x_federation_admin: str = Header(default="")):
    if not FEDERATION_ADMIN_TOKEN:
        raise HTTPException(503, "federation provisioning is locked: admin token is not configured")
    if not _secrets.compare_digest(x_federation_admin, FEDERATION_ADMIN_TOKEN):
        raise HTTPException(403, "federation admin authorization required")
    return True


class DivisionIn(BaseModel):
    slug: str = Field(min_length=3, max_length=40, pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
    display_name: str = Field(min_length=1, max_length=80)
    purpose: str = Field(default="", max_length=500)


class MachineAgentIn(BaseModel):
    division_slug: str = Field(min_length=3, max_length=40)
    role: str = Field(min_length=1, max_length=30)


@app.get("/api/federation/status")
def federation_status():
    return federation.status()


@app.post("/api/federation/divisions", dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def federation_create_division(payload: DivisionIn):
    try:
        division_id = federation.create_division(payload.slug, payload.display_name, payload.purpose)
        store.log("federation_admin", "division_provisioned", payload.slug)
        return {"id": division_id, "slug": payload.slug, "status": "PROVISIONED"}
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/federation/agents", dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def federation_create_agent(payload: MachineAgentIn):
    try:
        result = federation.create_agent(payload.division_slug, payload.role)
        store.log("federation_admin", "machine_agent_provisioned", result["machine_id"])
        return result  # token is returned once; only its hash is stored
    except (ValueError, LookupError) as exc:
        raise HTTPException(400, str(exc)) from exc
