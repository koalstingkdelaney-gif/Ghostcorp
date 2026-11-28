"""GhostCorp Web Agency API (FastAPI).

Outbound communications are disabled at this layer too: there is no send
endpoint that can fire. Proposals are drafts for the existing gated
pipelines. Calling/SMS endpoints exist only to return the disabled state.
"""
from fastapi import FastAPI, HTTPException, Header, Depends, Cookie, Request
from fastapi.responses import RedirectResponse
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
from .customer_feedback import CustomerFeedback, FeedbackError
from .product_pipeline import ProductPipeline, ProductPipelineError

settings = load_settings()
store = Store(settings.db_path)
customer_feedback = CustomerFeedback(settings.db_path)
product_pipeline = ProductPipeline(settings.db_path)
governor = SpendGovernor(settings.spend_cap_usd)
comms = DisabledCommsProvider(settings.calling_enabled, settings.sms_enabled)

# One owner-admin gate protects private business records and mutations.
# The secret is supplied only by the deployment environment, never Git.
import os
import secrets as _secrets
import os

FEDERATION_ADMIN_TOKEN = os.environ.get("FEDERATION_ADMIN_TOKEN", "")


from . import owner_auth


def require_federation_admin(
    request: Request,
    x_federation_admin: str = Header(default=""),
    ghostcorp_owner_session: str = Cookie(default="", alias=owner_auth.SESSION_COOKIE),
    x_csrf_token: str = Header(default=""),
):
    # Machine/admin API clients may use the deployment-only bearer-like header.
    if FEDERATION_ADMIN_TOKEN and _secrets.compare_digest(
        x_federation_admin, FEDERATION_ADMIN_TOKEN
    ):
        return True

    # Browser owner sessions are accepted only after GitHub OAuth identity
    # verification and require CSRF + exact same-origin checks on mutations.
    session = owner_auth.read_session(ghostcorp_owner_session)
    if not session:
        if not FEDERATION_ADMIN_TOKEN:
            raise HTTPException(503, "owner admin access is locked: sign-in is not configured")
        raise HTTPException(403, "owner admin authorization required")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin", "").rstrip("/")
        if not origin or not _secrets.compare_digest(origin, owner_auth.site_origin()):
            raise HTTPException(403, "same-origin request required")
        if not _secrets.compare_digest(x_csrf_token, str(session["csrf"])):
            raise HTTPException(403, "CSRF validation failed")
    return True


app = FastAPI(title="GhostCorp Web Agency", version=__version__)


@app.get("/auth/status")
def owner_auth_status():
    return {"configured": owner_auth.configured(), "provider": "github_oauth",
            "session_hours": 8, "mode": "OWNER_ALLOWLIST_REQUIRED"}


@app.get("/auth/github/start")
def owner_github_start():
    try:
        url, state_cookie = owner_auth.issue_state()
    except owner_auth.OwnerAuthUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    response = RedirectResponse(url, status_code=302)
    response.set_cookie(owner_auth.STATE_COOKIE if hasattr(owner_auth, "STATE_COOKIE") else "ghostcorp_oauth_state",
                        state_cookie, max_age=600, httponly=True, secure=True,
                        samesite="lax", path="/")
    return response


@app.get("/auth/github/callback")
def owner_github_callback(code: str = "", state: str = "",
                          ghostcorp_oauth_state: str = Cookie(default="")):
    try:
        session, csrf = owner_auth.complete_login(code, state, ghostcorp_oauth_state)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except owner_auth.OwnerAuthUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, "GitHub sign-in could not be completed") from exc
    response = RedirectResponse(owner_auth.site_origin() + "/vr/", status_code=303)
    response.delete_cookie("ghostcorp_oauth_state", path="/")
    response.set_cookie(owner_auth.SESSION_COOKIE, session, max_age=8 * 60 * 60,
                        httponly=True, secure=True, samesite="lax", path="/")
    response.set_cookie(owner_auth.CSRF_COOKIE, csrf, max_age=8 * 60 * 60,
                        httponly=False, secure=True, samesite="lax", path="/")
    return response


