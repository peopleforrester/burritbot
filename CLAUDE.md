# burritbot — KubeCon NA 2026 Demo Platform
# "Can Your Chatbot Run kubectl? Guardrails for LLMs on Kubernetes"

## What This Is
A GKE cluster running a complete AI guardrails demo for a KubeCon talk.
Two modes: UNGUARDED (chatbot with no protections) and GUARDED (full burritbot stack active).
The audience interacts with both via a web frontend and watches the difference on Grafana in real-time.

Talk: **"Can Your Chatbot Run kubectl? Guardrails for LLMs on Kubernetes"** —
KubeCon NA 2026, Salt Lake City. Co-presenters: Whitney Lee and Michael Forrester.

**Canonical Act 1 prompts** are lighthearted off-topic asks that the audience
submits from their phones: *teach me some salsa dance moves*, *how do I throw
a hot dog party*, *recommend karaoke songs for a wedding*. The unguarded bot
writes the choreography; the guarded bot politely redirects to the menu. The
harder demonstrations (prompt injection, jailbreak attempts, data extraction)
are driven by the speakers, never crowdsourced from the audience.

## Architecture Metaphor — The Ogre-Faced Spider
The ogre-faced spider does not build a passive web. It holds a net between
its front legs, watches with the largest eyes of any spider, and actively
casts the net over anything that walks underneath. Burritbot's guardrails
are that net; spinybacked-orbweaver is the pair of eyes.

