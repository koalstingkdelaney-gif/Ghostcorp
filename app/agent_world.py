"""Persistent, privacy-minimal simulation layer for the GhostCorp agent world.

This models where provisioned agents would work and their daily routine. It is
not a consciousness engine or an AI worker. Live presence is only reported
when an authenticated machine agent sends a heartbeat.
"""
import sqlite3
import threading
import time
from pathlib import Path

MISSION_BY_ROLE = {
    "coordinator": "Grow lawful GhostCorp net revenue by coordinating teams, validating results, and protecting owner priorities.",
    "researcher": "Discover evidence-backed customer problems, market opportunities, and free resources that can grow lawful net revenue.",
    "builder": "Turn approved opportunities into useful products, services, software, and repeatable business systems.",
    "tester": "Improve reliability, security, quality, and customer trust while preventing costly failures.",
    "analyst": "Measure net revenue, costs, conversion, retention, risk, and evidence quality; recommend profitable improvements.",
    "operator": "Keep approved GhostCorp services reliable, secure, recoverable, and within zero-cost or approved budgets.",
}

ROUTINES = {
    "coordinator": [
        (0, 6, "planning", "Review priorities and prepare the daily plan", "command-center"),
        (6, 12, "coordination", "Coordinate team queues and resolve blockers", "command-center"),
        (12, 18, "review", "Review deliverables and quality reports", "command-center"),
        (18, 24, "handoff", "Prepare handoffs and record decisions", "commons"),
    ],
    "researcher": [
        (0, 6, "reading", "Review research notes and open questions", "research-library"),
        (6, 12, "research", "Investigate assigned topics and gather evidence", "research-lab"),
        (12, 18, "synthesis", "Compare sources and prepare research briefs", "research-lab"),
        (18, 24, "knowledge", "Update shared project knowledge", "commons"),
    ],
    "builder": [
        (0, 6, "design", "Review specifications and plan implementation", "design-studio"),
        (6, 12, "building", "Implement assigned project work", "build-lab"),
        (12, 18, "testing", "Run checks and repair defects", "build-lab"),
        (18, 24, "handoff", "Document changes and prepare review", "commons"),
    ],
    "tester": [
        (0, 6, "test-planning", "Prepare test coverage and acceptance criteria", "qa-lab"),
        (6, 12, "testing", "Exercise features and record reproducible results", "qa-lab"),
        (12, 18, "security-review", "Check permissions, failure modes and regressions", "security-center"),
        (18, 24, "reporting", "Publish test findings for review", "commons"),
    ],
    "analyst": [
        (0, 6, "data-review", "Review data quality and measurement definitions", "analytics"),
        (6, 12, "analysis", "Analyze assigned business and product metrics", "analytics"),
        (12, 18, "forecasting", "Prepare scenarios and evidence-backed recommendations", "strategy-room"),
        (18, 24, "reporting", "Record assumptions and publish analysis", "commons"),
    ],
    "operator": [
        (0, 6, "monitoring", "Review service health and queued incidents", "operations"),
        (6, 12, "operations", "Process authorized operational tasks", "operations"),
        (12, 18, "maintenance", "Check backups, dependencies and service status", "server-room"),
        (18, 24, "handoff", "Record operational notes and hand off open work", "commons"),
    ],
}

def _utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

