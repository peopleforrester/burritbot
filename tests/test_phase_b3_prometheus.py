# ABOUTME: Phase B3 test — kube-prometheus-stack Application adapted from EKS to GKE.
# ABOUTME: Asserts ALB ingress removed, idp-* alerts renamed to burritbot-*, datasources kept.

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


GITOPS_APPS = PROJECT_ROOT / "gitops" / "apps"
PROMETHEUS_APP = GITOPS_APPS / "prometheus.yaml"

AWS_PATTERNS = [
    re.compile(r"eks\.amazonaws\.com"),
    re.compile(r"\.dkr\.ecr\."),
    re.compile(r"alb\.ingress\.kubernetes\.io"),
    re.compile(r"arn:aws:"),
    re.compile(r"\baws_iam_role\b"),
    re.compile(r"\bingressClassName:\s*alb\b"),
    re.compile(r"ai-enhanced-devops\.com"),  # EKS-era demo hostname
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


def _values(doc: dict) -> dict:
    return doc["spec"]["source"].get("helm", {}).get("valuesObject", {})


@pytest.mark.static
def test_prometheus_application_exists() -> None:
    assert PROMETHEUS_APP.is_file(), f"missing {PROMETHEUS_APP}"
    doc = _all_docs(PROMETHEUS_APP)[0]
    assert doc["kind"] == "Application"
    assert doc["metadata"]["name"] == "prometheus"
    assert doc["spec"]["destination"]["namespace"] == "monitoring"


@pytest.mark.static
def test_prometheus_chart_pinned() -> None:
    doc = _all_docs(PROMETHEUS_APP)[0]
    src = doc["spec"]["source"]
    assert src["chart"] == "kube-prometheus-stack"
    assert src["repoURL"] == "https://prometheus-community.github.io/helm-charts"
    assert src.get("targetRevision"), "chart targetRevision must be pinned"


@pytest.mark.static
def test_no_aws_strings_in_prometheus_app() -> None:
    _assert_no_aws_strings(PROMETHEUS_APP)


@pytest.mark.static
def test_grafana_ingress_block_removed_or_gke_native() -> None:
    """The EKS reference had a full ALB ingress block — must be gone or GKE-native."""
    values = _values(_all_docs(PROMETHEUS_APP)[0])
    ingress = values.get("grafana", {}).get("ingress", {})
    if ingress and ingress.get("enabled"):
        ingress_class = ingress.get("ingressClassName", "")
        assert ingress_class != "alb", "ALB ingress class must not be used on GKE"
        annotations = ingress.get("annotations", {}) or {}
        for k in annotations:
            assert not k.startswith("alb.ingress.kubernetes.io/"), (
                f"AWS ALB ingress annotation {k!r} must be removed"
            )


@pytest.mark.static
def test_alerts_renamed_from_idp_to_burritbot() -> None:
    """The EKS reference had idp-node-alerts / idp-app-alerts — rename to burritbot-*."""
    values = _values(_all_docs(PROMETHEUS_APP)[0])
    rules_map = values.get("additionalPrometheusRulesMap", {}) or {}
    if not rules_map:
        return  # additionalPrometheusRulesMap is optional, skip if absent
    burritbot_rules_key = next(
        (k for k in rules_map if "burritbot" in k.lower()), None
    )
    assert burritbot_rules_key is not None, (
        f"additionalPrometheusRulesMap must contain a burritbot key; "
        f"got {list(rules_map.keys())}"
    )
    groups = rules_map[burritbot_rules_key].get("groups", [])
    group_names = [g["name"] for g in groups]
    for name in group_names:
        assert not name.startswith("idp-"), (
            f"alert group {name!r} must be renamed from idp-* to burritbot-*"
        )


@pytest.mark.static
def test_tempo_and_loki_datasources_retained() -> None:
    """Tempo + Loki datasources are demo-critical (traces + logs panels)."""
    values = _values(_all_docs(PROMETHEUS_APP)[0])
    extra_ds = values.get("grafana", {}).get("additionalDataSources", []) or []
    ds_names = [d.get("name") for d in extra_ds]
    assert "Tempo" in ds_names, "Tempo datasource must be retained for trace panels"
    assert "Loki" in ds_names, "Loki datasource must be retained for log panels"
