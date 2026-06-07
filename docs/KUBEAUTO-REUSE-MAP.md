# Kubeauto-AI-Day Reuse Map (burritbot)

This is the per-file decision matrix for pulling material from the
kubeauto-ai-day (EKS) source into the burritbot (GKE) repo. The source lives
locally at
`~/repos/_archive/events/kubeauto-ai-day/`
(canonical public copy: https://github.com/peopleforrester/kubeauto-ai-day),
and is **gitignored** here — nothing is vendored; every reuse is a fresh
read + copy during the relevant phase session.

The EKS reference was delivered as a live conference talk in 2026-03
(27/27 components, 59 live tests), so every manifest below has been
verified against a real cluster. Adaptation is the work; greenfield
authoring is not.

**Naming conventions in this repo:**
- Guardrails namespace is **`burritbot-net`** (not `guardrails`).
- AI workload labels / annotations use the **`burritbot.io/*`** prefix
  (not the prior demo's `ai.*.demo/*`).
- Guardrails sidecar containers are named **`burritbot-*`** (enforced by
  Kyverno `require-guardrails-sidecar.yaml`).
- Live toggle script is **`cast-net.sh`** (not `toggle-guardrails.sh`).
- Phases 3–5 are named **"The Eyes"**, **"The Net — Security"**, and
  **"The Net — AI Gateway"** per the burritbot metaphor.

Source repo on GitHub for cross-reference:
https://github.com/peopleforrester/kubeauto-ai-day

## Legend

- **COPY** — take as-is (path rename may apply). Rare.
- **ADAPT** — copy and replace AWS/EKS-specific bits with GCP/GKE equivalents.
- **EXTEND** — copy as a base, then layer AI-specific additions on top.
- **IGNORE** — do not reuse; rewrite or omit.

## Root / Meta

| Source path | Decision | Notes |
|---|---|---|
| `CLAUDE.md` | ADAPT | Already adapted into this repo's root `CLAUDE.md` with GKE + AI additions and the updated phase list. |
| `README.md` | IGNORE | New `README.md` written for this repo's framing. |
| `PROJECT_STATE.md` | IGNORE | New one written here; old one is for the completed EU 2026 project. |
| `REMAINING-ITEMS.md` | IGNORE | Completion checklist for the prior project. |
| `LICENSE` | COPY (when published) | Apache 2.0, same lineage. |
| `.gitignore` | ADAPT | This repo's `.gitignore` is slimmer and adds `kubeauto-ai-day/`. |
| `.gitleaks.toml` | COPY | Pre-commit secret scanning. |
| `.pre-commit-config.yaml` | ADAPT | Keep yamllint + gitleaks; drop any AWS-specific hooks. |
| `.yamllint.yml` | COPY | |
| `pyproject.toml` | ADAPT | Reuse dependency layout, swap AWS SDK for google-cloud libs and add streamlit/langchain/langchain-google-vertexai. |
| `.python-version` | COPY | |
| `CONTRIBUTING.md` | ADAPT | Same structure, new repo name. |

## `.claude/`

| Source path | Decision | Notes |
|---|---|---|
| `.claude/commands/build-phase.md` | ADAPT | Replace EKS references with GKE; keep the workflow scaffolding. |
| `.claude/commands/validate-phase.md` | COPY | Mostly generic. |
| `.claude/commands/score-component.md` | ADAPT | Scorecard is optional for NA 2026 — keep if Michael wants a scorecard pass. |
| `.claude/settings.json` | ADAPT | Tune hook paths; verify the listed hooks all apply. |
| `.claude/hooks/cc-posttool-audit.sh` | COPY | |
| `.claude/hooks/cc-pretool-guard.sh` | COPY | |
| `.claude/hooks/cc-stop-deterministic.sh` | COPY | |
| `.claude/hooks/check-image-allowlist.sh` | ADAPT | Swap allow-list to include Vertex AI / Envoy AI Gateway images. |
| `.claude/hooks/check-namespace-scope.sh` | ADAPT | Add burritbot-unguarded / burritbot-guarded / burritbot-net / audience namespaces. |
| `.claude/hooks/commit-msg-validate.sh` | COPY | |
| `.claude/hooks/pre-push-tests.sh` | ADAPT | Point at new tests/ paths. |
| `.claude/skills/argocd-patterns.md` | COPY | ArgoCD + sync waves are unchanged. |
| `.claude/skills/kyverno-policies.md` | EXTEND | Add AI policies (provenance, sidecar, OTel annotations) tagged with `burritbot.io/layer: the-net`. |
| `.claude/skills/falco-rules.md` | EXTEND | Add the AI-workload rules section with `[burritbot, the-net, ...]` tags. |
| `.claude/skills/otel-wiring.md` | EXTEND | Add GenAI semantic conventions + spinybacked-orbweaver flow ("The Eyes"). |
| `.claude/skills/eks-hardening.md` | IGNORE | EKS-specific; replace with a new `gke-patterns.md` skill. |
| `.claude/skills/backstage-templates.md` | IGNORE | No Backstage in this demo. |

## `infrastructure/`

| Source path | Decision | Notes |
|---|---|---|
| `infrastructure/terraform/main.tf` | IGNORE | Rewrite for GCP providers. |
| `infrastructure/terraform/variables.tf` | ADAPT | Keep variable-naming convention; rewrite contents for GCP (project_id, region, cluster_name). |
| `infrastructure/terraform/outputs.tf` | ADAPT | Same pattern, GKE endpoint + WIF pool outputs. |
| `infrastructure/terraform/eks.tf` | IGNORE | Replace with `gke.tf`. |
| `infrastructure/terraform/vpc.tf` | ADAPT | Replace `aws_vpc` with `google_compute_network` + `google_compute_subnetwork`. |
| `infrastructure/terraform/iam.tf` | IGNORE | Replace with Workload Identity Federation setup. |
| `infrastructure/terraform/secrets.tf` | ADAPT | Replace with `google_secret_manager_secret` resources. |

## `gitops/`

| Source path | Decision | Notes |
|---|---|---|
| `gitops/bootstrap/app-of-apps.yaml` | ADAPT | Update `repoURL` and trim the child-app list to only what this demo needs. |
| `gitops/argocd/values.yaml` | ADAPT | Replace AWS ALB ingress with GKE Gateway API; remove ACM certificate ARN; likely simpler for a demo. |
| `gitops/namespaces/namespaces.yaml` | ADAPT | Replace namespace list with: argocd, monitoring, security, burritbot-net, burritbot-unguarded, burritbot-guarded, audience. |
| `gitops/apps/kyverno.yaml` | ADAPT | Use the same Application shape; update chart version to ≥1.13 (CEL GA). |
| `gitops/apps/kyverno-policies.yaml` | ADAPT | Point at the expanded policies/ tree. |
| `gitops/apps/falco.yaml` | ADAPT | Verify chart works on GKE Standard with NAP. |
| `gitops/apps/falcosidekick.yaml` | ADAPT | Route outputs to Grafana/Prometheus rather than the old destinations. |
| `gitops/apps/external-secrets.yaml` | ADAPT | Switch from AWS SecretsManager backend to `gcpsm`. |
| `gitops/apps/cert-manager.yaml` | COPY | Same chart, same version pattern. |
| `gitops/apps/cert-manager-issuers.yaml` | ADAPT | ClusterIssuer configured for Google DNS if used. |
| `gitops/apps/prometheus.yaml` | ADAPT | Same chart; tune scrape targets for the new workloads. |
| `gitops/apps/grafana-dashboards.yaml` | ADAPT | Point at the 3 new demo dashboards. |
| `gitops/apps/otel-collector.yaml` | EXTEND | Add GenAI processors per the spec. |
| `gitops/apps/loki.yaml` | COPY | Optional; only if logs are needed on the Grafana dashboard. |
| `gitops/apps/tempo.yaml` | COPY | Useful for the trace-view dashboard. |
| `gitops/apps/promtail.yaml` | COPY | Optional; pair with Loki. |
| `gitops/apps/network-policies.yaml` | ADAPT | Reuse the wiring; rewrite the per-namespace rules (burritbot-unguarded wide open, burritbot-guarded locked to burritbot-net only). |
| `gitops/apps/rbac.yaml` | ADAPT | Reuse structure; remove EKS-specific subjects. |
| `gitops/apps/resource-quotas.yaml` | COPY | |
| `gitops/apps/backstage*.yaml` | IGNORE | No Backstage. |
| `gitops/apps/ecom-*.yaml` | IGNORE | Sample app not reused. |
| `gitops/apps/*-party.yaml` | IGNORE | Prior-demo workloads. |
| `gitops/apps/load-generator.yaml` | IGNORE | Not needed; audience frontend generates load. |
| `gitops/apps/sample-app.yaml` | IGNORE | Replaced by burritbot-unguarded and burritbot-guarded. |
| `gitops/manifests/` | IGNORE | EU 2026 demo workloads; not reused. |

## `policies/`

| Source path | Decision | Notes |
|---|---|---|
| `policies/kyverno/disallow-privileged.yaml` | COPY | |
| `policies/kyverno/require-labels.yaml` | EXTEND | Add AI-specific required labels (`app.kubernetes.io/component=inference`, `burritbot.io/layer`, `burritbot.io/model-source`, `burritbot.io/model-hash`). |
| `policies/kyverno/require-networkpolicy.yaml` | COPY | |
| `policies/kyverno/require-probes.yaml` | COPY | |
| `policies/kyverno/require-resource-limits.yaml` | COPY | |
| `policies/kyverno/restrict-image-registries.yaml` | ADAPT | Update the allow-list for GCR/Artifact Registry + guardrails images. |
| `policies/network-policies/default-deny.yaml` | COPY | |
| `policies/network-policies/per-namespace/*` | ADAPT | Reuse pattern; write new per-namespace rules for burritbot-* and burritbot-net. |

**New files (no source):**
- `policies/kyverno/require-model-provenance.yaml`
- `policies/kyverno/require-inference-labels.yaml`
- `policies/kyverno/restrict-gpu-requests.yaml`
- `policies/kyverno/require-guardrails-sidecar.yaml`
- `policies/kyverno/require-otel-annotations.yaml`
- `policies/network-policies/burritbot-unguarded.yaml` (intentionally wide open)
- `policies/network-policies/burritbot-guarded.yaml` (locked to `burritbot-net` only)

## `security/`

| Source path | Decision | Notes |
|---|---|---|
| `security/falco/eks-aware-rules.yaml` | ADAPT | The spec refers to `custom-rules.yaml`; this file is the real source. Copy the non-EKS-specific rules into `security/falco/custom-rules.yaml`, then add `ai-workload-rules.yaml` alongside it. |
| `security/cert-manager/` | ADAPT | ClusterIssuer structure for Let's Encrypt via GCP DNS (if demo domain is used). |
| `security/eso/` | ADAPT | Switch backend to `gcpsm`. |
| `security/quotas-pdbs/` | COPY | ResourceQuota + PDBs generic enough to reuse. |
| `security/rbac/` | ADAPT | Remove EKS-specific subjects; keep structure. |

**New files (no source):**
- `security/falco/ai-workload-rules.yaml`
- `security/falcosidekick/values.yaml` (new, wired to Grafana)
- `security/rbac/cluster-roles.yaml` (new, minimal set for burritbot SAs)

## `observability/`

| Source path | Decision | Notes |
|---|---|---|
| `observability/grafana/dashboards/*` | IGNORE | Old platform-overview dashboard; replaced with 3 new demo-specific dashboards. |

**New files (no source):**
- `observability/otel-collector/config.yaml` (GenAI semconv processors)
- `observability/otel-weaver/genai-semconv-registry.yaml`
- `observability/spinybacked-orbweaver/config.yaml`
- `observability/prometheus/values.yaml`
- `observability/prometheus/rules/ai-alerts.yaml`
- `observability/grafana/dashboards/the-eyes-overview.json`
- `observability/grafana/dashboards/prompt-response-traces.json`
- `observability/grafana/dashboards/cast-net-comparison.json`

## `tests/`

| Source path | Decision | Notes |
|---|---|---|
| `tests/conftest.py` | ADAPT | Keep fixture structure; swap AWS boto3 fixtures for GCP google-cloud fixtures. |
| `tests/helpers/` | ADAPT | Keep `wait_helpers.py`/`kubectl_helpers.py` patterns; rewrite anything AWS-specific. |
| `tests/test_phase_01_foundation.py` | ADAPT | Reuse assertion structure; retarget all infrastructure assertions at GKE / WIF / GCP Secret Manager. |
| `tests/test_phase_02_gitops.py` | COPY | Mostly ArgoCD-native assertions, not EKS-specific. |
| `tests/test_phase_03_security.py` | ADAPT | Renumbered to Phase 4 in new layout; extend with AI policies + Falco rules. |
| `tests/test_phase_04_observability.py` | ADAPT | Renumbered to Phase 3; extend with GenAI semconv assertions. |
| `tests/test_phase_05_portal.py` | IGNORE | Backstage — not in scope. |
| `tests/test_phase_06_integration.py` | ADAPT | Rework as Phase 6 burritbot integration test. |
| `tests/test_phase_07_hardening.py` | COPY | Generic hardening checks mostly apply. |

**New files (no source):**
- `tests/test_phase_05_ai_gateway.py`
- `tests/test_phase_06_burritbot.py`
- `tests/test_phase_07_frontend.py`
- `tests/test_phase_08_hardening.py` (may replace the old #7)

## `spec/` and `docs/`

| Source path | Decision | Notes |
|---|---|---|
| `spec/BUILD-SPEC.md` | IGNORE | Old EKS spec; this repo's authoritative spec is `docs/BUILD-INSTRUCTIONS.md`. |
| `spec/SCORECARD.md` | ADAPT (optional) | Only if Michael wants a scorecard pass for NA 2026. |
| `docs/ARCHITECTURE.md` | ADAPT (Phase 8) | Carry forward the layout; rewrite content for the guardrails stack. |
| `docs/SETUP.md` | ADAPT (Phase 8) | Rewrite for GCP setup. |
| `docs/COST.md` | ADAPT (Phase 8) | Replace AWS pricing with GCP pricing. |
| `docs/TEARDOWN.md` | ADAPT (Phase 8) | `terraform destroy` + `gcloud` cleanup. |
| `docs/SECURITY.md` | ADAPT (Phase 8) | Carry forward defense-in-depth framing; extend with AI guardrails layer. |
| `docs/WALKTHROUGH.md` | IGNORE | Prior-talk narrative; new talk needs its own. |
| `docs/LESSONS-LEARNED.md` | IGNORE | Prior talk. |
| `docs/VERSION-MAP.md` | REFERENCE | Do not copy; use as a cross-check for component versions. |
| `docs/EIGHT-GUARDRAILS*.md` | REFERENCE | Conceptual framework; may inform the NA 2026 slide structure but not copied. |
| `docs/adr/*` | REFERENCE | Prior decisions; write new ADRs only when we change something. |

## `backstage/`, `collateral/`, `recordings/`, `sample-app/`, `scorecard/`, `scripts/`, `prompts/`

| Source path | Decision | Notes |
|---|---|---|
| `backstage/*` | IGNORE | Not in scope. |
| `collateral/*` | REFERENCE | New talk collateral will be written from scratch. |
| `recordings/*` | IGNORE | Prior talk recordings. |
| `sample-app/*` | IGNORE | Replaced by BurritBot. |
| `scorecard/*` | ADAPT (optional) | Only if scorecard is in scope for NA. |
| `scripts/*` | ADAPT | Reuse utility patterns; rewrite anything AWS CLI–specific. |
| `prompts/*` | REFERENCE | Useful as prior art for phase kickoff prompts. |

## Phase-by-Phase Reuse Checklist

### Phase 1 — GKE Foundation
- ADAPT: `infrastructure/terraform/variables.tf`, `outputs.tf`, `vpc.tf`
- COPY: `pyproject.toml`, `.python-version`, `.yamllint.yml`, `.gitleaks.toml`
- NEW: `gke.tf`, `iam.tf` (WIF), `secret-manager.tf`, `dns.tf`, `main.tf` (GCP)

### Phase 2 — GitOps Bootstrap
- COPY: `.claude/skills/argocd-patterns.md`, `gitops/namespaces/namespaces.yaml` (adapt list)
- ADAPT: `gitops/argocd/values.yaml`, `gitops/bootstrap/app-of-apps.yaml`, `gitops/apps/namespaces.yaml`, `gitops/apps/rbac.yaml`

### Phase 3 — The Eyes (Observability)
- EXTEND: `.claude/skills/otel-wiring.md`, `gitops/apps/otel-collector.yaml`, `gitops/apps/prometheus.yaml`, `gitops/apps/grafana-dashboards.yaml`
- COPY: `gitops/apps/tempo.yaml`, `gitops/apps/loki.yaml` (if logs needed)
- NEW: All three Grafana dashboards (`the-eyes-overview.json`, `prompt-response-traces.json`, `cast-net-comparison.json`), OTel Collector config, spinybacked-orbweaver config, GenAI semconv registry

### Phase 4 — The Net — Security
- COPY: `policies/kyverno/disallow-privileged.yaml`, `require-networkpolicy.yaml`, `require-probes.yaml`, `require-resource-limits.yaml`; `policies/network-policies/default-deny.yaml`
- EXTEND: `.claude/skills/kyverno-policies.md`, `.claude/skills/falco-rules.md`, `policies/kyverno/require-labels.yaml`, `security/falco/custom-rules.yaml`
- ADAPT: `gitops/apps/kyverno.yaml`, `gitops/apps/falco.yaml`, `gitops/apps/falcosidekick.yaml`, `gitops/apps/external-secrets.yaml`
- NEW: `require-model-provenance.yaml` (with `burritbot.io/layer: the-net` labels), `require-inference-labels.yaml`, `restrict-gpu-requests.yaml`, `require-guardrails-sidecar.yaml` (matches `burritbot-*` container names in `burritbot-guarded`), `require-otel-annotations.yaml`; `ai-workload-rules.yaml` (tagged `[burritbot, the-net, ...]`); per-burritbot network policies

### Phase 5 — The Net — AI Gateway
- No source reuse. All-new files under `guardrails/` and `gitops/apps/envoy-ai-gateway/`, `nemo-guardrails/`, `llm-guard/`. Deployed into the `burritbot-net` namespace.

### Phase 6 — BurritBot
- No source reuse. New `app/burritbot/` tree plus `gitops/apps/burritbot-unguarded/` and `burritbot-guarded/`.

### Phase 7 — Audience Frontend
- No source reuse. New `app/audience-frontend/` tree plus `gitops/apps/audience-frontend/`.

### Phase 8 — Hardening
- ADAPT: `docs/ARCHITECTURE.md`, `docs/SETUP.md`, `docs/COST.md`, `docs/TEARDOWN.md`, `docs/SECURITY.md` from kubeauto-ai-day as templates.
- COPY: `scripts/` utilities if any are still relevant.

## Discrepancies Noted

These are differences between `BUILD-INSTRUCTIONS.md`'s "What to Grab" list and
the actual file layout in kubeauto-ai-day:

1. **`security/falco/custom-rules.yaml` doesn't exist by that name.** The
   actual file is `security/falco/eks-aware-rules.yaml`. Phase 4 should copy
   the non-EKS-specific portion into a new `security/falco/custom-rules.yaml`
   and add `ai-workload-rules.yaml` next to it.
2. **`gitops/argocd/install.yaml` and `argocd-cm.yaml` don't exist.** The only
   file in that directory is `values.yaml`. The argocd install is Helm-based
   via the chart. Phase 2 should carry the `values.yaml` over (with ingress
   replaced) and wrap it in a new `install.yaml` Application manifest if the
   new layout calls for one.
3. **The kubeauto-ai-day phase order is different** (EKS foundation → GitOps →
   Security → Observability → Portal → Integration → Hardening). This repo
   reorders Phase 3 and Phase 4 so Observability comes before Security. Test
   files should be renumbered accordingly.
