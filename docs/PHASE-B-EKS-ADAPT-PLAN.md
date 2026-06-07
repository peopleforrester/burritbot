# Phase B — Adapt EKS Reference Manifests to GKE
# Source: docs/KUBEAUTO-REUSE-MAP.md (per-file decisions already made).
# Reference repo: ~/repos/_archive/events/kubeauto-ai-day/ (a prior live-delivered EKS demo platform).
# Strict TDD, phase by phase, no timelines.

## Verification Method
Each adapted manifest is read directly from the EKS reference, edited
in place under `gitops/apps/<component>.yaml`, and validated by a
static test that asserts the cloud-swap was complete (no AWS strings
remain, GCP equivalents are present, namespaces match the burritbot
layout). The reference repo is treated as authoritative for everything
*except* cloud-provider specifics — its 27/27 components were live-
tested in a prior delivery, so the structural choices are already
proven.

## Why this exists
The critical-fixes pass (docs/CRITICAL-FIXES-PLAN.md) made `deploy/<x>/`
paths resolve, but `deploy/monitoring/`, parts of `deploy/security/`,
and parts of `deploy/ai-gateway/` are still stub Kustomizations
because no ArgoCD Application yaml existed for the underlying Helm
charts (cert-manager, kube-prometheus-stack, OTel Collector,
external-secrets, Falco, Loki, Tempo, Promtail). The EKS reference
ships all of these — Phase B copies them across with the AWS→GCP
edits the reuse map already specifies.

