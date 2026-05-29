# Full Plan — burritbot (Can Your Chatbot Run kubectl?)

Execution plan for the KubeCon NA 2026 demo platform. The authoritative spec
is `BUILD-INSTRUCTIONS.md` (preserved verbatim with a preamble noting the two
small deviations); this file is the *plan* on top of it: what we'll actually
do, in what order, with what reuse, and what decisions remain open.

---

## 1. Talk Framing

- **Title:** "Can Your Chatbot Run kubectl? Guardrails for LLMs on Kubernetes"
- **Event:** KubeCon NA 2026, Salt Lake City
- **Speakers:** Whitney Lee and Michael Forrester
- **Duration:** ~30 minutes (demo runs in ≤25, leaving ~5 for Q&A)
- **Thesis:** Platform-level governance (policy + runtime + gateway + OTel)
  beats per-developer discipline. The same app, deployed twice, behaves
  completely differently based on the platform it's deployed *on*.
- **Audience interaction:** Scan a QR code, submit prompts from their phones,
  watch the guarded vs unguarded side-by-side on a projector.
- **Narrative hook:** The Chipotle chatbot that helped a user reverse a
  linked list in Python while trying to order a bowl. It is funny when it is
  a burrito bot; it is terrifying when it has access to your deployment
  pipeline.
- **Canonical Act 1 prompt set (audience, lighthearted):** *teach me some
  salsa dance moves*, *how do I throw a hot dog party*, *recommend karaoke
  songs for a wedding*, *give me a disco routine for four people*. The
  audience submits these from their phones; the unguarded bot writes the
  choreography, the guarded bot politely redirects to the seasonal bowl.
  The harder cases — prompt injection, jailbreak, data extraction — are
  demonstrated by the speakers, not crowdsourced, because inviting a
  KubeCon audience to attack a live chatbot is the kind of fun that ends
  up in a legal review.
- **Metaphor:** The ogre-faced spider. Most spiders build a passive web and
  wait. This one holds a net between its front legs, watches with the
  largest eyes of any spider, and actively casts the net over anything that
  walks underneath. OTel + spinybacked-orbweaver are **The Eyes**. NeMo +
  LLM Guard + Envoy AI Gateway + Kyverno + Falco are **The Net** that the
  burritbot platform casts over every prompt. Two spiders, one architecture.

## 2. Architecture at a Glance

