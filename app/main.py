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
