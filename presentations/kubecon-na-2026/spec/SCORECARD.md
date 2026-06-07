# burritbot Scorecard

Honest per-component scorecard for the KubeCon NA 2026 burritbot
demo build. Update after each component passes its tests. Red cells
that tell the truth are more useful to the audience than green cells
that lie.

## Status key

- GREEN — component is deployed and the test for it is passing
- YELLOW — component is deployed but tests are partial or a
  workaround is in place
- RED — component is missing or tests fail
- n/a — not in scope for this build

## Layer summary

| Layer | Components | Status | Notes |
|-------|-----------|--------|-------|
| Foundation | GKE Standard + NAP, WIF, Secret Manager, VPC | RED | Phase 1 not started |
| The Web | ArgoCD, cert-manager, External Secrets | RED | Phase 2 not started |
| The Eyes | OTel Collector, Weaver, spinybacked-orbweaver, Prometheus, Grafana | RED | Phase 3 not started |
| The Net (Security) | Kyverno, Falco | RED | Phase 4 not started |
| The Net (AI Gateway) | NeMo Guardrails, LLM Guard, Envoy AI Gateway | RED | Phase 5 not started |
| Application | BurritBot (FastAPI + Vertex AI) | RED | Phase 6 not started |
| Audience | FastAPI frontend + cast-net.sh | RED | Phase 7 not started |
| Hardening | Runbook, scorecard, teardown | RED | Phase 8 not started |

## Per-component detail

### Phase 1 — Foundation

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| Terraform (Google provider) | Foundation | ~> 7.0 (GA 7.27.0) | RED | |
| GKE Standard + NAP | Foundation | 1.34+ | RED | |
| Workload Identity Federation | Foundation | n/a | RED | |
| Secret Manager | Foundation | n/a | RED | |

### Phase 2 — The Web (GitOps)

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| ArgoCD | The Web | 3.x | RED | |
| cert-manager | The Web | 1.20+ | RED | |
| External Secrets Operator | The Web | 0.10+ | RED | |

### Phase 3 — The Eyes

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| OpenTelemetry Collector | The Eyes | 0.149+ | RED | Needs `gen_ai.provider.name` attribute processor (semconv v1.37.0) |
| OTel Weaver | The Eyes | 0.22+ | RED | |
| spinybacked-orbweaver | The Eyes | in-repo | RED | Score threshold 0.85 |
| Prometheus (kube-prometheus-stack) | The Eyes | latest | RED | |
| Grafana | The Eyes | 12.x | RED | Three demo dashboards |

### Phase 4 — The Net (Security)

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| Kyverno | The Net | chart 3.7.1 / app 1.17+ | RED | CEL expressions for burritbot.io labels |
| Falco | The Net | 0.43.x / rules engine 0.57.0 | RED | modern-bpf driver, burritbot tags |

### Phase 5 — The Net (AI Gateway)

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| NeMo Guardrails | The Net | 0.11+ | RED | Four Colang rails |
| LLM Guard | The Net | 0.3.17+ | RED | Input + output scanners |
| Envoy AI Gateway | The Net | 0.2+ | RED | Gateway API v1.2 |

### Phase 6 — Application

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| FastAPI BurritBot | Application | 0.1.0 | RED | |
| Vertex AI (gemini-3-pro via google-genai) | Application | GA | RED | 1.5 / 2.0 / 2.5 variants are forbidden |

### Phase 7 — Audience

| CNCF Project | Layer | Version | Status | Notes |
|--------------|-------|---------|--------|-------|
| FastAPI audience frontend | Audience | 0.1.0 | RED | 10/minute per-IP rate limit |
| cast-net.sh | Audience | 0.1.0 | RED | Live traffic toggle |

### Phase 8 — Hardening

| Artifact | Layer | Status | Notes |
|---------|-------|--------|-------|
| docs/RUNBOOK.md | Hardening | RED | Six required sections |
| docs/SCORECARD.md | Hardening | YELLOW | This file (skeleton) |
| scripts/teardown.sh | Hardening | RED | |
| Rehearsal run (end-to-end) | Hardening | RED | |

## Rehearsal Log

Record each rehearsal with date, what worked, what did not. Do not
edit the entries — append new ones below.

_(no rehearsals yet)_
