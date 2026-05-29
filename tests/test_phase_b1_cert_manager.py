# ABOUTME: Phase B1 test — cert-manager + cert-manager-issuers Apps adapted from EKS reference.
# ABOUTME: Asserts the GCP swap is complete: no AWS strings, GCE ingress class, wave order correct.

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


GITOPS_APPS = PROJECT_ROOT / "gitops" / "apps"
NAMESPACES_FILE = PROJECT_ROOT / "gitops" / "namespaces" / "namespaces.yaml"
CLUSTER_ISSUERS = PROJECT_ROOT / "security" / "cert-manager" / "cluster-issuers.yaml"

CERT_MANAGER_APP = GITOPS_APPS / "cert-manager.yaml"
CERT_MANAGER_ISSUERS_APP = GITOPS_APPS / "cert-manager-issuers.yaml"

AWS_PATTERNS = [
    re.compile(r"eks\.amazonaws\.com"),
    re.compile(r"\.dkr\.ecr\."),
    re.compile(r"alb\.ingress\.kubernetes\.io"),
    re.compile(r"arn:aws:"),
    re.compile(r"\baws_iam_role\b"),
    re.compile(r"\bingressClassName:\s*alb\b"),
]


def _all_docs(path: Path) -> list[dict]:
    with path.open() as fp:
        return [d for d in yaml.safe_load_all(fp) if d]


def _assert_no_aws_strings(path: Path) -> None:
    text = path.read_text()
    for pat in AWS_PATTERNS:
        match = pat.search(text)
        assert not match, (
            f"{path.name}: AWS string {pat.pattern!r} still present "
            f"(line containing: {match.group(0)!r}) — finish the GCP swap"
        )


@pytest.mark.static
def test_cert_manager_application_exists() -> None:
    assert CERT_MANAGER_APP.is_file(), f"missing {CERT_MANAGER_APP}"
    doc = _all_docs(CERT_MANAGER_APP)[0]
    assert doc["kind"] == "Application"
    assert doc["metadata"]["name"] == "cert-manager"
    assert doc["spec"]["destination"]["namespace"] == "cert-manager"


@pytest.mark.static
def test_cert_manager_issuers_application_exists() -> None:
    assert CERT_MANAGER_ISSUERS_APP.is_file(), f"missing {CERT_MANAGER_ISSUERS_APP}"
    doc = _all_docs(CERT_MANAGER_ISSUERS_APP)[0]
    assert doc["kind"] == "Application"
    assert doc["metadata"]["name"] == "cert-manager-issuers"
    # Points at this repo's security/cert-manager/, not the EKS reference path
    source = doc["spec"]["source"]
    assert source.get("path") == "security/cert-manager", (
        f"issuers App should reference this repo's security/cert-manager/, "
        f"got path={source.get('path')!r}"
    )


@pytest.mark.static
def test_sync_wave_order_correct() -> None:
    """Issuers must sync after cert-manager (CRDs and webhook need to be up)."""
    cm = _all_docs(CERT_MANAGER_APP)[0]
    issuers = _all_docs(CERT_MANAGER_ISSUERS_APP)[0]
    cm_wave = int(cm["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"])
    issuers_wave = int(
        issuers["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"]
    )
    assert cm_wave < issuers_wave, (
        f"cert-manager wave ({cm_wave}) must be < issuers wave ({issuers_wave})"
    )


@pytest.mark.static
def test_no_aws_strings_in_cert_manager_app() -> None:
    _assert_no_aws_strings(CERT_MANAGER_APP)


@pytest.mark.static
def test_no_aws_strings_in_issuers_app() -> None:
    _assert_no_aws_strings(CERT_MANAGER_ISSUERS_APP)


@pytest.mark.static
def test_cluster_issuers_manifest_exists() -> None:
    assert CLUSTER_ISSUERS.is_file(), f"missing {CLUSTER_ISSUERS}"
    docs = _all_docs(CLUSTER_ISSUERS)
    kinds = {d["kind"] for d in docs}
    assert "ClusterIssuer" in kinds, "expected at least one ClusterIssuer"
    # GCE / Gateway API only — no ALB
    _assert_no_aws_strings(CLUSTER_ISSUERS)


@pytest.mark.static
def test_cert_manager_namespace_declared() -> None:
    """The cert-manager namespace must exist in the platform namespace list."""
    docs = _all_docs(NAMESPACES_FILE)
    namespace_names = {
        d["metadata"]["name"] for d in docs if d.get("kind") == "Namespace"
    }
    assert "cert-manager" in namespace_names, (
        "cert-manager namespace must be declared in "
        "gitops/namespaces/namespaces.yaml so the chart can install"
    )