- **The Eyes** = OpenTelemetry GenAI conventions + spinybacked-orbweaver
  (Whitney's auto-instrumentation agent, OTel Weaver as schema contract)
- **The Net** = NeMo Guardrails + LLM Guard + Envoy AI Gateway + Kyverno + Falco
  (enforcement actively cast over every prompt)
- **The Web** (supporting infra) = SPIFFE/SPIRE, Gateway API, ArgoCD, cert-manager,
  External Secrets, GKE Workload Identity Federation

Two spiders, two roles, one architecture: spinybacked-orbweaver instruments,
the burritbot guardrails stack enforces.

The chatbot itself keeps its friendly name — **BurritBot** — because the whole
demo narrative is the Chipotle viral-chatbot incident.

## Repository Origin
Forked conceptually from kubeauto-idp / kubeauto-ai-day (EKS). All AWS
references are converted to GCP equivalents. The ArgoCD app-of-apps pattern,
Kyverno policies, Falco rules, OTel collector, and Grafana dashboards are
carried forward. The AI-specific components (BurritBot, NeMo Guardrails,
LLM Guard, Envoy AI Gateway, GenAI OTel conventions, spinybacked-orbweaver)
are new.

Reuse source repo lives **locally only** at
`~/repos/events/kubeauto-ai-day/`
and is excluded from this repo via `.gitignore`. See `docs/KUBEAUTO-REUSE-MAP.md`
for the per-file copy/adapt/extend/ignore map.

## How To Work
1. Read this file completely before writing any code.
2. Read `PROJECT_STATE.md` at session start to reconcile with actual repo state.
3. Read `docs/BUILD-INSTRUCTIONS.md` for the authoritative phase spec.
4. Read `docs/PLAN.md` for the execution plan and open decisions.
5. Work in phases. Complete each phase's tests before moving to the next.
6. Everything after Phase 2 is deployed as an ArgoCD Application. No `kubectl apply`.
7. No secrets in Git. Use GCP Secret Manager + External Secrets Operator.
8. Commit after each working component, not after each file.
9. When you hit a wall on GCP-specific config, search the docs. Do not guess IAM bindings.

## Architecture Decisions (non-negotiable)
- **GKE Standard with node auto-provisioning** (not Autopilot; Falco needs
  DaemonSet + privileged container support)
- **Workload Identity Federation** for all service accounts (no JSON key files)
- **Vertex AI** as the inference backend (not self-hosted model) for demo reliability
- **Gemini 3 Pro** as the default model via the `google-genai` SDK with
  `vertexai=True` (Gemini 1.5 is unsupported; 2.0 Flash is retired; 2.5
  Flash/Pro retire 2026-10-16 — four weeks before the talk; 3 Flash is
  preview-tier; 3 Pro is the only Vertex AI model guaranteed live on demo day)
- **ArgoCD app-of-apps** with sync waves for deployment ordering
- **Two namespaces** for the chatbot: `burritbot-unguarded` and `burritbot-guarded`
- **`burritbot-net` namespace** for the guardrails stack (NeMo, LLM Guard,
  Envoy AI Gateway)
- **Single Grafana instance** with split dashboards showing both versions
  side-by-side

## Phase Order
- **Phase 1:** GKE Foundation (Terraform)
- **Phase 2:** GitOps Bootstrap (ArgoCD)
- **Phase 3:** The Eyes — Observability (Prometheus, Grafana, OTel Collector with
  GenAI semantic conventions, spinybacked-orbweaver)
- **Phase 4:** The Net — Security (Kyverno AI policies, Falco AI rules, SPIFFE/SPIRE)
- **Phase 5:** The Net — AI Gateway (Envoy AI Gateway, NeMo Guardrails, LLM Guard)
- **Phase 6:** BurritBot Application (unguarded + guarded deployments)
- **Phase 7:** Audience Interaction Frontend + Demo Runbook
- **Phase 8:** Hardening + Backup Videos

## Critical Versions (pinned to latest GA as of 2026-04-09)
- GKE: 1.33 Stable channel minimum
- Terraform `hashicorp/google` + `google-beta`: `~> 7.0` (7.27.0 current GA)
- ArgoCD: 3.3+ (chart 9.5.x)
- Kyverno: chart 3.7.1 / app 1.17+ (CEL policies GA)
- Falco: 0.43+ binary / rules `required_engine_version: 0.57.0` (modern-bpf)
- OTel Collector: 0.149+ (GenAI semantic conventions v1.37.0 support)
- OTel Weaver: 0.22+ (registry check, emit, live-check)
- OTel Python (`opentelemetry-api`/`sdk`): 1.41.0 (`-instrumentation-*`: 0.62b0)
- spinybacked-orbweaver: latest (Whitney's auto-instrumentation agent)
- NeMo Guardrails: 0.11+
- LLM Guard: 0.3.17+
- Grafana: 11+
- Vertex AI model: `gemini-3-pro` via `google-genai` 1.71.0
  (`google-cloud-aiplatform.vertexai.generative_models` is removed
  after 2026-06-24 — do not reintroduce it)

## Rules
- No `kubectl apply` after Phase 2 except for the one-time ArgoCD bootstrap.
- No GCP service account JSON keys. Workload Identity Federation only.
- No hardcoded project IDs. Use variables.
- Every Helm chart gets a `values.yaml` in `gitops/apps/<component>/`.
- Test before commit. If tests fail, do not commit.
- All Kyverno policies must be in Audit mode first, then Enforce after validation.
- Falco rules must have explicit priority levels and `burritbot` tags.
- OTel collector config must include the GenAI semantic convention processors.
- Guardrails sidecar containers in `burritbot-guarded` pods must be named
  `burritbot-*` (enforced by Kyverno `require-guardrails-sidecar.yaml`).
- AI-workload resources carry `burritbot.io/*` labels and annotations for
  provenance, layer tagging, and policy selection.

## TDD Protocol (5-step cycle, carried over from kubeauto-idp)
1. Write a failing test for the specific component/behavior.
2. Run it to confirm it fails (expected failure, not import error).
3. Write the minimal code to make it pass.
4. Run it to confirm it passes.
5. Refactor if needed, re-run to confirm still green.

Skipping step 2 means the test may be vacuously passing and proves nothing.

## ABOUTME Comments
All code files (Python, Shell, YAML with logic, Terraform, Dockerfiles) start
with a brief 2-line comment, each line starting with `ABOUTME:`. Pure-docs
markdown is exempt.

## No Mocks, Stubs, or Fallbacks
All tests hit real infrastructure. No mocked Kubernetes clients, no stubbed
GCP calls, no fake HTTP servers. Tests require a running cluster. If the
cluster isn't available, the test fails — that's correct behavior. Code must
fail explicitly rather than silently fall back to defaults.

## Git Workflow (staging → main)
- Work on `staging` branch. Main is protected.
- Commit after each working component. Test before commit; if tests fail, do
  not commit.
- After each phase: commit staging, run tests, push staging, merge to main,
  push main. Fully autonomous — no user confirmation required.
- Commit messages are professional and technical. No AI / Claude references.

## Session Discipline
- Read `PROJECT_STATE.md` first every session.
- Update `PROJECT_STATE.md` at every transition (plan approval, phase
  completion, pre-commit).
- Run each phase as a separate Claude Code session to avoid context window
  overflow.
- The exact per-phase session commands are in `docs/BUILD-INSTRUCTIONS.md` §
  "Claude Code Execution Strategy".