## Cloud-swap cheat sheet (applies to every phase)
| EKS pattern | GKE equivalent |
| --- | --- |
| IRSA annotation `eks.amazonaws.com/role-arn: arn:aws:iam::...:role/X` | WIF annotation `iam.gke.io/gcp-service-account: X@<project>.iam.gserviceaccount.com` |
| AWS Secrets Manager backend (`aws/secretsmanager`) | `gcpsm` backend |
| ALB ingress (`ingressClassName: alb` + alb.ingress.kubernetes.io/* annotations) | GKE Gateway API (`gateway.networking.k8s.io/v1` Gateway + HTTPRoute) |
| ACM cert ARN (`alb.ingress.kubernetes.io/certificate-arn: ...`) | cert-manager-issued cert via ClusterIssuer (HTTP-01 or DNS-01 with Cloud DNS) |
| ECR image registries (`*.dkr.ecr.<region>.amazonaws.com`) | Artifact Registry (`<region>-docker.pkg.dev/<project>/<repo>`) |
| `cluster.name: kubeauto-ai-day` (resource processor) | `cluster.name: burritbot` |
| `aws_*` Terraform | `google_*` Terraform (already done in Phase 1) |
| EC2 IMDS Falco rule (`fd.sip = "169.254.169.254"`) | GCE metadata Falco rule (same IP — keep but reframe the description and tags from `aws` → `gcp`) |
| Demo hostname `*.ai-enhanced-devops.com` | Demo hostname under a burritbot-owned domain (or omit ingress entirely for the demo and use `kubectl port-forward`) |

## Common test pattern (every phase reuses this)
For each adapted Application yaml, the static test asserts:
1. The file exists at `gitops/apps/<name>.yaml`.
2. `apiVersion`/`kind`/`metadata.name` are an ArgoCD Application.
3. `spec.destination.namespace` matches the expected burritbot
   namespace (no `apps`, `platform`, or other EKS-reference namespaces
   that the burritbot layout doesn't use).
4. No AWS-specific strings remain: no `eks.amazonaws.com`,
   `aws_iam_role`, `dkr.ecr`, `alb.ingress.kubernetes.io`, no
   AWS account IDs, no `arn:aws:`.
5. Where the reuse map says EXTEND, the new GenAI / burritbot
   additions are present (e.g. for OTel: GenAI semantic-convention
   processors and `burritbot.io/*` resource attributes).

Each phase adds one parametrized cross-cloud-string test alongside
its component-specific assertions.

## Phase order (smallest swap → largest)

### Phase B1 — cert-manager + cert-manager-issuers
**Swap surface:** tiny. cert-manager chart itself has zero AWS in it.
cert-manager-issuers `repoURL` points at peopleforrester/kubeauto-ai-day
+ `path: security/cert-manager` — rewrite to this repo's `security/cert-manager/`
once the ClusterIssuer manifests are adapted.

**Files:**
- `gitops/apps/cert-manager.yaml` — COPY from EKS, change wave annotation if needed, leave Helm values alone (CRDs enabled, single-replica is fine for demo).
- `gitops/apps/cert-manager-issuers.yaml` — COPY structure, rewrite `repoURL` to this repo, `path: security/cert-manager`.
- `security/cert-manager/letsencrypt-staging.yaml`, `letsencrypt-production.yaml` — copy ClusterIssuer manifests from EKS reference, leave alone (ACME HTTP-01 is cloud-agnostic). If the demo doesn't use a real hostname, mark these as disabled / commented and document why.

**Test:** `tests/test_phase_b1_cert_manager.py`
- Application yaml exists for `cert-manager` and `cert-manager-issuers`.
- Both Applications target the `cert-manager` namespace (or whatever the burritbot layout uses — TBD: add `cert-manager` to `EXPECTED_NAMESPACES` if not present).
- No AWS strings remain.
- Wave order: cert-manager < cert-manager-issuers.

### Phase B2 — external-secrets
**Swap surface:** small. IRSA annotation → WIF annotation. Chart and namespace are GCP-agnostic.

**Files:**
- `gitops/apps/external-secrets.yaml` — adapt: `eks.amazonaws.com/role-arn: arn:aws:iam::...` → `iam.gke.io/gcp-service-account: REPLACE_WITH_ESO_GSA_EMAIL`. Switch `namespace: platform` → namespace already in this repo's layout (likely `security` or a new `external-secrets` namespace — pick during the phase).
- Add a placeholder `security/eso/burritbot-secrets.yaml` ExternalSecret pointing at `gcpsm` backend (NOT `aws/secretsmanager`).

**Test:** `tests/test_phase_b2_external_secrets.py`
- Application yaml exists.
- IRSA pattern is absent; WIF annotation is present.
- No AWS Secrets Manager refs; `gcpsm` is the only backend.

### Phase B3 — kube-prometheus-stack
**Swap surface:** medium. ALB ingress block is the biggest chunk to delete + replace; ACM cert ARN to drop; alert rule names need rename from `idp-*` to `burritbot-*`; add a ServiceMonitor (or PodMonitor) for the OTel Collector.

**Files:**
- `gitops/apps/prometheus.yaml` — adapt: drop the entire `grafana.ingress` ALB block (replace with a Gateway-API-based HTTPRoute in a separate file under `observability/grafana/` OR omit ingress entirely and document `kubectl port-forward 3000:80`); rename `idp-node-alerts` → `burritbot-node-alerts`, `idp-app-alerts` → `burritbot-app-alerts`; keep `additionalDataSources` (Tempo + Loki) as-is.
- Optionally: `observability/grafana/httproute.yaml` (new) if Gateway API is wanted.

**Test:** `tests/test_phase_b3_prometheus.py`
- Application yaml exists.
- No `alb.ingress.kubernetes.io/*` annotations, no `arn:aws:acm`.
- No `idp-` alert names; `burritbot-` rename complete.
- Tempo + Loki datasources still present.

### Phase B4 — OTel Collector (EXTEND, not just ADAPT)
**Swap surface:** medium. The EKS config is solid — DaemonSet, OTLP receivers, batch + memory_limiter processors. Need to add GenAI semantic-convention processors per `~/.claude/rules/tools/opentelemetry.md` and the existing `observability/otel-collector/config.yaml` work from Phase 3.

**Files:**
- `gitops/apps/otel-collector.yaml` — adapt: change `cluster.name: kubeauto-ai-day` → `cluster.name: burritbot`; EXTEND `processors:` with the GenAI attribute mapper from the existing Phase 3 config (`gen_ai.provider.name`, `gen_ai.request.model`, etc.); keep prometheusremotewrite + otlp/tempo exporters.

**Test:** `tests/test_phase_b4_otel_collector.py`
- Application yaml exists.
- `cluster.name` value is `burritbot`.
- GenAI processors present (string match against `gen_ai.` substring in the processors block).
- DaemonSet mode; OTLP gRPC 4317 + HTTP 4318 ports exposed.

### Phase B5 — Falco + Falcosidekick
**Swap surface:** medium. EKS-aware rules section needs reframing — the IMDS rule's IP (169.254.169.254) is the same on GCE, but the description, tags (`aws`), and "EKS with Pod Identity" prose need rewriting for GKE + WIF. The existing burritbot Falco rules at `security/falco/rules/burritbot-the-net.yaml` need to be wrapped into the Helm chart's `customRules:` block (or referenced via a ConfigMap the chart consumes).

**Files:**
- `gitops/apps/falco.yaml` — adapt: rename `customRules.eks-aware-rules.yaml` → `customRules.gke-aware-rules.yaml`; rewrite the IMDS rule description and tags; ADD a `customRules.burritbot-the-net.yaml` entry copy-pasted from `security/falco/rules/burritbot-the-net.yaml` (resolves the C19 Falco list issue from the senior review at the same time — `burritbot_net_ips` will need defining here too).
- `gitops/apps/falcosidekick.yaml` — copy from EKS, retarget outputs (today's EKS reference routes to Grafana — same target works on GKE; verify no AWS bits).

**Test:** `tests/test_phase_b5_falco.py`
- Application yaml exists.
- No `aws` tag on any Falco rule; `gcp`/`gke` substituted where the rule is cloud-aware.
- The burritbot-the-net rules are present in the customRules block.
- `burritbot_net_ips` list is defined (closes C19).

### Phase B6 — Loki + Tempo + Promtail
**Swap surface:** smallest. These are mostly COPY per the reuse map. Verify no AWS S3 backend in Loki values (Loki on EKS often uses S3 for chunks) — for the demo, either keep filesystem storage or switch to a GCS bucket via WIF.

**Files:**
- `gitops/apps/loki.yaml` — copy; check `storage.type` (if `s3`, switch to `filesystem` for demo simplicity OR `gcs` if persistence matters).
- `gitops/apps/tempo.yaml` — copy; same storage check.
- `gitops/apps/promtail.yaml` — copy; verify scrape config has no AWS-specific labels.

**Test:** `tests/test_phase_b6_logs_traces.py`
- All three Application yamls exist.
- No AWS storage backends (`s3:` blocks); `filesystem` or `gcs` only.

### Phase B7 — kyverno (chart install, not policies)
**Swap surface:** tiny. The chart install is already a stub `deploy/05-kyverno.yaml` (wired by Phase A1). Just need to verify it matches the EKS reference's chart version (3.7.1 in this repo, check the reference for any deltas) and namespace (`security` here vs whatever EKS used).

**Files:**
- `gitops/apps/kyverno.yaml` (NEW; the existing `gitops/apps/05-kyverno.yaml` is the ArgoCD app-of-apps child — this is a different file under the same naming convention, OR fold into the existing one).

**Test:** `tests/test_phase_b7_kyverno_install.py`
- Application yaml exists and references the correct Helm chart + version.
- Targets the `security` namespace.

### Phase B8 — Wire the new Applications into deploy/ and app-of-apps
**Swap surface:** small. Update the existing `deploy/monitoring/kustomization.yaml`, `deploy/security/kustomization.yaml`, and `deploy/ai-gateway/kustomization.yaml` stubs to reference the new manifests. Update `gitops/bootstrap/app-of-apps.yaml` if the wave ordering needs to shift.

**Files:**
- `deploy/monitoring/kustomization.yaml` — add `../../gitops/apps/prometheus.yaml`, `otel-collector.yaml`, `loki.yaml`, `tempo.yaml`, `promtail.yaml`.
- `deploy/security/kustomization.yaml` — add `../../gitops/apps/cert-manager.yaml`, `cert-manager-issuers.yaml`, `external-secrets.yaml`, `falco.yaml`, `falcosidekick.yaml`. Remove the corresponding TODO comments.
- `deploy/ai-gateway/kustomization.yaml` — only AI-Gateway-specific bits (the actual NeMo / LLM Guard Deployment wrappers are still missing and tracked separately).

**Test:** `tests/test_phase_b8_deploy_wiring.py`
- Each `deploy/<x>/kustomization.yaml` has empty TODO list (no remaining `TODO(critical-fixes-plan)` comments).
- Every Application yaml under `gitops/apps/` is referenced by exactly one `deploy/<x>/kustomization.yaml`.

## Out of scope for Phase B
- **NeMo Guardrails Deployment** wrapping `ai-gateway/nemo-guardrails/config.yaml` — the EKS reference has no NeMo, this is genuinely greenfield. Track as a separate Phase C (NeMo + LLM Guard Deployment authoring), with live verification against the NeMo 0.11 container (the C3 deferred item also lives there).
- **LLM Guard Deployment** — same as NeMo.
- **Grafana dashboard ConfigMaps** wrapping the existing JSON dashboards in `observability/grafana/dashboards/` — touched by Phase B3 if the `sidecar.dashboards.enabled: true` flag is on; if not, a tiny separate phase.
- **All Terraform-side hardening** (C11 GCS backend, C12 private cluster, C13 deletion-protection guard) — different surface, separate plan.
- **Cluster apply, live ArgoCD sync, live test markers** — Phase C/D (requires GCP auth + Terraform installed).

## Commit Strategy
- One commit per phase (B1 through B8) on `staging`.
- Failing test first; minimum implementation; full static suite green before commit.
- Commit message names the EKS source file and the GCP swap: e.g. `feat(B2): adapt external-secrets.yaml from EKS IRSA to GKE WIF`.

## Exit Conditions
- All eight Application yamls land under `gitops/apps/` with passing static tests.
- Every `deploy/<x>/kustomization.yaml` is no longer a stub.
- The Phase A6 truthful-count test still passes (total ≈ 80 + ~16 new = ~96 static tests).
- PROJECT_STATE.md refreshed at the end of Phase B with the new manifest inventory and a clear note that live validation is the remaining hard blocker.
