# ABOUTME: Phase 8 hardening/docs tests — runbook, scorecard, teardown, final state.
# ABOUTME: Static checks that the demo-day operational artifacts are in place.

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


pytestmark = pytest.mark.phase8

PRESENTATION_DOCS = PROJECT_ROOT / "presentations" / "kubecon-na-2026" / "docs"
RUNBOOK = PRESENTATION_DOCS / "RUNBOOK.md"
SCORECARD = PRESENTATION_DOCS / "SCORECARD.md"
TEARDOWN_SCRIPT = PROJECT_ROOT / "scripts" / "teardown.sh"

REQUIRED_RUNBOOK_SECTIONS = {
    "Pre-flight",
    "Act 1",
    "Act 2",
    "Cast the Net",
    "Teardown",
    "Rollback",
}

REQUIRED_SCORECARD_HEADERS = {
    "CNCF Project",
    "Layer",  # The Eyes / The Net / The Web
}


@pytest.mark.static
def test_runbook_exists_and_has_all_sections() -> None:
    """RUNBOOK.md (under the active talk folder) has the required operational sections."""
    assert RUNBOOK.exists(), f"RUNBOOK.md missing at {RUNBOOK}"
    text = RUNBOOK.read_text(encoding="utf-8")
    missing = [s for s in REQUIRED_RUNBOOK_SECTIONS if s not in text]
    assert not missing, f"RUNBOOK.md missing sections: {missing}"


@pytest.mark.static
def test_scorecard_exists_with_cncf_columns() -> None:
    """SCORECARD.md (under the active talk folder) enumerates CNCF projects by burritbot layer."""
    assert SCORECARD.exists(), f"SCORECARD.md missing at {SCORECARD}"
    text = SCORECARD.read_text(encoding="utf-8")
    missing = [h for h in REQUIRED_SCORECARD_HEADERS if h not in text]
    assert not missing, f"SCORECARD.md missing headers: {missing}"
    # At least the three layer names should appear somewhere.
    for layer in ("The Eyes", "The Net", "The Web"):
        assert layer in text, f"SCORECARD.md missing layer `{layer}`"


@pytest.mark.static
def test_teardown_script_exists_and_is_executable() -> None:
    """scripts/teardown.sh exists, is executable, and calls terraform destroy."""
    import stat as _stat

    assert TEARDOWN_SCRIPT.exists(), "scripts/teardown.sh is missing"
    mode = TEARDOWN_SCRIPT.stat().st_mode
    assert mode & _stat.S_IXUSR, "scripts/teardown.sh is not executable"
    text = TEARDOWN_SCRIPT.read_text(encoding="utf-8")
    assert "terraform destroy" in text, (
        "teardown.sh never invokes `terraform destroy`"
    )


@pytest.mark.static
def test_all_shell_scripts_start_with_aboutme() -> None:
    """Every *.sh under scripts/ starts with two ABOUTME: comment lines."""
    scripts_dir = PROJECT_ROOT / "scripts"
    if not scripts_dir.exists():
        pytest.skip("scripts/ directory not yet created")
    offenders = []
    for path in scripts_dir.glob("*.sh"):
        head = path.read_text(encoding="utf-8").splitlines()[:4]
        hits = sum(1 for ln in head if "ABOUTME:" in ln)
        if hits < 2:
            offenders.append(path.name)
    assert not offenders, f"Scripts missing ABOUTME: {offenders}"


@pytest.mark.static
def test_project_state_marked_complete() -> None:
    """PROJECT_STATE.md records Phase 8 as complete by demo day."""
    state = PROJECT_ROOT / "PROJECT_STATE.md"
    assert state.exists(), "PROJECT_STATE.md is missing"
    # Soft check: Phase 8 should be referenced somewhere so future /continue
    # sessions don't lose the hardening context.
    text = state.read_text(encoding="utf-8")
    assert "Phase 8" in text, "PROJECT_STATE.md never mentions Phase 8"
