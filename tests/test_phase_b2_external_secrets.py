# ABOUTME: Phase B2 test — external-secrets Application adapted from EKS IRSA to GKE WIF.
# ABOUTME: Asserts the cloud-swap is complete: gcpsm provider, no aws/secretsmanager refs.

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


GITOPS_APPS = PROJECT_ROOT / "gitops" / "apps"
NAMESPACES_FILE = PROJECT_ROOT / "gitops" / "namespaces" / "namespaces.yaml"
ESO_DIR = PROJECT_ROOT / "security" / "eso"

ESO_APP = GITOPS_APPS / "external-secrets.yaml"
CLUSTER_SECRET_STORE = ESO_DIR / "cluster-secret-store.yaml"

WIF_ANNOTATION_KEY = "iam.gke.io/gcp-service-account"
IRSA_ANNOTATION_KEY = "eks.amazonaws.com/role-arn"

AWS_PATTERNS = [
    re.compile(r"eks\.amazonaws\.com"),
    re.compile(r"\.dkr\.ecr\."),
    re.compile(r"arn:aws:"),
    re.compile(r"\baws_iam_role\b"),
    re.compile(r"aws/secretsmanager", re.IGNORECASE),
    re.compile(r"\bSecretsManager\b"),
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
            f"(matched: {match.group(0)!r}) — finish the GCP swap"
        )


@pytest.mark.static
def test_external_secrets_application_exists() -> None:
    assert ESO_APP.is_file(), f"missing {ESO_APP}"
    doc = _all_docs(ESO_APP)[0]
    assert doc["kind"] == "Application"
    assert doc["metadata"]["name"] == "external-secrets"


@pytest.mark.static
def test_external_secrets_targets_correct_namespace() -> None:
    doc = _all_docs(ESO_APP)[0]
    ns = doc["spec"]["destination"]["namespace"]
    assert ns == "external-secrets", (
        f"ESO Application should target the external-secrets namespace "
        f"(matches Helm chart default), got {ns!r}"
    )


@pytest.mark.static
def test_external_secrets_app_uses_wif_not_irsa() -> None:
    """The chart's serviceAccount.annotations must use WIF, not IRSA."""
    doc = _all_docs(ESO_APP)[0]
    values = (
        doc["spec"]["source"]
        .get("helm", {})
        .get("valuesObject", {})
    )
    sa = values.get("serviceAccount", {})
    annotations = sa.get("annotations", {}) or {}
    assert IRSA_ANNOTATION_KEY not in annotations, (
        f"IRSA annotation {IRSA_ANNOTATION_KEY} must be removed for GKE"
    )
    assert WIF_ANNOTATION_KEY in annotations, (
        f"WIF annotation {WIF_ANNOTATION_KEY} must be present on the ESO "
        f"controller serviceAccount"
    )


@pytest.mark.static
def test_no_aws_strings_in_eso_app() -> None:
    _assert_no_aws_strings(ESO_APP)


@pytest.mark.static
def test_cluster_secret_store_uses_gcpsm() -> None:
    assert CLUSTER_SECRET_STORE.is_file(), f"missing {CLUSTER_SECRET_STORE}"
    doc = _all_docs(CLUSTER_SECRET_STORE)[0]
    assert doc["kind"] == "ClusterSecretStore"
    provider_keys = set(doc["spec"]["provider"].keys())
    assert "gcpsm" in provider_keys, (
        f"ClusterSecretStore must use 'gcpsm' provider for GCP Secret "
        f"Manager, got providers: {provider_keys}"
    )
    assert "aws" not in provider_keys, "AWS provider must be removed"


@pytest.mark.static
def test_no_aws_strings_in_cluster_secret_store() -> None:
    _assert_no_aws_strings(CLUSTER_SECRET_STORE)


@pytest.mark.static
def test_external_secrets_namespace_declared() -> None:
    docs = _all_docs(NAMESPACES_FILE)
    namespace_names = {
        d["metadata"]["name"] for d in docs if d.get("kind") == "Namespace"
    }
    assert "external-secrets" in namespace_names, (
        "external-secrets namespace must be declared in "
        "gitops/namespaces/namespaces.yaml for the chart to install"
    )