@app.get("/auth/me")
def owner_auth_me(ghostcorp_owner_session: str = Cookie(default="", alias=owner_auth.SESSION_COOKIE)):
    session = owner_auth.read_session(ghostcorp_owner_session)
    if not session:
        return {"authenticated": False}
    return {"authenticated": True, "owner": session["sub"], "csrf_token": session["csrf"],
            "expires_at": session["exp"]}


@app.post("/auth/logout")
def owner_auth_logout(request: Request,
                      ghostcorp_owner_session: str = Cookie(default="", alias=owner_auth.SESSION_COOKIE),
                      x_csrf_token: str = Header(default="")):
    session = owner_auth.read_session(ghostcorp_owner_session)
    if session:
        origin = request.headers.get("origin", "").rstrip("/")
        if not origin or not _secrets.compare_digest(origin, owner_auth.site_origin()):
            raise HTTPException(403, "same-origin request required")
        if not _secrets.compare_digest(x_csrf_token, str(session["csrf"])):
            raise HTTPException(403, "CSRF validation failed")
    response = RedirectResponse(owner_auth.site_origin() + "/", status_code=303)
    response.delete_cookie(owner_auth.SESSION_COOKIE, path="/")
    response.delete_cookie(owner_auth.CSRF_COOKIE, path="/")
    return response


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


class PublicProblemSubmissionIn(BaseModel):
    problem: str = Field(min_length=20, max_length=2000)
    context: str = Field(default="", max_length=1500)
    email: str = Field(default="", max_length=254)
    contact_permission: bool = False
    website: str = Field(default="", max_length=120)


class ProblemSubmissionReviewIn(BaseModel):
    status: str = Field(pattern=r"^(REVIEWED|ROADMAP|CLOSED)$")


class CustomerResearchTaskIn(BaseModel):
    division_slug: str = Field(min_length=3, max_length=40)


class ProductDraftIn(BaseModel):
    source_submission_id: int = Field(default=0, ge=0)
    title: str = Field(min_length=4, max_length=120)
    problem: str = Field(min_length=20, max_length=2000)
    audience: str = Field(min_length=5, max_length=300)
    solution: str = Field(min_length=20, max_length=2000)
    description: str = Field(min_length=40, max_length=5000)
    format: str = Field(min_length=2, max_length=20)
    proposed_price_cents: int = Field(default=0, ge=0, le=1000000)


class ProductValidationIn(BaseModel):
    checks: list[dict] = Field(min_length=3, max_length=20)
    evidence_summary: str = Field(min_length=20, max_length=1500)


class ProductDecisionIn(BaseModel):
    decision: str = Field(pattern=r"^(APPROVED_FOR_LISTING|REJECTED)$")


@app.post("/api/public/problem-submissions")
def submit_customer_problem(payload: PublicProblemSubmissionIn, request: Request):
    """Accept a product-problem suggestion without exposing private business records."""
    guard_mutation()
    if payload.website.strip():  # Honeypot: silently accept automated spam.
        return {"accepted": True}
    client_ip = request.client.host if request.client else "unknown"
    rate_secret = os.environ.get("PUBLIC_FEEDBACK_RATE_SECRET", "")
    if not rate_secret or len(rate_secret) < 32:
        raise HTTPException(503, "public feedback intake is not configured")
    try:
        fingerprint = customer_feedback.fingerprint(client_ip, rate_secret)
        customer_feedback.submit(payload.problem, payload.context, payload.email,
                                 payload.contact_permission, fingerprint)
        store.log("public", "customer_problem_received", "new submission")
        return {"accepted": True,
                "message": "Thank you. Your problem suggestion has been received for review."}
    except FeedbackError as exc:
        message = str(exc)
        if "rate-limit secret" in message:
            raise HTTPException(503, message) from exc
        raise HTTPException(422, message) from exc


@app.get("/api/customer/problem-submissions",
         dependencies=[Depends(require_federation_admin)])
def list_customer_problem_submissions(status: str = "NEW", limit: int = 100):
    try:
        return {"items": customer_feedback.list(status, limit)}
    except FeedbackError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/customer/problem-submissions/{submission_id}/review",
          dependencies=[Depends(require_federation_admin)])
def review_customer_problem_submission(submission_id: int,
                                        payload: ProblemSubmissionReviewIn):
    guard_mutation()
    try:
        result = customer_feedback.update_status(submission_id, payload.status)
        store.log("federation_admin", "customer_problem_review",
                  str(submission_id) + ":" + payload.status)
        return result
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except FeedbackError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/customer/problem-submissions/{submission_id}/research",
          dependencies=[Depends(require_federation_admin)])
