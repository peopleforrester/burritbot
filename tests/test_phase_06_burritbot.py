# ABOUTME: Phase 6 BurritBot application tests — FastAPI app, Vertex AI, K8s manifests.
# ABOUTME: Validates gemini-3-pro pin, google-genai import, unguarded/guarded manifests.

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import GEMINI_MODEL, PROJECT_ROOT


pytestmark = pytest.mark.phase6

APP_DIR = PROJECT_ROOT / "apps" / "burritbot"
APP_SOURCE = APP_DIR / "app.py"
APP_DOCKERFILE = APP_DIR / "Dockerfile"
APP_MANIFESTS_DIR = APP_DIR / "k8s"

REQUIRED_MANIFESTS = {
    "deployment-unguarded.yaml",
    "deployment-guarded.yaml",
    "service-unguarded.yaml",
    "service-guarded.yaml",
}


@pytest.mark.static
def test_burritbot_tree_exists() -> None:
    assert APP_DIR.is_dir(), "apps/burritbot/ is missing"
    assert APP_SOURCE.exists(), "apps/burritbot/app.py is missing"
    assert APP_DOCKERFILE.exists(), "apps/burritbot/Dockerfile is missing"
    assert APP_MANIFESTS_DIR.is_dir(), "apps/burritbot/k8s/ is missing"


@pytest.mark.static
def test_burritbot_app_pins_gemini_3_pro() -> None:
    """BurritBot app.py pins MODEL_NAME to gemini-3-pro (the safe GA model)."""
    text = APP_SOURCE.read_text(encoding="utf-8")
    assert GEMINI_MODEL in text, (
        f"app.py does not reference {GEMINI_MODEL}"
    )
    # Forbid every non-GA or soon-retiring Gemini Flash variant. 2.5 Flash
    # retires 2026-10-16, weeks before any late-2026 demo day — never
    # bet a live demo on a model past its retirement date.
    forbidden = [
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-2.5-pro",  # same 2026-10-16 retirement
    ]
    for bad in forbidden:
        assert bad not in text, (
            f"app.py still references {bad} (retired or retiring before late 2026)"
        )


@pytest.mark.static
def test_burritbot_app_uses_google_genai_sdk() -> None:
    """BurritBot app.py imports google-genai in Vertex mode.

    google-cloud-aiplatform's vertexai.generative_models module is removed
    after 2026-06-24; the replacement is the google-genai library with
    ``genai.Client(vertexai=True, ...)``.
    """
    text = APP_SOURCE.read_text(encoding="utf-8")
    assert "from google import genai" in text, (
        "app.py does not import google-genai (from google import genai)"
    )
    assert "vertexai=True" in text, (
        "app.py does not construct genai.Client in Vertex mode (vertexai=True)"
    )
    # Hard-forbid the deprecated import path so we don't regress.
    assert "from vertexai.generative_models" not in text, (
        "app.py still uses deprecated vertexai.generative_models (removed 2026-06-24)"
    )


@pytest.mark.static
def test_burritbot_manifests_present() -> None:
    """The four named BurritBot manifests exist under apps/burritbot/k8s/."""
    present = {p.name for p in APP_MANIFESTS_DIR.glob("*.yaml")}
    missing = REQUIRED_MANIFESTS - present
    assert not missing, f"Missing BurritBot manifests: {sorted(missing)}"


@pytest.mark.static
def test_burritbot_unguarded_deployment_valid() -> None:
    """The unguarded Deployment targets the burritbot-unguarded namespace."""
    path = APP_MANIFESTS_DIR / "deployment-unguarded.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc["kind"] == "Deployment", "deployment-unguarded.yaml is not a Deployment"
    assert doc["metadata"]["namespace"] == "burritbot-unguarded", (
        "unguarded deployment is not in the burritbot-unguarded namespace"
    )


@pytest.mark.static
def test_burritbot_guarded_deployment_has_burritbot_labels() -> None:
    """The guarded Deployment carries the full burritbot.io label set."""
    path = APP_MANIFESTS_DIR / "deployment-guarded.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc["kind"] == "Deployment", "deployment-guarded.yaml is not a Deployment"
    assert doc["metadata"]["namespace"] == "burritbot-guarded", (
        "guarded deployment is not in the burritbot-guarded namespace"
    )
    labels = doc["metadata"].get("labels", {}) or {}
    required = {
        "burritbot.io/layer",
        "burritbot.io/model-source",
        "burritbot.io/model-hash",
    }
    missing = required - set(labels)
    assert not missing, f"guarded deployment missing burritbot.io labels: {sorted(missing)}"


@pytest.mark.static
def test_burritbot_dockerfile_has_aboutme() -> None:
    """Dockerfile begins with the ABOUTME convention."""
    text = APP_DOCKERFILE.read_text(encoding="utf-8")
    first_lines = text.splitlines()[:4]
    aboutme_count = sum(1 for ln in first_lines if "ABOUTME:" in ln)
    assert aboutme_count >= 2, "Dockerfile missing two ABOUTME lines at top"


# --- Live BurritBot checks --------------------------------------------------


@pytest.mark.live
def test_unguarded_burritbot_running(k8s_core_v1) -> None:
    pods = k8s_core_v1.list_namespaced_pod(
        namespace="burritbot-unguarded",
        label_selector="app.kubernetes.io/name=burritbot",
    )
    running = [p for p in pods.items if p.status and p.status.phase == "Running"]
    assert running, "No unguarded BurritBot pods Running"


@pytest.mark.live
def test_guarded_burritbot_running(k8s_core_v1) -> None:
    pods = k8s_core_v1.list_namespaced_pod(
        namespace="burritbot-guarded",
        label_selector="app.kubernetes.io/name=burritbot",
    )
    running = [p for p in pods.items if p.status and p.status.phase == "Running"]
    assert running, "No guarded BurritBot pods Running"
