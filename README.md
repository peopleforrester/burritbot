# burritbot — A Reusable AI-Guardrails Demo Platform for Kubernetes

burritbot is a self-contained Kubernetes platform that runs the *same*
chatbot two ways at once — completely unguarded in one namespace, and
locked behind a layered guardrails stack in another — so the difference
in behavior is observable in real time on a single Grafana dashboard.

## The Name

**burritbot** is the ogre-faced spider. Unlike most spiders that build a
passive web and wait, the ogre-faced spider holds a net between its
front legs, watches with the largest eyes of any spider, and actively
casts the net over anything that walks underneath. That hunting strategy
*is* the architecture:

- **The Eyes** — OpenTelemetry GenAI semantic conventions plus the
  [spinybacked-orbweaver](https://github.com/wiggitywhitney/spinybacked-orbweaver)
  auto-instrumentation agent. Everything the platform sees, it sees through
  the eyes.
- **The Net** — NeMo Guardrails + LLM Guard + Envoy AI Gateway + Kyverno +
  Falco. Actively cast over every inference request. Catches what does
  not belong.

Two spiders, two roles, one architecture: spinybacked-orbweaver
instruments, burritbot enforces. The chatbot itself keeps a friendly
name — **BurritBot** — because the demo opens with the viral Chipotle
chatbot incident (order a burrito, also reverse a linked list in Python).

## The Demo Pattern

Two acts, one burrito shop.

- **Act 1 — Unguarded.** BurritBot is deployed with no protections. The
  audience submits lighthearted off-topic prompts from their phones
  (*teach me some salsa dance moves*, *how do I throw a hot dog party*).
  BurritBot cheerfully obliges every one of them, just like Chipotle's
  customer support bot that helped a user reverse a linked list in
  Python while he was trying to order a bowl. It's funny on stage. It is
  the exact same failure mode that lets an internal bot answer questions
  it should never be answering.
- **Act 2 — Guarded.** The same chatbot runs in a second namespace
  behind the burritbot net (Envoy AI Gateway → NeMo Guardrails →
  LLM Guard → Vertex AI), with Kyverno policies, Falco rules, and OTel
  GenAI semantic conventions wired through to a live Grafana dashboard.
  The same audience prompts come in and get politely redirected to the
  menu. The presenters then escalate to harder cases (prompt injection,
  jailbreak attempts, data extraction) and the audience watches every
  one of them get blocked, logged, and traced in real time.

The point: **platform-level governance, not per-developer discipline.**
The platform does the guardrailing. The developer writes a normal app.

## Repo Status

The platform is in active development. See `PROJECT_STATE.md` for the
current phase and what's verified-static vs verified-live.

## Talks Using This Platform

Event-specific delivery artifacts (runbook, scorecard, CFP text,
build-day plan) live under `presentations/<event>/` so the platform
itself stays event-neutral. Today:

- `presentations/kubecon-na-2026/` — Whitney Lee and Michael Forrester,
  KubeCon NA 2026, Salt Lake City. *"Can Your Chatbot Run kubectl?
  Guardrails for LLMs on Kubernetes."*

Future deliveries get their own sibling subfolder under `presentations/`.

## Key Documents

| Document | Purpose |
|----------|---------|
| `PROJECT_STATE.md` | Current phase and verified-static vs verified-live status. |
| `docs/KUBEAUTO-REUSE-MAP.md` | Per-file copy/adapt/ignore map from the upstream EKS reference. |
| `docs/PHASE-B-EKS-ADAPT-PLAN.md` | EKS-to-GKE manifest adaptation plan (executed). |
| `docs/CRITICAL-FIXES-PLAN.md` | Senior-review repair plan (executed). |
| `docs/PHASE-G-GENERICIZE-PLAN.md` | This genericization pass. |
| `presentations/<event>/docs/PLAN.md` | The talk-specific execution plan. |
| `presentations/<event>/docs/RUNBOOK.md` | The talk-specific on-stage runbook. |

## Build Phases

1. **GKE Foundation** — Terraform, VPC, Workload Identity Federation
2. **GitOps Bootstrap** — ArgoCD, app-of-apps, sync waves
3. **The Eyes** — Prometheus, Grafana, OTel Collector with GenAI conventions,
   spinybacked-orbweaver
4. **The Net — Security** — Kyverno AI policies, Falco AI rules
5. **The Net — AI Gateway** — Envoy AI Gateway, NeMo Guardrails, LLM Guard
6. **BurritBot** — Unguarded and guarded FastAPI deployments
7. **Audience Frontend** — Mobile-friendly prompt submission UI + QR code
8. **Hardening** — Full-demo rehearsal, backup videos, cost doc, teardown

Each phase runs in its own Claude Code session. Test-first, ArgoCD-deployed,
no secrets in Git.

## Ancestry

Forked conceptually from [kubeauto-ai-day](https://github.com/peopleforrester/kubeauto-ai-day),
an earlier EKS-based platform delivered live as a conference talk in 2026-03.
That repo lives on disk as a local-only reference; see
`docs/KUBEAUTO-REUSE-MAP.md` for exactly what carries forward.

## License

Apache 2.0 (pending) — matching the upstream lineage.
