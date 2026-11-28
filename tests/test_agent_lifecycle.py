from app.agent_lifecycle import AgentLifecycle


def test_agent_wake_work_sleep_dream_wake_cycle(tmp_path):
    lifecycle = AgentLifecycle(str(tmp_path / "lifecycle.db"))
    lifecycle.register("agent-001")
    state = lifecycle.transition("agent-001", "WORKING", goal="Build approved product")
    assert state["mode"] == "WORKING"
    assert state["cycle"] == 1
    state = lifecycle.transition("agent-001", "SLEEPING", reason="End of work block")
    assert state["mode"] == "SLEEPING"
    state = lifecycle.transition("agent-001", "DREAMING")
    assert state["mode"] == "DREAMING"
    artifact = lifecycle.add_dream_artifact(
        "agent-001", "research-lab", "idea", "New product concept",
        "A testable idea created during a dream cycle.", {"hypothesis": "H1"})
    assert artifact["status"] == "AWAITING_REVIEW"
    state = lifecycle.transition("agent-001", "WAKING")
    assert state["mode"] == "WAKING"
    state = lifecycle.transition("agent-001", "WORKING", goal="Review dream discoveries")
    assert state["mode"] == "WORKING"
    assert state["cycle"] == 2


def test_invalid_lifecycle_transition_is_rejected(tmp_path):
    lifecycle = AgentLifecycle(str(tmp_path / "lifecycle.db"))
    lifecycle.register("agent-002")
    try:
        lifecycle.transition("agent-002", "DREAMING")
    except ValueError as exc:
        assert "invalid lifecycle transition" in str(exc)
    else:
        raise AssertionError("agent cannot jump directly into dreaming")


def test_dream_artifact_only_allowed_during_dreaming(tmp_path):
    lifecycle = AgentLifecycle(str(tmp_path / "lifecycle.db"))
    lifecycle.register("agent-003")
    try:
        lifecycle.add_dream_artifact(
            "agent-003", "build-lab", "prototype-plan", "Plan", "Summary", {})
    except ValueError as exc:
        assert "only be submitted while DREAMING" in str(exc)
    else:
        raise AssertionError("work-mode agent cannot submit dream artifacts")


def test_dream_artifact_payload_is_bounded(tmp_path):
    lifecycle = AgentLifecycle(str(tmp_path / "lifecycle.db"))
    lifecycle.register("agent-004")
    lifecycle.transition("agent-004", "WORKING")
    lifecycle.transition("agent-004", "SLEEPING")
    lifecycle.transition("agent-004", "DREAMING")
    try:
        lifecycle.add_dream_artifact(
            "agent-004", "research-lab", "idea", "Too large", "Summary",
            {"payload": "x" * 9000})
    except ValueError as exc:
        assert "under 8 KiB" in str(exc)
    else:
        raise AssertionError("oversized dream payload must be rejected")


def test_dream_artifacts_wait_for_owner_review(tmp_path):
    lifecycle = AgentLifecycle(str(tmp_path / "lifecycle.db"))
    lifecycle.register("agent-005")
    lifecycle.transition("agent-005", "WORKING")
    lifecycle.transition("agent-005", "SLEEPING")
    lifecycle.transition("agent-005", "DREAMING")
    lifecycle.add_dream_artifact(
        "agent-005", "research-lab", "skill-proposal", "Proposed skill",
        "A candidate skill for evaluation.", {})
    assert len(lifecycle.artifacts("AWAITING_REVIEW")) == 1
    assert lifecycle.artifacts("APPROVED") == []