class AgentWorld:
    def __init__(self, db_path):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS world_agents (
          machine_id TEXT PRIMARY KEY,
          division_slug TEXT NOT NULL,
          role TEXT NOT NULL,
          display_name TEXT NOT NULL,
          zone TEXT NOT NULL DEFAULT 'commons',
          activity TEXT NOT NULL DEFAULT 'awaiting-assignment',
          heartbeat_at INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS world_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          machine_id TEXT NOT NULL,
          event_type TEXT NOT NULL,
          summary TEXT NOT NULL,
          zone TEXT NOT NULL DEFAULT 'commons',
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_world_events_created
          ON world_events(created_at DESC);

        CREATE TABLE IF NOT EXISTS world_adaptations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_key TEXT NOT NULL UNIQUE,
          machine_id TEXT NOT NULL,
          division_slug TEXT NOT NULL,
          zone TEXT NOT NULL,
          change_type TEXT NOT NULL,
          title TEXT NOT NULL,
          summary TEXT NOT NULL,
          config TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_world_adaptations_zone
          ON world_adaptations(zone,id DESC);
        """)
        self.conn.commit()

    def sync_registry(self, registry):
        """Create world identities for every registered machine agent."""
        with self._lock:
            agents = registry.conn.execute(
                "SELECT machine_id,division_slug,role FROM machine_agents WHERE status='PROVISIONED'"
            ).fetchall()
            for agent in agents:
                machine_id, division, role = agent["machine_id"], agent["division_slug"], agent["role"]
                suffix = machine_id[-4:].upper()
                name = f"{role.title()}-{suffix}"
                zone = "command-center" if role == "coordinator" else "commons"
                self.conn.execute(
                    """INSERT OR IGNORE INTO world_agents
                       (machine_id,division_slug,role,display_name,zone,activity,created_at,updated_at)
                       VALUES(?,?,?,?,?,'awaiting-assignment',?,?)""",
                    (machine_id, division, role, name, zone, _utc(), _utc()),
                )
            self.conn.commit()
            return len(agents)

    @staticmethod
    def routine_for(role, hour=None):
        hour = time.gmtime().tm_hour if hour is None else int(hour) % 24
        blocks = ROUTINES.get(role, ROUTINES["operator"])
        for start, end, activity, description, zone in blocks:
            if start <= hour < end:
                return {"activity": activity, "description": description, "zone": zone}
        return {"activity": "rest-cycle", "description": "Between scheduled work blocks", "zone": "quarters"}

    def heartbeat(self, machine_id, zone="", activity=""):
        allowed_zones = {
            "commons", "command-center", "research-library", "research-lab",
            "design-studio", "build-lab", "qa-lab", "security-center",
            "analytics", "strategy-room", "operations", "server-room", "quarters",
        }
        if zone and zone not in allowed_zones:
            raise ValueError("unknown world zone")
        if activity and len(activity) > 80:
            raise ValueError("activity is too long")
        with self._lock:
            row = self.conn.execute(
                "SELECT role,zone,activity FROM world_agents WHERE machine_id=?",
                (machine_id,),
            ).fetchone()
            if not row:
                raise LookupError("agent has no world identity")
            next_zone = zone or row["zone"]
            next_activity = activity or row["activity"]
            now = int(time.time())
            self.conn.execute(
                "UPDATE world_agents SET zone=?,activity=?,heartbeat_at=?,updated_at=? WHERE machine_id=?",
                (next_zone, next_activity, now, _utc(), machine_id),
            )
            self.conn.execute(
                "INSERT INTO world_events(machine_id,event_type,summary,zone,created_at) VALUES(?,?,?,?,?)",
                (machine_id, "heartbeat", "Agent checked in to its world workspace", next_zone, _utc()),
            )
            self.conn.execute(
                "DELETE FROM world_events WHERE id NOT IN (SELECT id FROM world_events ORDER BY id DESC LIMIT 5000)"
            )
            self.conn.commit()
            return {"machine_id": machine_id, "zone": next_zone, "activity": next_activity,
                    "presence": "LIVE", "heartbeat_at": now}

    def snapshot(self):
        now = int(time.time())
        hour = time.gmtime(now).tm_hour
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM world_agents ORDER BY division_slug,role,machine_id"
            ).fetchall()
            agents = []
            for row in rows:
                data = dict(row)
                live = bool(data["heartbeat_at"] and now - data["heartbeat_at"] <= 180)
                routine = self.routine_for(data["role"], hour)
                agents.append({
                    "machine_id": data["machine_id"],
                    "display_name": data["display_name"],
                    "division": data["division_slug"],
                    "role": data["role"],
                    "zone": data["zone"] if live else routine["zone"],
                    "activity": data["activity"] if live else routine["activity"],
                    "activity_description": routine["description"],
                    "long_term_mission": MISSION_BY_ROLE.get(data["role"], "Advance GhostCorp approved goals safely."),
                    "presence": "LIVE" if live else "SIMULATED",
                    "heartbeat_at": data["heartbeat_at"] or None,
                })
            counts = {"total": len(agents), "live": sum(a["presence"] == "LIVE" for a in agents),
                      "simulated": sum(a["presence"] == "SIMULATED" for a in agents)}
            return {"mode": "WORLD_SIMULATION_WITH_AUTHENTICATED_PRESENCE",
                    "world_policy": {"primary_goal": "maximize lawful net value for GhostCorp", "default_paid_spend_usd": 0, "agent_work_environment": "private GhostCorp sandbox", "external_actions": "controlled gateways only", "owner_override": True},
                    "world_time_utc": _utc(), "counts": counts, "agents": agents}


    def record_learning(self, machine_id, event_key, change_type, title, summary, config=None):
        """Persist a bounded, declarative world adaptation in the agent's current zone."""
        import json
        allowed_types = {"knowledge-cluster", "workspace-layout", "ambient-state",
                         "workstation-upgrade", "display-panel"}
        if change_type not in allowed_types:
            raise ValueError("unsupported world change type")
        if not isinstance(event_key, str) or not 3 <= len(event_key) <= 120:
            raise ValueError("invalid event key")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 80:
            raise ValueError("title must be 1-80 characters")
        if not isinstance(summary, str) or not 1 <= len(summary.strip()) <= 500:
            raise ValueError("summary must be 1-500 characters")
        config = {} if config is None else config
        if not isinstance(config, dict) or len(json.dumps(config).encode("utf-8")) > 2048:
            raise ValueError("world change config must be a small JSON object")
        allowed_config = {"accent", "intensity", "scale", "position", "labels", "density"}
        if set(config) - allowed_config:
            raise ValueError("world change config contains unsupported properties")
        if "accent" in config and (not isinstance(config["accent"], str) or
                                    len(config["accent"]) > 24 or
                                    not __import__("re").fullmatch(r"#[0-9a-fA-F]{6}", config["accent"])):
            raise ValueError("accent must be a six-digit hex color")
        for key, low, high in (("intensity", 0.0, 1.0), ("scale", 0.5, 2.0), ("density", 0.1, 2.0)):
            if key in config and (not isinstance(config[key], (int, float)) or
                                  isinstance(config[key], bool) or not low <= config[key] <= high):
                raise ValueError(f"{key} is outside its allowed range")
        if "position" in config:
            pos = config["position"]
            if (not isinstance(pos, list) or len(pos) != 3 or
                any(not isinstance(v, (int, float)) or isinstance(v, bool) or abs(v) > 20 for v in pos)):
                raise ValueError("position must be three bounded numeric coordinates")
        if "labels" in config:
            labels = config["labels"]
            if (not isinstance(labels, list) or len(labels) > 8 or
                any(not isinstance(v, str) or len(v) > 32 for v in labels)):
                raise ValueError("labels must be at most eight short strings")
        with self._lock:
            agent = self.conn.execute(
                "SELECT division_slug,zone FROM world_agents WHERE machine_id=?",
                (machine_id,)
            ).fetchone()
            if not agent:
                raise LookupError("agent has no world identity")
            now = _utc()
            encoded = json.dumps(config, separators=(",", ":"), ensure_ascii=False)
            try:
                cur = self.conn.execute(
                    """INSERT INTO world_adaptations
                       (event_key,machine_id,division_slug,zone,change_type,title,summary,config,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (event_key,machine_id,agent["division_slug"],agent["zone"],
                     change_type,title.strip(),summary.strip(),encoded,now)
                )
            except sqlite3.IntegrityError:
                row = self.conn.execute(
                    "SELECT id,zone,change_type,title,created_at FROM world_adaptations WHERE event_key=?",
                    (event_key,)
                ).fetchone()
                return {"outcome":"duplicate","adaptation":dict(row)}
            self.conn.execute(
                """INSERT INTO world_events(machine_id,event_type,summary,zone,created_at)
                   VALUES(?,?,?,?,?)""",
                (machine_id,"world_adaptation",title.strip()+": "+summary.strip()[:300],
                 agent["zone"],now)
            )
            self.conn.commit()
            return {"outcome":"created","adaptation":{
                "id":cur.lastrowid,"machine_id":machine_id,"division":agent["division_slug"],
                "zone":agent["zone"],"change_type":change_type,"title":title.strip(),
                "summary":summary.strip(),"config":config,"created_at":now}}

    def adaptations(self, limit=200, zone=""):
        import json
        limit = max(1, min(int(limit), 500))
        with self._lock:
            if zone:
                rows = self.conn.execute(
                    """SELECT id,machine_id,division_slug,zone,change_type,title,summary,config,created_at
                       FROM world_adaptations WHERE zone=? ORDER BY id DESC LIMIT ?""",
                    (zone,limit)
                ).fetchall()
            else:
                rows = self.conn.execute(
                    """SELECT id,machine_id,division_slug,zone,change_type,title,summary,config,created_at
                       FROM world_adaptations ORDER BY id DESC LIMIT ?""",(limit,)
                ).fetchall()
            return [{**dict(row),"config":json.loads(row["config"])} for row in rows]

    def recent_events(self, limit=50):
        limit = max(1, min(int(limit), 200))
        with self._lock:
            rows = self.conn.execute(
                """SELECT machine_id,event_type,summary,zone,created_at
                   FROM world_events ORDER BY id DESC LIMIT ?""", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
