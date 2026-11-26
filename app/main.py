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

from .ledger import SimulationLedger

ledger = SimulationLedger(settings.db_path)


class LedgerEventIn(BaseModel):
    event_id: str = Field(min_length=3, max_length=120)
    payment_id: str = Field(min_length=3, max_length=120)
    division_slug: str = Field(min_length=3, max_length=40)
    event_type: str = Field(min_length=1, max_length=40)
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=4)
    details: dict = Field(default_factory=dict)


@app.get("/api/ledger/status")
def ledger_status():
    return ledger.summary()


@app.post("/api/ledger/simulate-event", dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def ledger_simulate_event(payload: LedgerEventIn):
    try:
        outcome = ledger.record(payload.event_id, payload.payment_id, payload.division_slug,
                                payload.event_type, payload.amount_minor, payload.currency,
                                payload.details)
        store.log("federation_admin", "ledger_simulation_event", payload.event_id + ":" + outcome)
        return {"outcome": outcome, "mode": "SIMULATED_ONLY"}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


# Durable agent queue. Agents can claim only work assigned to their division.
from .agent_runtime import AgentRuntime
from fastapi import Request

agent_runtime = AgentRuntime(settings.db_path)


def require_agent(authorization: str = Header(default="")):
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "machine bearer token required")
    agent = agent_runtime.authenticate(token)
    if not agent:
        raise HTTPException(403, "invalid or inactive machine identity")
    return agent


class TaskIn(BaseModel):
    task_key: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9._:-]+$")
    division_slug: str = Field(min_length=3, max_length=40)
    required_role: str = Field(default="", max_length=30)
    task_type: str = Field(min_length=2, max_length=60)
    payload: dict = Field(default_factory=dict)


class TaskCompleteIn(BaseModel):
    lease_token: str = Field(min_length=20, max_length=200)
    result: dict = Field(default_factory=dict)


@app.get("/api/runtime/status")
def runtime_status():
    return agent_runtime.status()


@app.post("/api/runtime/tasks", dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def runtime_enqueue(payload: TaskIn):
    if not federation.conn.execute("SELECT 1 FROM divisions WHERE slug=?",
                                   (payload.division_slug,)).fetchone():
        raise HTTPException(404, "division not found")
    allowed = {"coordinator", "researcher", "builder", "tester", "analyst", "operator"}
    if payload.required_role and payload.required_role not in allowed:
        raise HTTPException(422, "unsupported required role")
    outcome = agent_runtime.enqueue(payload.task_key, payload.division_slug,
                                     payload.required_role, payload.task_type, payload.payload)
    return {"outcome": outcome, "mode": "DURABLE_QUEUE"}


@app.post("/api/runtime/claim")
def runtime_claim(agent: dict = __import__("fastapi").Depends(require_agent)):
    return agent_runtime.claim(agent) or {"outcome":"no_matching_task"}


@app.post("/api/runtime/tasks/{task_id}/complete")
def runtime_complete(task_id: int, payload: TaskCompleteIn,
                     agent: dict = __import__("fastapi").Depends(require_agent)):
    if not agent_runtime.complete(agent, task_id, payload.lease_token, payload.result):
        raise HTTPException(409, "task lease invalid, expired, or outside agent division")
    return {"outcome":"completed"}


# Public engineering journal. Writes require the existing federation admin token.
from .build_journal import BuildJournal
build_journal = BuildJournal(settings.db_path)


class BuildJournalIn(BaseModel):
    event_key: str = Field(min_length=3, max_length=120)
    category: str = Field(min_length=1, max_length=30)
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=600)
    state: str = Field(min_length=1, max_length=30)
    commit_ref: str = Field(default="", max_length=40)


@app.get("/api/public/build-journal")
def public_build_journal(limit: int = 30):
    """Read-only public log of explicitly published, sanitized milestones."""
    return build_journal.list_public(limit)


@app.post("/api/build-journal/publish",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def publish_build_journal(payload: BuildJournalIn):
    try:
        outcome = build_journal.publish(payload.model_dump())
        store.log("federation_admin", "public_build_journal", payload.event_key + ":" + outcome)
        return {"outcome": outcome}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