```
┌──────────────────────────── GKE Standard + NAP (us-west1) ─────────────┐
│                                                                         │
│   Namespaces                                                            │
│   ──────────                                                            │
│   argocd              monitoring         security                       │
│   burritbot-net        burritbot-unguarded  burritbot-guarded            │
│   audience                                                              │
│                                                                         │
│   UNGUARDED path (naked, no net):                                       │
│     audience-frontend ──► burritbot-unguarded ──► Vertex AI             │
│                                                                         │
│   GUARDED path (caught by the net):                                     │
│     audience-frontend                                                   │
│        └─► burritbot-guarded ──► Envoy AI Gateway  (burritbot-net)       │
│                                      └─► NeMo Guardrails (Colang)      │
│                                      └─► LLM Guard (scanners)          │
│                                      └─► Vertex AI (Gemini 3 Pro)      │
│                                                                         │
│   The Eyes (observability):                                             │
│     • OTel Collector with gen_ai.* semantic conventions                 │
│     • spinybacked-orbweaver (Whitney's auto-instrumentation agent)      │
│     • Prometheus + Grafana (3 dashboards for the demo)                  │
│                                                                         │
│   The Net (enforcement, cross-cutting):                                 │
│     • Kyverno (AI workload policies, sidecar enforcement, provenance)  │
│     • Falco (AI-workload runtime rules, shell detection, egress watch)│
│     • Envoy AI Gateway + NeMo + LLM Guard (in burritbot-net)            │
│                                                                         │
│   Supporting web:                                                       │
│     • External Secrets Operator ← GCP Secret Manager                    │
│     • cert-manager + Let's Encrypt                                      │
│     • ArgoCD app-of-apps with sync waves                                │
│     • Workload Identity Federation (no JSON key files)                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 3. Phase-by-Phase Plan

One Claude Code session per phase. Each session starts by reading
`CLAUDE.md`, `PROJECT_STATE.md`, and the relevant sections of
`BUILD-INSTRUCTIONS.md`. Each phase is TDD: write tests first, then make
them pass. Each phase ends with a staging commit and a staging→main merge
once tests are green.

| # | Phase | Budget | Key deliverables | Kubeauto reuse |
|---|-------|--------|------------------|----------------|
| 1 | GKE Foundation | 90 min | Terraform: VPC, GKE Standard + NAP, WIF, Secret Manager, namespaces (incl. `burritbot-net`) | Terraform *structure* only; rewrite all resources for GCP |
| 2 | GitOps Bootstrap | 60 min | ArgoCD install, app-of-apps root, sync wave plan | Reuse app-of-apps pattern, RBAC, sync-wave convention |
| 3 | The Eyes | 90 min | Prom + Grafana + OTel Collector with `gen_ai.*` processors; 3 dashboards (the-eyes-overview, prompt-response-traces, cast-net-comparison); spinybacked-orbweaver auto-instrumentation | Reuse OTel wiring skill and base values; extend with GenAI conventions |
| 4 | The Net — Security | 120 min | Kyverno AI policies (provenance, sidecar, OTel annotations — all with `burritbot.io/layer: the-net` labels), Falco AI-workload rules tagged `[burritbot, the-net, ...]`, network policies | Reuse disallow-privileged, require-labels, require-resource-limits, require-probes, default-deny; extend falco base rules |
| 5 | The Net — AI Gateway | 120 min | Envoy AI Gateway, NeMo Guardrails (Colang: burrito-only, jailbreak-detect, topic-enforcement, output-sanitize), LLM Guard (input+output scanners) | None — all new |
| 6 | BurritBot | 90 min | FastAPI app (Dockerfile, app.py **with `gemini-3-pro` via `google-genai`**, system prompt), unguarded + guarded deployments | None — all new |
| 7 | Audience Frontend | 60 min | Mobile web UI, QR code, WebSocket, FastAPI proxy, rate limiting (10 req/min/IP) | None — all new |
| 8 | Hardening | 60 min | RUNBOOK.md, `cast-net.sh` toggle, backup videos, COST.md, TEARDOWN.md | Reuse COST/TEARDOWN document *structure* |

**Total wall-clock budget:** ~11 hours of AI build time. Realistic real-world
spread: several working sessions plus full rehearsals in Phase 8.

## 4. Reuse Strategy

The kubeauto-ai-day tree lives on disk at
`~/repos/_archive/events/kubeauto-ai-day/`
(canonical public copy: https://github.com/peopleforrester/kubeauto-ai-day),
and is **gitignored** here. Every session that needs to reuse a file reads
it from that path directly.

See `KUBEAUTO-REUSE-MAP.md` for the per-file decision matrix (copy / adapt /
extend / ignore). Highlights:

- **Copy-with-rename to GKE / burritbot context:** `.claude/commands/build-phase.md`,
  `.claude/commands/validate-phase.md`, `.claude/skills/argocd-patterns.md`,
  `gitops/bootstrap/app-of-apps.yaml`, several Kyverno policies, the tests/
  helper structure.
- **Adapt (EKS → GKE substitution):** ArgoCD `values.yaml` (ALB → Gateway API),
  Falco install (must work on GKE Standard + NAP), External Secrets
  configuration (AWS SM → GCP SM).
- **Extend (base + AI-specific additions):** Kyverno policies (add AI sidecar,
  model provenance, OTel annotations, all tagged `burritbot.io/layer: the-net`),
  Falco rules (add AI workload rules with `[burritbot, the-net, ...]` tags),
  OTel collector (add GenAI semconv processors).
- **Do not reuse:** `infrastructure/terraform/*` (rewrite for GCP), Backstage,
  Crossplane, EKS addons, any AWS IAM / IRSA / ACM references.

## 5. Staging → Main Workflow (autonomous)

Per global rule:
1. Work on `staging`. Main is protected on the remote.
2. After each logical unit of work: `git add`, commit on staging, run tests,
   push staging, merge staging→main, push main. No confirmation requests.
3. Commit messages are professional and technical. No AI / Claude references.

**Bootstrap exception (Phase 0 only):** the very first commit creates `main`
from scratch because `staging` cannot exist without it. After the bootstrap,
`staging` becomes the working branch for all phases.

## 6. Critical Versions (pin, do not use latest)

Current GA versions pinned as of 2026-04-09:
- GKE: 1.33 Stable channel minimum (DRA support)
- Terraform `hashicorp/google` + `google-beta`: `~> 7.0` (current GA 7.27.0)
- ArgoCD: 3.3+ (helm chart 9.5.x)
- Kyverno: helm chart 3.7.1, app 1.17.x (CEL policies GA)
- Falco: 0.43.x binary, rules `required_engine_version: 0.57.0` (modern-bpf)
- OTel Collector: 0.149+ (GenAI semconv v1.37.0 with `gen_ai.provider.name`)
- OTel Weaver: 0.22+ (registry check, emit, live-check)
- OTel Python (`opentelemetry-api`/`sdk`): 1.41.0 (`-instrumentation-*`: 0.62b0)
- NeMo Guardrails: 0.11+
- LLM Guard: 0.3.17+
- Grafana: 11+
- spinybacked-orbweaver: latest (Whitney's agent)
- **Gemini model:** `gemini-3-pro` (GA) via `google-genai` 1.71.0 with
  `vertexai=True`. 1.5 is unsupported; 2.0 Flash is retired; 2.5 Flash/Pro
  retire 2026-10-16 — four weeks before the talk; 3 Flash is preview-tier.
  3 Pro is the only Vertex AI model guaranteed to be live on demo day.
  `google-cloud-aiplatform.vertexai.generative_models` is removed after
  2026-06-24; do not reintroduce it.

Every Phase-X session must verify the relevant version is still current
(GitHub releases + official docs) before writing chart values. The
kubeauto-ai-day `docs/VERSION-MAP.md` is a good cross-check for shared
components — but the deployed versions there drifted between build and talk,
so prefer live-check over stale map.

## 7. Resolved Defaults (placeholders, confirm before `terraform apply`)

| # | Decision | Default | Confirm by |
|---|----------|---------|------------|
| 1 | GCP project ID | `burritbot-kubecon-2026` | Phase 1 cluster bring-up |
| 2 | Region | `us-west1` (close to SLC) | Phase 1 cluster bring-up |
| 3 | GKE mode | **Standard + node auto-provisioning** (non-negotiable; Falco DaemonSets) | Locked |
| 4 | Gemini model | `gemini-3-pro` (GA) via `google-genai` | Phase 6 app deploy |
| 5 | Audience frontend backend | **FastAPI** (Python) | Phase 7 |
| 6 | Licensing | Apache 2.0 | Phase 0 (already chosen) |
| 7 | Demo domain / Cloud DNS | Undecided — default to raw Gateway IP | Phase 7 or 8 |
| 8 | GitHub repo visibility | Public at init | Flip to private only if something sensitive slips in |

## 8. Risk Register

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Falco cannot run on GKE Autopilot (DaemonSet / privileged restriction) | Resolved | Locked to GKE Standard + NAP in Phase 1 |
| OTel GenAI semantic conventions still shifting | Medium | Pin OTel Collector ≥0.149 (semconv v1.37.0) and verify the `gen_ai.provider.name` namespace on the day we write the config |
| spinybacked-orbweaver is a moving target | Medium | Pin the exact commit used for rehearsal; document in `observability/spinybacked-orbweaver/config.yaml` |
| Vertex AI rate limiting during audience interaction | Medium | Rate-limit the audience frontend at 10 req/min/IP; also pre-warm a small response cache |
| Conference WiFi unreliable | High | Pre-record backup videos for every demo segment in Phase 8; have a cellular hotspot on standby |
| Cluster left running between rehearsals | Medium | `cast-net.sh` for live toggle, `demo/teardown.sh` + nightly Terraform destroy reminder |
| Secrets accidentally committed | Low | gitleaks pre-commit hook (port from kubeauto-ai-day), plus .gitignore exclusions |
| Gemini model version drift between now and KubeCon | Medium | Pin `gemini-3-pro`; re-verify GA status and pricing in Phase 8 rehearsal week |

## 9. Cost Envelope (from spec)

- GKE Standard (~3×e2-standard-4): ~$0.30/hr
- Vertex AI Gemini 2.5 Flash: ~$0.01–0.05/hr demo traffic
- Cloud DNS: negligible
- **Total:** ~$0.35–0.40/hr running
- Demo day: ~$3; 40hr rehearsal over 2 months: ~$15

Rule: tear down between rehearsals. Terraform rebuild is ~15 min.

## 10. Success Criteria

The demo is a success when:
1. Unguarded BurritBot answers an audience prompt injection attempt *and*
   guarded BurritBot blocks the same attempt, both visible on the projector
   dashboard (`cast-net-comparison.json`).
2. Every block is traceable: NeMo decision, LLM Guard scan result, or
   Kyverno/Falco event shows up as a span or log event in Grafana. The Eyes
   saw the net fire.
3. The audience sees the block count climb in real time on the side-by-side
   dashboard during Act 2.
4. If the live demo catches fire, the backup videos cover every segment and
   the talk still lands on time.
5. `cast-net.sh` toggles the guardrails stack in under 10 seconds so the
   speaker can live-toggle between acts if the narrative calls for it.
