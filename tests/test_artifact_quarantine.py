import os
import stat

import pytest

from app.agent_workspaces import AgentWorkspaceManager
from app.artifact_quarantine import (
    ArtifactPolicyError,
    ArtifactQuarantine,
    ArtifactQuarantineUnavailable,
)


def setup_quarantine(tmp_path, clock=None, max_bytes=1_048_576):
    db = str(tmp_path / "ghostcorp.db")
    workspace_root = tmp_path / "workspaces"
    manager = AgentWorkspaceManager(db, str(workspace_root), clock=clock)
    workspace = manager.create("agent_123", 600)
    quarantine_root = tmp_path / "quarantine"
    quarantine_root.mkdir(mode=0o700)
    quarantine = ArtifactQuarantine(
        db, str(workspace_root), str(quarantine_root),
        clock=clock, max_bytes=max_bytes,
    )
    return manager, workspace, quarantine, workspace_root, quarantine_root


def test_text_artifact_is_hashed_copied_and_kept_quarantined(tmp_path):
    _, workspace, quarantine, workspace_root, quarantine_root = setup_quarantine(tmp_path)
    artifact = workspace_root / workspace["workspace_id"] / "reports" / "build.json"
    artifact.parent.mkdir(mode=0o700)
    artifact.write_text('{"tests": 12, "result": "draft"}', encoding="utf-8")

    result = quarantine.quarantine(workspace["workspace_id"], "reports/build.json")

    assert result["detected_type"] == "JSON_TEXT"
    assert result["status"] == "QUARANTINED"
    assert result["review_required"] is True
    assert result["automatic_release"] is False
    assert "malware_scanner_not_configured" in result["risk_flags"]
    stored = list(quarantine_root.glob("*.bin"))
    assert len(stored) == 1
    assert stored[0].read_bytes() == artifact.read_bytes()
    assert stat.S_IMODE(stored[0].stat().st_mode) == 0o600
    listed = quarantine.list()
    assert listed[0]["sha256"] == result["sha256"]
    assert "stored_name" not in listed[0]
    assert quarantine.status()["malware_scanner"] == "NOT_CONFIGURED"


def test_archive_and_executable_content_are_flagged_without_extraction(tmp_path):
    _, workspace, quarantine, root, _ = setup_quarantine(tmp_path)
    folder = root / workspace["workspace_id"]
    (folder / "bundle.zip").write_bytes(b"PK\\x03\\x04fake archive")
    (folder / "program.bin").write_bytes(b"\\x7fELF" + b"not-a-real-program")

    archive = quarantine.quarantine(workspace["workspace_id"], "bundle.zip")
    executable = quarantine.quarantine(workspace["workspace_id"], "program.bin")

    assert archive["detected_type"] == "ARCHIVE"
    assert "archive_not_extracted" in archive["risk_flags"]
    assert executable["detected_type"] == "EXECUTABLE_OR_SCRIPT"
    assert "executable_or_script_content" in executable["risk_flags"]
    assert len(list((root.parent / "quarantine").glob("*.bin"))) == 2


def test_symlink_artifacts_and_symlink_directories_are_rejected(tmp_path):
    _, workspace, quarantine, root, _ = setup_quarantine(tmp_path)
    folder = root / workspace["workspace_id"]
    outside = tmp_path / "outside.txt"
    outside.write_text("not inside workspace", encoding="utf-8")
    (folder / "linked.txt").symlink_to(outside)
    outside_dir = tmp_path / "outside-dir"
    outside_dir.mkdir()
    (outside_dir / "payload.txt").write_text("external", encoding="utf-8")
    (folder / "linked-dir").symlink_to(outside_dir, target_is_directory=True)

    with pytest.raises(ArtifactPolicyError):
        quarantine.quarantine(workspace["workspace_id"], "linked.txt")
    with pytest.raises(ArtifactPolicyError):
        quarantine.quarantine(workspace["workspace_id"], "linked-dir/payload.txt")


@pytest.mark.parametrize("name", [
    "../outside.txt", "/etc/passwd", ".hidden", "reports/../secret",
    "reports/./file.txt", "reports//file.txt", "reports/",
])
def test_unsafe_artifact_names_are_rejected(tmp_path, name):
    _, workspace, quarantine, _, _ = setup_quarantine(tmp_path)
    with pytest.raises(ArtifactPolicyError):
        quarantine.quarantine(workspace["workspace_id"], name)


def test_expired_workspace_cannot_supply_artifacts(tmp_path):
    clock = [1000]
    _, workspace, quarantine, root, _ = setup_quarantine(tmp_path, clock=lambda: clock[0])
    (root / workspace["workspace_id"] / "result.txt").write_text("result", encoding="utf-8")
    clock[0] = 1601
    with pytest.raises(ArtifactPolicyError):
        quarantine.quarantine(workspace["workspace_id"], "result.txt")


def test_size_limit_and_hardlinks_are_rejected(tmp_path):
    _, workspace, quarantine, root, _ = setup_quarantine(tmp_path, max_bytes=4)
    folder = root / workspace["workspace_id"]
    (folder / "large.txt").write_bytes(b"12345")
    with pytest.raises(ArtifactPolicyError):
        quarantine.quarantine(workspace["workspace_id"], "large.txt")

    outside = tmp_path / "outside-hardlink.txt"
    outside.write_text("data", encoding="utf-8")
    os.link(outside, folder / "linked-file.txt")
    with pytest.raises(ArtifactPolicyError):
        quarantine.quarantine(workspace["workspace_id"], "linked-file.txt")


def test_missing_configuration_fails_closed(tmp_path):
    quarantine = ArtifactQuarantine(str(tmp_path / "empty.db"))
    assert quarantine.status()["enabled"] is False
    with pytest.raises(ArtifactQuarantineUnavailable):
        quarantine.quarantine("ws_" + "a" * 32, "artifact.txt")


def test_quarantine_root_must_be_existing_private_directory(tmp_path):
    _, workspace, quarantine, root, quarantine_root = setup_quarantine(tmp_path)
    (root / workspace["workspace_id"] / "result.txt").write_text("result", encoding="utf-8")
    quarantine_root.chmod(0o755)
    assert quarantine.status()["enabled"] is False
    with pytest.raises(ArtifactPolicyError):
        quarantine.quarantine(workspace["workspace_id"], "result.txt")


def test_quarantine_root_symlink_is_rejected(tmp_path):
    _, workspace, quarantine, root, quarantine_root = setup_quarantine(tmp_path)
    (root / workspace["workspace_id"] / "result.txt").write_text("result", encoding="utf-8")
    real = tmp_path / "real-quarantine"
    real.mkdir(mode=0o700)
    quarantine_root.rmdir()
    quarantine_root.symlink_to(real, target_is_directory=True)
    assert quarantine.status()["enabled"] is False
    with pytest.raises(ArtifactPolicyError):
        quarantine.quarantine(workspace["workspace_id"], "result.txt")
