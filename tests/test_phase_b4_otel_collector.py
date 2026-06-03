# ABOUTME: Phase B4 test — OTel Collector Application EXTENDed with GenAI semconv processors.
# ABOUTME: Asserts cluster.name is burritbot, GenAI gen_ai.* attribute mapper is present.

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


GITOPS_APPS = PROJECT_ROOT / "gitops" / "apps"
OTEL_APP = GITOPS_APPS / "otel-collector.yaml"

AWS_PATTERNS = [
    re.compile(r"eks\.amazonaws\.com"),
    re.compile(r"\.dkr\.ecr\."),
    re.compile(r"alb\.ingress\.kubernetes\.io"),
    re.compile(r"arn:aws:"),
    re.compile(r"\baws_iam_role\b"),
    re.compile(r"cluster\.name.*kubeauto-ai-day"),
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
def test_otel_application_exists() -> None:
    assert OTEL_APP.is_file(), f"missing {OTEL_APP}"
    doc = _all_docs(OTEL_APP)[0]
    assert doc["kind"] == "Application"
    assert doc["metadata"]["name"] == "otel-collector"
    assert doc["spec"]["destination"]["namespace"] == "monitoring"


@pytest.mark.static
def test_otel_chart_pinned_daemonset_mode() -> None:
    doc = _all_docs(OTEL_APP)[0]
    src = doc["spec"]["source"]
    assert src["chart"] == "opentelemetry-collector"
    assert src.get("targetRevision"), "chart targetRevision must be pinned"
    values = _values(doc)
    assert values.get("mode") == "daemonset", (
        "OTel Collector should run as DaemonSet for per-node telemetry"
    )


@pytest.mark.static
def test_no_aws_strings_in_otel_app() -> None:
    _assert_no_aws_strings(OTEL_APP)


@pytest.mark.static
def test_cluster_name_is_burritbot() -> None:
    """resource processor must set cluster.name=burritbot (was kubeauto-ai-day on EKS)."""
    values = _values(_all_docs(OTEL_APP)[0])
    resource_attrs = (
        values.get("config", {})
        .get("processors", {})
        .get("resource", {})
        .get("attributes", [])
    )
    cluster_attr = next(
        (a for a in resource_attrs if a.get("key") == "cluster.name"), None
    )
    assert cluster_attr is not None, "resource processor must set cluster.name"
    assert cluster_attr.get("value") == "burritbot", (
        f"cluster.name should be 'burritbot', got {cluster_attr.get('value')!r}"
    )


@pytest.mark.static
def test_genai_semconv_processor_present() -> None:
    """The Eyes layer requires gen_ai.* attribute decoration per semconv v1.37.0."""
    values = _values(_all_docs(OTEL_APP)[0])
    processors = values.get("config", {}).get("processors", {})
    # The GenAI processor is typically named `attributes` or `attributes/genai`.
    # Look for any processor that contains an action keyed on gen_ai.*.
    found = False
    for proc_name, proc_cfg in processors.items():
        actions = (proc_cfg or {}).get("actions", []) or []
        for action in actions:
            if action.get("key", "").startswith("gen_ai."):
                found = True
                break
        if found:
            break
    assert found, (
        "OTel Collector must include a processor that decorates gen_ai.* "
        "attributes (gen_ai.provider.name, gen_ai.request.model, etc.) "
        "per OTel GenAI semconv v1.37.0 — see "
        "observability/otel-collector/config.yaml for the EXTEND template"
    )


@pytest.mark.static
def test_genai_processor_in_traces_and_metrics_pipelines() -> None:
    """The genai processor must run in BOTH pipelines, not just metrics."""
    values = _values(_all_docs(OTEL_APP)[0])
    pipelines = values.get("config", {}).get("service", {}).get("pipelines", {})

    # Find the genai-bearing processor name first.
    processors = values.get("config", {}).get("processors", {})
    genai_proc_name = None
    for proc_name, proc_cfg in processors.items():
        actions = (proc_cfg or {}).get("actions", []) or []
        if any(a.get("key", "").startswith("gen_ai.") for a in actions):
            genai_proc_name = proc_name
            break
    assert genai_proc_name, "no genai-bearing processor found"

    for kind in ("traces", "metrics"):
        if kind in pipelines:
            assert genai_proc_name in pipelines[kind].get("processors", []), (
                f"{genai_proc_name!r} must be in the {kind} pipeline"
            )