def queue_customer_problem_research(submission_id: int, payload: CustomerResearchTaskIn):
    """Turn an owner-selected customer problem into a bounded researcher task."""
    submission = customer_feedback.get(submission_id)
    if not submission:
        raise HTTPException(404, "submission not found")
    if submission["status"] not in {"ROADMAP", "REVIEWED"}:
        raise HTTPException(409, "review the submission before creating a research task")
    division = federation.conn.execute(
        "SELECT slug FROM divisions WHERE slug=?", (payload.division_slug,)
    ).fetchone()
    if not division:
        raise HTTPException(404, "research division not found")
    # Contact email is deliberately excluded from the agent task.
    prompt = (
        "Prepare a customer-problem validation brief using only the supplied "
        "description and general knowledge. Do not claim to have browsed or "
        "verified competitors. Separate observed facts from hypotheses. Include: "
        "customer segments to interview, jobs-to-be-done, current workaround "
        "hypotheses, competing solution categories to investigate, 8 neutral "
        "interview questions, a low-cost validation experiment, possible product "
        "approaches, risks, and what evidence would disprove the idea. Do not "
        "contact anyone or make purchases.\n\nPROBLEM:\n" + submission["problem"] +
        "\n\nCONTEXT:\n" + submission["context"]
    )
    outcome = agent_runtime.enqueue(
        "customer-problem-" + str(submission_id) + "-research-v1",
        payload.division_slug, "researcher", "research_summary",
        {"privacy_class": "internal", "prompt": prompt, "max_output_tokens": 900,
         "source_submission_id": submission_id, "tools_enabled": False}
    )
    store.log("federation_admin", "customer_research_queued",
              str(submission_id) + ":" + outcome)
    return {"outcome": outcome, "mode": "QUEUED_FOR_RESEARCHER",
            "source_submission_id": submission_id,
            "contact_data_shared": False,
            "research_limit": "No live web search or external contact is performed by this task."}


@app.post("/api/products/drafts",
          dependencies=[Depends(require_federation_admin)])
def create_product_draft(payload: ProductDraftIn):
    guard_mutation()
    data = payload.model_dump()
    source_id = data["source_submission_id"]
    if source_id:
        source = customer_feedback.get(source_id)
        if not source or source["status"] not in {"ROADMAP", "REVIEWED"}:
            raise HTTPException(409, "source customer problem must be reviewed first")
    try:
        result = product_pipeline.create(data)
        store.log("federation_admin", "product_draft_created", str(result["id"]))
        return result
    except ProductPipelineError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/products/drafts",
         dependencies=[Depends(require_federation_admin)])
def list_product_drafts(status: str = "ALL", limit: int = 100):
    try:
        return {"items": product_pipeline.list(status, limit)}
    except ProductPipelineError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/products/drafts/{product_id}/validation",
          dependencies=[Depends(require_federation_admin)])
def record_product_validation(product_id: int, payload: ProductValidationIn):
    guard_mutation()
    try:
        result = product_pipeline.record_validation(
            product_id, payload.checks, payload.evidence_summary)
        store.log("federation_admin", "product_validation_recorded", str(product_id))
        return result
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ProductPipelineError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/products/drafts/{product_id}/decision",
          dependencies=[Depends(require_federation_admin)])
def decide_product_draft(product_id: int, payload: ProductDecisionIn):
    guard_mutation()
    try:
        result = product_pipeline.decide(product_id, payload.decision)
        store.log("federation_admin", "product_owner_decision",
                  str(product_id) + ":" + payload.decision)
        return {"product": result, "published": False,
                "note": "Approval only prepares a listing. It does not publish to Gumroad."}
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ProductPipelineError as exc:
        raise HTTPException(409, str(exc)) from exc


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


@app.post("/api/leads", dependencies=[Depends(require_federation_admin)])
def add_lead(lead: LeadIn):
    guard_mutation()
    data = lead.model_dump()
    score, reasons = score_lead(data)
    data["score"], data["score_reasons"] = score, reasons
    outcome = store.add_lead(data)
    store.log("api", "lead_add", f"{data['email']}: {outcome}")
    return {"outcome": outcome, "score": score, "reasons": reasons}


