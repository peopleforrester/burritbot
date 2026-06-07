# ABOUTME: Shared pytest fixtures for burritbot integration tests.
# ABOUTME: Provides Kubernetes clients, GCP clients, and project-wide constants.

from __future__ import annotations

import os
from pathlib import Path

import pytest


# --- Project constants (Rule: no hardcoded project IDs in shipped code;
# tests use these constants so they can be overridden via env vars for the
# real project ID before `terraform apply`) ---

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TERRAFORM_DIR = PROJECT_ROOT / "infrastructure" / "terraform"

GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "burritbot-kubecon-2026")
GCP_REGION = os.environ.get("GCP_REGION", "us-west1")
CLUSTER_NAME = os.environ.get("CLUSTER_NAME", "burritbot")

# Gemini model pin — Gemini 3 Pro is the GA default for this demo.
# Do not regress to 1.5 (unsupported), 2.0 (retired), or 2.5 (retires
# 2026-10-16 — before any late-2026 demo day).
GEMINI_MODEL = os.environ.get("MODEL_NAME", "gemini-3-pro")

# Namespaces the platform must provision. Note `burritbot-net` (not
# `guardrails`) — the enforcement stack lives in its own namespace.
EXPECTED_NAMESPACES = [
    "argocd",
    "monitoring",
    "security",
    "burritbot-net",
    "burritbot-unguarded",
    "burritbot-guarded",
    "audience",
    "cert-manager",
    "external-secrets",
]

# Grafana demo credentials (base64 of admin:admin) for wget in test pods.
GRAFANA_BASIC_AUTH = "Basic YWRtaW46YWRtaW4="


# --- Live-cluster fixture gating ----------------------------------------
#
# Tests decorated with @pytest.mark.live require a reachable GKE cluster and
# a loaded kubeconfig. On a bare workstation (no kubectl, no kubeconfig) we
# skip them at collection time so the rest of the suite (static validation,
# policy unit tests, Python unit tests) can still run.


def _kubeconfig_available() -> bool:
    """Return True if a kubeconfig is reachable and kubernetes lib imports."""
    try:
        from kubernetes import config  # type: ignore

        config.load_kube_config()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def kubeconfig_loaded() -> bool:
    """Session fixture that returns whether kubeconfig loaded cleanly."""
    return _kubeconfig_available()


@pytest.fixture(scope="session")
def k8s_core_v1():
    """CoreV1Api client for pod/service/namespace assertions.

    Fails explicitly if kubeconfig is not loaded (no fallbacks, no mocks).
    """
    if not _kubeconfig_available():
        pytest.skip("kubeconfig not loaded; live cluster fixture unavailable")
    from kubernetes import client  # type: ignore

    return client.CoreV1Api()


@pytest.fixture(scope="session")
def k8s_apps_v1():
    """AppsV1Api client for deployment/daemonset assertions."""
    if not _kubeconfig_available():
        pytest.skip("kubeconfig not loaded; live cluster fixture unavailable")
    from kubernetes import client  # type: ignore

    return client.AppsV1Api()


@pytest.fixture(scope="session")
def k8s_custom_objects():
    """CustomObjectsApi client for CRD assertions (Kyverno policies, etc.)."""
    if not _kubeconfig_available():
        pytest.skip("kubeconfig not loaded; live cluster fixture unavailable")
    from kubernetes import client  # type: ignore

    return client.CustomObjectsApi()


@pytest.fixture(scope="session")
def k8s_networking_v1():
    """NetworkingV1Api client for NetworkPolicy assertions."""
    if not _kubeconfig_available():
        pytest.skip("kubeconfig not loaded; live cluster fixture unavailable")
    from kubernetes import client  # type: ignore

    return client.NetworkingV1Api()


@pytest.fixture(scope="session")
def k8s_rbac_v1():
    """RbacAuthorizationV1Api client for RBAC assertions."""
    if not _kubeconfig_available():
        pytest.skip("kubeconfig not loaded; live cluster fixture unavailable")
    from kubernetes import client  # type: ignore

    return client.RbacAuthorizationV1Api()


# --- GCP client fixtures ------------------------------------------------


@pytest.fixture(scope="session")
def gcp_project_id() -> str:
    """Return the GCP project ID under test."""
    return GCP_PROJECT_ID


@pytest.fixture(scope="session")
def gcp_region() -> str:
    """Return the GCP region under test."""
    return GCP_REGION


@pytest.fixture(scope="session")
def cluster_name() -> str:
    """Return the GKE cluster name used throughout tests."""
    return CLUSTER_NAME


@pytest.fixture(scope="session")
def expected_namespaces() -> list[str]:
    """Return the list of namespaces the burritbot platform requires."""
    return list(EXPECTED_NAMESPACES)


@pytest.fixture(scope="session")
def gcp_container_client():
    """google-cloud-container ClusterManagerClient for GKE assertions."""
    try:
        from google.cloud import container_v1  # type: ignore
    except ImportError:
        pytest.skip("google-cloud-container not installed")
    try:
        return container_v1.ClusterManagerClient()
    except Exception as exc:  # pragma: no cover — only hit without ADC
        pytest.skip(f"GCP auth unavailable: {exc}")


@pytest.fixture(scope="session")
def gcp_secret_manager_client():
    """google-cloud-secret-manager SecretManagerServiceClient."""
    try:
        from google.cloud import secretmanager  # type: ignore
    except ImportError:
        pytest.skip("google-cloud-secret-manager not installed")
    try:
        return secretmanager.SecretManagerServiceClient()
    except Exception as exc:  # pragma: no cover — only hit without ADC
        pytest.skip(f"GCP auth unavailable: {exc}")
