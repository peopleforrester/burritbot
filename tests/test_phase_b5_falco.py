# ABOUTME: Phase B5 test — Falco + Falcosidekick Applications adapted from EKS to GKE.
# ABOUTME: Asserts no AWS-tagged rules, burritbot-the-net rules included, burritbot_net_ips defined.

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


GITOPS_APPS = PROJECT_ROOT / "gitops" / "apps"
FALCO_APP = GITOPS_APPS / "falco.yaml"
FALCOSIDEKICK_APP = GITOPS_APPS / "falcosidekick.yaml"

AWS_PATTERNS = [
    re.compile(r"eks\.amazonaws\.com"),
    re.compile(r"\.dkr\.ecr\."),
    re.compile(r"arn:aws:"),
    re.compile(r"\baws_iam_role\b"),
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
def test_falco_application_exists() -> None:
    assert FALCO_APP.is_file(), f"missing {FALCO_APP}"
    doc = _all_docs(FALCO_APP)[0]
    assert doc["kind"] == "Application"
    assert doc["metadata"]["name"] == "falco"
    assert doc["spec"]["destination"]["namespace"] == "security"


@pytest.mark.static
def test_falcosidekick_application_exists() -> None:
    assert FALCOSIDEKICK_APP.is_file(), f"missing {FALCOSIDEKICK_APP}"
    doc = _all_docs(FALCOSIDEKICK_APP)[0]
    assert doc["kind"] == "Application"
    assert doc["metadata"]["name"] == "falcosidekick"
    assert doc["spec"]["destination"]["namespace"] == "security"


@pytest.mark.static
def test_falco_uses_modern_ebpf_driver() -> None:
    """modern_ebpf is required for GKE Standard (no kernel headers needed)."""
    values = _values(_all_docs(FALCO_APP)[0])
    assert values.get("driver", {}).get("kind") == "modern_ebpf"


@pytest.mark.static
def test_no_aws_strings_in_falco_apps() -> None:
    _assert_no_aws_strings(FALCO_APP)
    _assert_no_aws_strings(FALCOSIDEKICK_APP)


@pytest.mark.static
def test_falco_rules_have_no_aws_tag() -> None:
    """EKS reference tagged the IMDS rule with [aws]; GKE rewrite must drop it."""
    text = FALCO_APP.read_text()
    # tags appear as YAML list entries: `tags: [container, network, aws, ...]`
    aws_tag = re.search(r"tags:\s*\[[^\]]*\baws\b[^\]]*\]", text)
    assert aws_tag is None, (
        f"a Falco rule still carries the 'aws' tag: {aws_tag.group(0)!r} — "
        f"rewrite for GKE (gcp / gke tags)"
    )


@pytest.mark.static
def test_burritbot_the_net_rules_present_in_custom_rules() -> None:
    """Closes C19 from the senior review: rules must be wrapped into chart customRules."""
    text = FALCO_APP.read_text()
    # Look for any of the burritbot rule names in the customRules block.
    assert "Burritbot Guarded Pod Shell Spawned" in text, (
        "burritbot-the-net rules must be folded into Falco chart customRules; "
        "the standalone YAML at security/falco/rules/burritbot-the-net.yaml "
        "is not picked up by the chart"
    )


@pytest.mark.static
def test_burritbot_net_ips_list_defined() -> None:
    """Closes C19 from the senior review: the list was referenced but undefined."""
    text = FALCO_APP.read_text()
    # Must appear as a Falco list definition, not just as a reference.
    assert re.search(r"list:\s*burritbot_net_ips", text), (
        "the burritbot_net_ips list referenced by 'Burritbot Guarded Pod "
        "Outbound To Non Burritbot Net' must be defined alongside the rule"
    )


@pytest.mark.static
def test_falco_sync_wave_before_workloads() -> None:
    """Falco must be live before guarded workloads start (negative wave)."""
    doc = _all_docs(FALCO_APP)[0]
    wave = int(doc["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"])
    assert wave < 0, f"Falco wave must be negative; got {wave}"
