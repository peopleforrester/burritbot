# burritbot Scorecard

Honest per-component scorecard for the KubeCon NA 2026 burritbot demo
build. Red cells that tell the truth are more useful to the audience
than green cells that lie. This file is the demo-day source of truth;
the skeleton at `spec/SCORECARD.md` is the build-time template.

## Status key

- **GREEN** — deployed to the live cluster and phase tests pass
- **YELLOW** — authored and static tests green, live validation pending
- **RED** — missing, broken, or failing
- **n/a** — intentionally not in scope for this build

## Layer summary

| Layer | Components | Status | Notes |
|-------|-----------|--------|-------|
| Foundation | GKE Standard + NAP, WIF, Secret Manager, VPC | YELLOW | Phase 1 static tests pass; not yet applied |
| The Web | ArgoCD app-of-apps, sync waves | YELLOW | Phase 2 static tests pass |
| The Eyes | OTel Collector, Weaver, spinybacked-orbweaver, dashboards | YELLOW | Phase 3 static tests pass |
| The Net (Security) | Kyverno, Falco | YELLOW | Phase 4 static tests pass |
| The Net (AI Gateway) | NeMo Guardrails, content scanners, Envoy AI Gateway | YELLOW | Phase 5 static tests pass |
| Application | BurritBot (FastAPI + Vertex) | YELLOW | Phase 6 static tests pass |
| Audience | FastAPI frontend + cast-net.sh | YELLOW | Phase 7 static tests pass |
| Hardening | Runbook, scorecard, teardown | YELLOW | Phase 8 static tests pass |

## Per-component detail

### Phase 1 — Foundation

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| Terraform (Google provider) | Foundation | ~> 7.0 (GA 7.27.0) | YELLOW | HCL authored; `terraform validate` deferred |
| GKE Standard + NAP | Foundation | 1.34+ | YELLOW | Non-negotiable: not Autopilot (Falco needs privileged) |
| Workload Identity Federation | Foundation | n/a | YELLOW | No JSON keys anywhere in the repo |
| Secret Manager | Foundation | n/a | YELLOW | Vertex secret declared; actual payload injected at apply time |

### Phase 2 — The Web (GitOps)

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| ArgoCD | The Web | 3.x | YELLOW | Helm values + app-of-apps authored |
| Namespaces app | The Web | — | YELLOW | Seven namespaces declared in one manifest |
| Sync waves | The Web | — | YELLOW | -10 ns → -5 kyverno → 0 monitoring/security → 1 gateway/burritbot → 2 audience |

### Phase 3 — The Eyes

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| OpenTelemetry Collector | The Eyes | 0.149+ | YELLOW | `memory_limiter` first; `gen_ai.provider.name` attributes processor present (semconv v1.37.0) |
| OTel Weaver | The Eyes | 0.22+ | YELLOW | Registry covers `gen_ai` + `burritbot` attribute groups |
| spinybacked-orbweaver | The Eyes | in-repo | YELLOW | Score threshold pinned at 0.85 |
| Grafana dashboards | The Eyes | 12.x | YELLOW | Three demo dashboards: Eyes Overview / Prompt-Response / Cast the Net |

### Phase 4 — The Net (Security)

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| Kyverno | The Net | chart 3.7.1 / app 1.17+ | YELLOW | CEL bracket syntax for `burritbot.io/*` labels |
| require-burritbot-labels | The Net | — | YELLOW | Enforces `burritbot.io/layer`, `model-source`, `model-hash` |
| require-burritbot-sidecar-naming | The Net | — | YELLOW | `burritbot-` prefix enforced on guarded sidecars |
| restrict-burritbot-network | The Net | — | YELLOW | Generates NetworkPolicy locking egress to burritbot-net + DNS |
| Falco | The Net | 0.43.x / rules engine 0.57.0 | YELLOW | modern-bpf, tagged `[burritbot, the-net, ...]` |

### Phase 5 — The Net (AI Gateway)

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| NeMo Guardrails | The Net | 0.11+ | YELLOW | Colang 2.0: burrito-only, jailbreak-detect, topic-enforcement, output-sanitize |
| Content scanners | The Net | 0.3.17+ | YELLOW | Input + output scanner lists populated; double-escaped regex |
| Envoy AI Gateway | The Net | 0.2+ | YELLOW | Gateway + HTTPRoute + AIGatewayRoute chaining both ExtProc filters |

### Phase 6 — Application

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| FastAPI BurritBot | Application | 0.1.0 | YELLOW | Factory pattern, lazy Vertex init, typed Pydantic request/response |
| Vertex (gemini-3-pro via google-genai) | Application | GA | YELLOW | 1.5 / 2.0 / 2.5 variants are forbidden by tests |
| Dockerfile | Application | — | YELLOW | python:3.13-slim, non-root UID 1001, tini + uvicorn |
| K8s manifests | Application | — | YELLOW | Unguarded + guarded Deployments and Services; full burritbot.io label set |

### Phase 7 — Audience

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| FastAPI audience frontend | Audience | 0.1.0 | YELLOW | slowapi `10/minute` per-IP; CORS locked to demo origins |
| cast-net.sh | Audience | 0.1.0 | YELLOW | `kubectl patch --type=json`; cast / recall / status |
| Deployment in `audience` ns | Audience | — | YELLOW | Non-root, readOnlyRootFilesystem, probes |

### Phase 8 — Hardening

| Artifact | Layer | Status | Notes |
|---------|-------|--------|-------|
| docs/RUNBOOK.md | Hardening | YELLOW | Pre-flight / Act 1 / Act 2 / Cast the Net / Teardown / Rollback |
| docs/SCORECARD.md | Hardening | YELLOW | This file |
| scripts/teardown.sh | Hardening | YELLOW | Invokes `terraform destroy` with confirmation |
| Rehearsal run (end-to-end) | Hardening | RED | Requires live cluster |

## Rehearsal Log

Record each rehearsal with date, what worked, what did not. Do not
edit past entries — append new ones below.

_(no rehearsals yet — first one is gated on live Phase 1 apply)_
