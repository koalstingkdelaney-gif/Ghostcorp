import sqlite3

import pytest

from app.federation import FederationRegistry


def test_division_and_agent_use_machine_identity_only(tmp_path):
    db = tmp_path / "federation.db"
    registry = FederationRegistry(str(db))
    registry.create_division("research-lab", "Research Lab", "Prototype and test")
    agent = registry.create_agent("research-lab", "researcher")

    assert agent["machine_id"].startswith("gca_")
    assert agent["status"] == "PROVISIONED"
    assert agent["agent_token"]
    stored = sqlite3.connect(db).execute(
        "SELECT token_hash FROM machine_agents WHERE machine_id=?",
        (agent["machine_id"],),
    ).fetchone()[0]
    assert stored != agent["agent_token"]
    assert len(stored) == 64

    status = registry.status()
    assert status["counts"] == {"divisions": 1, "agents": 1}
    assert status["personal_identity_fields"] is False
    assert "email" not in status["agents"][0]
    assert "personal_name" not in status["agents"][0]


def test_duplicate_division_slug_is_rejected(tmp_path):
    registry = FederationRegistry(str(tmp_path / "federation.db"))
    registry.create_division("product-lab", "Product Lab", "")
    with pytest.raises(ValueError, match="already exists"):
        registry.create_division("product-lab", "Second Lab", "")


def test_agent_requires_existing_division_and_allowed_role(tmp_path):
    registry = FederationRegistry(str(tmp_path / "federation.db"))
    with pytest.raises(LookupError):
        registry.create_agent("missing-lab", "researcher")
    registry.create_division("build-lab", "Build Lab", "")
    with pytest.raises(ValueError, match="unsupported"):
        registry.create_agent("build-lab", "owner")
