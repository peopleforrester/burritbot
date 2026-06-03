# ABOUTME: Phase B8 test — deploy/<x>/kustomization.yaml stubs are wired, TODOs resolved.
# ABOUTME: Asserts the post-A1 stubs now reference real B-series resources where applicable.

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


DEPLOY = PROJECT_ROOT / "deploy"


def _load_kustomization(path: Path) -> dict:
    with path.open() as fp:
        for doc in yaml.safe_load_all(fp):
            if doc and doc.get("kind") == "Kustomization":
                return doc
    raise AssertionError(f"no Kustomization in {path}")


@pytest.mark.static
def test_deploy_monitoring_includes_grafana_external_secret() -> None:
    """B2 added a Grafana admin ExternalSecret; deploy/monitoring should wire it."""
    k = _load_kustomization(DEPLOY / "monitoring" / "kustomization.yaml")
    resources = k.get("resources", []) or []
    has_grafana = any("grafana-admin-external-secret" in r for r in resources)
    assert has_grafana, (
        "deploy/monitoring must include "
        "../../security/eso/grafana-admin-external-secret.yaml"
    )


@pytest.mark.static
def test_deploy_security_includes_cluster_secret_store() -> None:
    """B2 added a gcpsm ClusterSecretStore; deploy/security should wire it."""
    k = _load_kustomization(DEPLOY / "security" / "kustomization.yaml")
    resources = k.get("resources", []) or []
    has_css = any("cluster-secret-store" in r for r in resources)
    assert has_css, (
        "deploy/security must include "
        "../../security/eso/cluster-secret-store.yaml"
    )


@pytest.mark.static
def test_b8_kustomizations_drop_resolved_todos() -> None:
    """B8 must remove the critical-fixes-plan TODO comments that B5/B7 resolved."""
    for component in ("monitoring", "security", "ai-gateway"):
        path = DEPLOY / component / "kustomization.yaml"
        text = path.read_text()
        # The specific TODOs that B5 (falco wrap), B7 (kyverno install), and
        # this phase (B8) now address must be gone. A NeMo/LLM Guard TODO
        # tracked to Phase C is allowed if explicitly scoped to phase-c.
        critical_fix_todos = re.findall(
            r"TODO\(critical-fixes-plan\)", text
        )
        assert not critical_fix_todos, (
            f"{path.name} still has TODO(critical-fixes-plan) comments; "
            f"either resolve or re-scope to TODO(phase-c) if genuinely "
            f"deferred to NeMo/LLM Guard work"
        )


@pytest.mark.static
def test_no_deploy_kustomization_is_empty_resources() -> None:
    """Every deploy/<x>/kustomization.yaml must reference at least one resource."""
    for kust_path in DEPLOY.rglob("kustomization.yaml"):
        k = _load_kustomization(kust_path)
        resources = k.get("resources", []) or []
        assert resources, (
            f"{kust_path.relative_to(PROJECT_ROOT)} has an empty resources "
            f"list — either populate it or document why it's intentionally "
            f"empty (and re-evaluate whether the wrapper Application should "
            f"exist at all)"
        )