@app.post("/api/discovery/import", dependencies=[Depends(require_federation_admin)])
def import_discovery_results(payload: DiscoveryImportIn):
    """Import structured results from an approved provider adapter; no scraping."""
    guard_mutation()
    try:
        return ingest_results(store, payload.results, payload.provider)
    except DiscoveryRecordError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/leads", dependencies=[Depends(require_federation_admin)])
def list_leads(limit: int = 200):
    return store.leads(max(1, min(limit, 5000)))


@app.post("/api/leads/{lead_id}/audit", dependencies=[Depends(require_federation_admin)])
def audit_lead(lead_id: int):
    guard_mutation()
    lead = store.lead(lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    audit = audit_website(lead["source_url"])
    store.set_audit(lead_id, audit)
    return audit


@app.post("/api/leads/{lead_id}/proposal", dependencies=[Depends(require_federation_admin)])
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


@app.post("/api/jobs/run", dependencies=[Depends(require_federation_admin)])
def jobs_run():
    guard_mutation()
    return run_pending(store)


@app.get("/api/dashboard/summary", dependencies=[Depends(require_federation_admin)])
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


# Identity-minimal federation registry. The same owner-admin gate protects
# business records, world controls, provisioning and other private operations.
from .federation import FederationRegistry

federation = FederationRegistry(settings.db_path)


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
        # Every new identity starts INITIALIZING and must explicitly wake.
        agent_lifecycle.register(result["machine_id"])
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


class OwnerAgentIn(BaseModel):
    machine_id: str = Field(min_length=8, max_length=80)


class OwnerAgentProvisionIn(BaseModel):
    division_slug: str = Field(min_length=3, max_length=40)
    role: str = Field(min_length=1, max_length=30)


class OwnerLifecycleTransitionIn(BaseModel):
    target: str = Field(min_length=3, max_length=20)
    goal: str = Field(default="", max_length=200)
    reason: str = Field(default="", max_length=300)


class OwnerTaskCompleteIn(BaseModel):
    machine_id: str = Field(min_length=8, max_length=80)
    lease_token: str = Field(min_length=20, max_length=200)
    result: dict = Field(default_factory=dict)


@app.post("/api/owner/agents/provision",
          dependencies=[Depends(require_federation_admin)])
def owner_provision_agent(payload: OwnerAgentProvisionIn):
    guard_mutation()
    try:
        result = federation.create_agent(payload.division_slug, payload.role)
        agent_lifecycle.register(result["machine_id"])
        # The machine token is intentionally discarded: this browser worker
        # uses the owner session, not a long-lived token in headset storage.
        store.log("federation_admin", "owner_agent_provisioned",
                  result["machine_id"] + ":" + payload.role)
        return {"machine_id": result["machine_id"], "division": payload.division_slug,
                "role": payload.role, "status": "INITIALIZING",
                "credential_returned": False}
    except (ValueError, LookupError) as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/owner/agents",
         dependencies=[Depends(require_federation_admin)])
def owner_list_agents():
    result = federation.status()
    for agent in result["agents"]:
        agent_lifecycle.register(agent["machine_id"])
        agent["lifecycle"] = agent_lifecycle.get(agent["machine_id"])
    return result


@app.post("/api/owner/agents/{machine_id}/transition",
          dependencies=[Depends(require_federation_admin)])
def owner_transition_agent(machine_id: str, payload: OwnerLifecycleTransitionIn):
    record = federation.conn.execute(
        "SELECT machine_id FROM machine_agents WHERE machine_id=? AND status='PROVISIONED'",
        (machine_id,),
    ).fetchone()
    if not record:
        raise HTTPException(404, "provisioned agent not found")
    agent_lifecycle.register(machine_id)
    try:
        result = agent_lifecycle.transition(
            machine_id, payload.target.upper(), payload.goal, payload.reason)
        store.log("federation_admin", "owner_agent_transition", machine_id + ":" + result["mode"])
        return result
    except (ValueError, LookupError) as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/runtime/owner/claim",
          dependencies=[Depends(require_federation_admin)])
def owner_runtime_claim(payload: OwnerAgentIn):
    row = federation.conn.execute(
        "SELECT machine_id,division_slug,role,status FROM machine_agents "
        "WHERE machine_id=? AND status='PROVISIONED'", (payload.machine_id,)
    ).fetchone()
    if not row:
        raise HTTPException(404, "provisioned agent not found")
    task = agent_runtime.claim(dict(row))
    return task or {"outcome": "no_matching_task"}


@app.post("/api/runtime/owner/tasks/{task_id}/complete",
          dependencies=[Depends(require_federation_admin)])
def owner_runtime_complete(task_id: int, payload: OwnerTaskCompleteIn):
    row = federation.conn.execute(
        "SELECT machine_id,division_slug,role,status FROM machine_agents "
        "WHERE machine_id=? AND status='PROVISIONED'", (payload.machine_id,)
    ).fetchone()
    if not row:
        raise HTTPException(404, "provisioned agent not found")
    try:
        completed = agent_runtime.complete(dict(row), task_id, payload.lease_token, payload.result)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not completed:
        raise HTTPException(409, "task lease invalid, expired, or outside agent division")
    return {"outcome": "completed"}


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


# Persistent VR world registry. World profiles mirror provisioned machine agents;
# presence is LIVE only after a signed-in machine agent sends a recent heartbeat.
from .agent_world import AgentWorld
agent_world = AgentWorld(settings.db_path)


class WorldHeartbeatIn(BaseModel):
    zone: str = Field(default="", max_length=40)
    activity: str = Field(default="", max_length=80)


class WorldLearningIn(BaseModel):
    event_key: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9._:-]+$")
    change_type: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=500)
    config: dict = Field(default_factory=dict)


@app.get("/api/world/snapshot",
         dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def world_snapshot():
    agent_world.sync_registry(federation)
    result = agent_world.snapshot()
    result["adaptations"] = agent_world.adaptations(200)
    return result


@app.get("/api/world/events",
         dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def world_events(limit: int = 50):
    return agent_world.recent_events(limit)


@app.post("/api/world/heartbeat")
def world_heartbeat(payload: WorldHeartbeatIn,
                    agent: dict = __import__("fastapi").Depends(require_agent)):
    agent_world.sync_registry(federation)
    try:
        result = agent_world.heartbeat(agent["machine_id"], payload.zone, payload.activity)
        store.log(agent["machine_id"], "world_heartbeat", result["zone"] + ":" + result["activity"])
        return result
    except (ValueError, LookupError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/world/adaptations",
         dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def world_adaptations(limit: int = 200, zone: str = ""):
    if zone and not __import__("re").fullmatch(r"[a-z0-9][a-z0-9-]{1,38}[a-z0-9]", zone):
        raise HTTPException(422, "invalid world zone")
    return {"items": agent_world.adaptations(limit, zone)}


@app.post("/api/world/learn")
def world_learn(payload: WorldLearningIn,
                agent: dict = __import__("fastapi").Depends(require_agent)):
    """Record an authenticated bot learning event as a local-area world adaptation."""
    guard_mutation()
    agent_world.sync_registry(federation)
    try:
        result = agent_world.record_learning(
            agent["machine_id"], payload.event_key, payload.change_type,
            payload.title, payload.summary, payload.config)
        store.log(agent["machine_id"], "world_learning", result["adaptation"]["zone"] + ":" + payload.change_type)
        return result
    except (ValueError, LookupError) as exc:
        raise HTTPException(422, str(exc)) from exc



# Persistent agent lifecycle: initialize, work, sleep, dream, wake.
from .agent_lifecycle import AgentLifecycle
agent_lifecycle = AgentLifecycle(settings.db_path)


class LifecycleTransitionIn(BaseModel):
    target: str = Field(min_length=3, max_length=20)
    goal: str = Field(default="", max_length=200)
    reason: str = Field(default="", max_length=300)


class DreamArtifactIn(BaseModel):
    artifact_type: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=1000)
    artifact: dict = Field(default_factory=dict)


class DreamArtifactReviewIn(BaseModel):
    decision: str = Field(pattern=r"^(APPROVED|REJECTED)$")


@app.get("/api/lifecycle/status",
         dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def lifecycle_status():
    agent_world.sync_registry(federation)
    for item in agent_world.snapshot()["agents"]:
        agent_lifecycle.register(item["machine_id"])
    return agent_lifecycle.snapshot()


@app.get("/api/lifecycle/me")
def lifecycle_me(agent: dict = __import__("fastapi").Depends(require_agent)):
    agent_lifecycle.register(agent["machine_id"])
    return agent_lifecycle.get(agent["machine_id"])


@app.post("/api/lifecycle/transition")
def lifecycle_transition(payload: LifecycleTransitionIn,
                         agent: dict = __import__("fastapi").Depends(require_agent)):
    guard_mutation()
    agent_lifecycle.register(agent["machine_id"])
    try:
        result = agent_lifecycle.transition(
            agent["machine_id"], payload.target.upper(), payload.goal, payload.reason)
        store.log(agent["machine_id"], "lifecycle_transition", result["mode"])
        return result
    except (ValueError, LookupError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/lifecycle/dream-artifacts")
def lifecycle_dream_artifact(payload: DreamArtifactIn,
                              agent: dict = __import__("fastapi").Depends(require_agent)):
    guard_mutation()
    agent_lifecycle.register(agent["machine_id"])
    try:
        result = agent_lifecycle.add_dream_artifact(
            agent["machine_id"], agent["division_slug"], payload.artifact_type,
            payload.title, payload.summary, payload.artifact)
        store.log(agent["machine_id"], "dream_artifact_submitted", str(result["id"]))
        return result
    except (ValueError, LookupError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/lifecycle/dream-artifacts",
         dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def lifecycle_dream_artifacts(status: str = "AWAITING_REVIEW", limit: int = 100):
    if status not in {"AWAITING_REVIEW", "APPROVED", "REJECTED"}:
        raise HTTPException(422, "invalid artifact review status")
    return {"items": agent_lifecycle.artifacts(status, limit)}

@app.post("/api/lifecycle/dream-artifacts/{artifact_id}/review",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def lifecycle_review_dream_artifact(artifact_id: int, payload: DreamArtifactReviewIn):
    guard_mutation()
    try:
        result = agent_lifecycle.review_artifact(artifact_id, payload.decision)
        store.log("federation_admin", "dream_artifact_review",
                  str(artifact_id) + ":" + payload.decision)
        return result
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc



# Platform expansion: capability tracking and opt-in community compute.
# Enrollment is public but creates PENDING_REVIEW records only. No remote code
# execution is exposed by this API. Approval issues a scoped node credential.
from .platform_registry import PlatformRegistry
platform_registry = PlatformRegistry(settings.db_path)


class ContributorEnrollIn(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    consent_version: str = Field(min_length=3, max_length=40)
    terms_accepted: bool
    resources: dict = Field(default_factory=dict)


class ContributorHeartbeatIn(BaseModel):
    cpu_percent: float = Field(default=0, ge=0, le=100)
    ram_used_mb: int = Field(default=0, ge=0, le=1048576)
    paused: bool = False


@app.get("/api/platform/capabilities")
def platform_capabilities():
    return {"items": platform_registry.capabilities(),
            "note": "Statuses reflect tracked implementation, not deployment."}


@app.get("/api/platform/compute/status")
def compute_status():
    return platform_registry.summary()


@app.post("/api/platform/compute/enroll")
def compute_enroll(payload: ContributorEnrollIn):
    guard_mutation()
    if not payload.terms_accepted:
        raise HTTPException(400, "explicit contributor consent is required")
    if payload.consent_version != "ghostcorp-compute-v1":
        raise HTTPException(400, "please review the current contributor terms")
    try:
        result = platform_registry.enroll(payload.display_name, payload.consent_version,
                                          payload.resources)
        store.log("contributor", "compute_enrollment_pending", result["node_id"])
        return result
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, "invalid resource declaration") from exc


@app.post("/api/platform/compute/{node_id}/approve",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def compute_approve(node_id: str):
    try:
        result = platform_registry.approve(node_id)
        store.log("federation_admin", "compute_contributor_approved", node_id)
        return result
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/platform/compute/{node_id}/revoke",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def compute_revoke(node_id: str):
    try:
        result = platform_registry.revoke(node_id)
        store.log("federation_admin", "compute_contributor_revoked", node_id)
        return result
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/platform/compute/nodes",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def compute_nodes():
    return {"items": platform_registry.list_nodes()}


def require_compute_node(authorization: str = Header(default="")):
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "compute node bearer token required")
    node = platform_registry.authenticate(token)
    if not node:
        raise HTTPException(403, "invalid, revoked or inactive compute node")
    return node


@app.post("/api/platform/compute/heartbeat")
def compute_heartbeat(payload: ContributorHeartbeatIn,
                      node: dict = __import__("fastapi").Depends(require_compute_node)):
    try:
        return platform_registry.heartbeat(node["node_id"], payload.model_dump())
    except LookupError as exc:
        raise HTTPException(403, str(exc)) from exc


@app.get("/api/platform/compute/capacity")
def compute_capacity():
    return platform_registry.capacity_snapshot()


# Fixed-workload sandbox adapter. Disabled by default and owner-admin gated.
from .sandbox import DockerSandbox, SandboxUnavailable
sandbox_runner = DockerSandbox()


@app.get("/api/sandbox/status")
def sandbox_status():
    return sandbox_runner.status()


@app.post("/api/sandbox/run-public-tests",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def sandbox_run_public_tests():
    guard_mutation()
    try:
        return sandbox_runner.run_public_tests()
    except SandboxUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


# Workload governance: signed fixed-profile manifests and durable per-agent quotas.
# These controls authorize/account for work only; they do not dispatch or execute it.
from .workload_governance import WorkloadAuthority, WorkloadPolicyError, QuotaLedger

workload_authority = WorkloadAuthority(os.environ.get("GHOSTCORP_WORKLOAD_SIGNING_KEY", ""))
workload_quotas = QuotaLedger(settings.db_path)


class WorkloadManifestIn(BaseModel):
    workload_type: str = Field(min_length=3, max_length=60)
    agent_id: str = Field(min_length=3, max_length=80)
    source_revision: str = Field(min_length=40, max_length=40)
    ttl_seconds: int = Field(default=900, ge=60, le=3600)


class QuotaReserveIn(BaseModel):
    agent_id: str = Field(min_length=3, max_length=80)
    task_key: str = Field(min_length=3, max_length=120)
    seconds: int = Field(ge=1, le=600)


class QuotaSettleIn(BaseModel):
    reservation_id: str = Field(min_length=8, max_length=100)
    actual_seconds: int = Field(ge=0, le=600)


@app.get("/api/workloads/catalog")
def workload_catalog():
    from .workload_governance import PROFILES
    return {"workloads": PROFILES,
            "execution_enabled": False,
            "note": "Profiles are authorization templates only; no remote workload runner is enabled."}


@app.post("/api/workloads/manifest",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def workload_manifest_issue(payload: WorkloadManifestIn):
    guard_mutation()
    try:
        manifest = workload_authority.issue(
            payload.workload_type, payload.agent_id, payload.source_revision,
            payload.ttl_seconds)
        store.log("federation_admin", "workload_manifest_issued", manifest["workload_id"])
        return manifest
    except WorkloadPolicyError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/workloads/quotas/reserve",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def workload_quota_reserve(payload: QuotaReserveIn):
    guard_mutation()
    try:
        result = workload_quotas.reserve(payload.agent_id, payload.task_key, payload.seconds)
        store.log("federation_admin", "workload_quota_reserved",
                  result.get("reservation_id", payload.task_key))
        return result
    except WorkloadPolicyError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/workloads/quotas/settle",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def workload_quota_settle(payload: QuotaSettleIn):
    guard_mutation()
    try:
        result = workload_quotas.settle(payload.reservation_id, payload.actual_seconds)
        store.log("federation_admin", "workload_quota_settled", payload.reservation_id)
        return result
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except WorkloadPolicyError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/workloads/quotas/{agent_id}",
         dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def workload_quota_status(agent_id: str):
    if not __import__("re").fullmatch(r"[A-Za-z0-9_-]{3,80}", agent_id):
        raise HTTPException(422, "invalid agent identity")
    return workload_quotas.status(agent_id)


# Agent-specific temporary workspace allocation. This creates empty directories
# only; it is not an execution or host-isolation boundary.
from .agent_workspaces import AgentWorkspaceManager, WorkspacePolicyError
workspace_manager = AgentWorkspaceManager(
    settings.db_path, os.environ.get("GHOSTCORP_WORKSPACE_ROOT") or None)


class WorkspaceCreateIn(BaseModel):
    agent_id: str = Field(min_length=3, max_length=80)
    ttl_seconds: int = Field(default=3600, ge=60, le=86400)


@app.get("/api/workspaces/status")
def workspace_status():
    return workspace_manager.status()


@app.get("/api/workspaces",
         dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def workspace_list(agent_id: str = ""):
    try:
        return {"items": workspace_manager.list(agent_id or None)}
    except WorkspacePolicyError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/workspaces",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def workspace_create(payload: WorkspaceCreateIn):
    guard_mutation()
    try:
        return workspace_manager.create(payload.agent_id, payload.ttl_seconds)
    except WorkspacePolicyError as exc:
        raise HTTPException(503 if "not configured" in str(exc) else 422, str(exc)) from exc


@app.post("/api/workspaces/{workspace_id}/release",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def workspace_release(workspace_id: str):
    guard_mutation()
    try:
        return workspace_manager.release(workspace_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except WorkspacePolicyError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/workspaces/cleanup-expired",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def workspace_cleanup_expired():
    guard_mutation()
    return {"items": workspace_manager.cleanup_expired()}


# Artifact quarantine: bounded, non-executing intake from an active agent workspace.
# Files remain private and pending review; no archive extraction or malware-free claim.
from .artifact_quarantine import (
    ArtifactPolicyError, ArtifactQuarantine, ArtifactQuarantineUnavailable,
)

artifact_quarantine = ArtifactQuarantine(
    settings.db_path,
    os.environ.get("GHOSTCORP_WORKSPACE_ROOT") or None,
    os.environ.get("GHOSTCORP_ARTIFACT_QUARANTINE_ROOT") or None,
)


class ArtifactQuarantineIn(BaseModel):
    workspace_id: str = Field(min_length=35, max_length=35, pattern=r"^ws_[a-f0-9]{32}$")
    artifact_name: str = Field(min_length=1, max_length=180)


@app.get("/api/artifacts/status")
def artifact_quarantine_status():
    state = artifact_quarantine.status()
    state["owner_admin_gate_configured"] = bool(FEDERATION_ADMIN_TOKEN)
    state["enabled"] = state["enabled"] and bool(FEDERATION_ADMIN_TOKEN)
    return state


@app.post("/api/artifacts/quarantine",
          dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def artifact_quarantine_ingest(payload: ArtifactQuarantineIn):
    guard_mutation()
    try:
        result = artifact_quarantine.quarantine(payload.workspace_id, payload.artifact_name)
        store.log("federation_admin", "artifact_quarantined", result["artifact_id"])
        return result
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ArtifactQuarantineUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except ArtifactPolicyError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/artifacts/quarantine",
         dependencies=[__import__("fastapi").Depends(require_federation_admin)])
def artifact_quarantine_list(limit: int = 100):
    return {"items": artifact_quarantine.list(limit)}


@app.get("/api/owner/action-center",
         dependencies=[Depends(require_federation_admin)])
def owner_action_center():
    """One private, evidence-oriented view of items requiring owner attention."""
    agent_world.sync_registry(federation)
    return {
        "mode": "OWNER_PRIVATE_ACTION_CENTER",
        "health": {"paused": settings.paused, "spend_cap_usd": governor.cap_usd,
                   "spent_usd": governor.spent_usd,
                   "payments_mode": settings.payments_mode},
        "queue": agent_runtime.status(),
        "lifecycle": agent_lifecycle.snapshot(),
        "world": agent_world.snapshot(),
        "agents": owner_list_agents(),
        "customer_problems": {"new": customer_feedback.list("NEW", 50),
                              "roadmap": customer_feedback.list("ROADMAP", 50)},
        "product_drafts": {"items": product_pipeline.list("ALL", 100)},
        "dream_artifacts": {"items": agent_lifecycle.artifacts("AWAITING_REVIEW", 100)},
        "artifacts": artifact_quarantine.list(100),
        "capability_status": {
            "owner_email_sign_in": owner_auth.configured(),
            "live_workers": False,
            "local_model_backend": "DISABLED_UNLESS_CONFIGURED",
            "gumroad_live_verification": False,
            "production_deployment": False,
        },
    }
