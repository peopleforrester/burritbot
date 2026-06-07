# Phase G — Genericize the burritbot Platform
# Strip KubeCon NA 2026 framing so the platform can be re-presented at
# AgentCon, future KubeCons, or any other event without confusion.

## Verification Method
A new static test (Phase G5) scans the entire tree for case-insensitive
"kubecon" and fails the suite if it appears outside the talk-specific
subfolder. Lets future cleanup spot regressions automatically — no
trusting "scrubbed" claims that aren't re-checked.

## Why this exists
The repo today is framed end-to-end as a KubeCon NA 2026 demo platform.
Mentioning a specific event in the platform code / docs creates two
problems: (1) it ages out the moment the talk is done; (2) re-using
the same platform at another con (AgentCon was named) creates "is this
the KubeCon version or the new version?" confusion in audience-facing
material.

Resolution per Michael: move event-specific talk artifacts into a
clearly-scoped subfolder, scrub the rest of the tree to be event-neutral.

## Subfolder choice
`presentations/kubecon-na-2026/` — extensible (`presentations/agentcon-2026/`
later), self-explanatory, doesn't collide with the `~/repos/events/`
parent on disk.

## Triage

### MOVE — pure talk artifacts (live in `presentations/kubecon-na-2026/`)
- `docs/CFP-SUBMISSION.md` — KubeCon NA CFP text
- `docs/RUNBOOK.md` — Pre-flight / Act 1 / Cast the Net / Act 2 / Teardown
- `docs/SCORECARD.md` — talk-day per-component status
- `docs/PLAN.md` — Talk Framing section + KubeCon execution plan
- `docs/BUILD-INSTRUCTIONS.md` — talk build spec
- `spec/SCORECARD.md` — talk success metrics skeleton

### SCRUB in place — platform files that just mention KubeCon as context
- `README.md`, `CLAUDE.md`, `PROJECT_STATE.md`, `pyproject.toml` — must
  live at repo root by convention; rewrite to be platform-generic
- `.gitignore`, `tests/conftest.py`, `tests/test_phase_06_burritbot.py`,
  `tests/test_phase_08_hardening.py` — tests/configs in place
- `apps/burritbot/app.py`, `ai-gateway/llm-guard/config.yaml`,
  `scripts/teardown.sh`, `chatbot-research/*` — code/scripts in place
- `docs/KUBEAUTO-REUSE-MAP.md`, `docs/PHASE-B-EKS-ADAPT-PLAN.md` — platform docs
- `spec/phases/phase-{01,02,08}-*.md` — phase specs in place
- `.claude/skills/*.md`, `.claude/commands/burritbot-validate.md` — Claude
  Code reads from `.claude/`; locations cannot move

### LEAVE — false positives or out-of-scope
- GCP project ID placeholder `burritbot-kubecon-2026` (placeholder, not a
  KubeCon ref in the doc sense — different concept)
- `kubeauto-ai-day` references (upstream EKS repo name, "kubeauto" is
  "kubernetes automation", not "KubeCon")
- Parent directory name `Kubecon-NA-2026-Whitney-BurritoBot/` (cannot
  rename without breaking the workspace; not in-repo content)

## Phase order

### G1 — Move talk artifacts
Create `presentations/kubecon-na-2026/{docs,spec}/`. Move the 6 files.
Update every reference: `tests/test_phase_08_hardening.py`,
`README.md`, `CLAUDE.md`, `PROJECT_STATE.md`, and any other doc that
points at the moved paths. Static suite must stay green.

### G2 — Scrub KubeCon refs from platform files
For each SCRUB-bucket file, replace dated mentions:
- "KubeCon NA 2026" → "the demo event" / drop entirely
- "Salt Lake City" → drop or replace with generic "demo venue"
- "before the talk" → "before demo day" / drop
- Talk-day dates (Nov 2026) → keep where they describe Gemini model
  retirement reality, recast where they're just talk dates
Leave GCP project ID and kubeauto-ai-day refs alone.

### G3 — Rewrite README and CLAUDE.md generic
- README.md: position burritbot as a reusable AI-guardrails-on-K8s
  demo platform. Add "Talks using this platform" section pointing at
  `presentations/`.
- CLAUDE.md: drop "KubeCon NA 2026" from the title and "What This Is"
  sections; reframe phase 7 / 8 narrative as event-neutral; pointer
  to `presentations/` for the run-of-show.
- PROJECT_STATE.md: same — drop event-specific Talk Context block,
  replace with a one-liner about the presentations folder.

### G4 — Update GitHub repo description
`gh repo edit --description "..."` — drop "KubeCon NA 2026" from the
About text. New description: roughly "burritbot — a reusable AI
guardrails demo platform for Kubernetes (NeMo + LLM Guard + Envoy AI
Gateway + Kyverno + Falco on GKE)."

### G5 — Add KubeCon-leak test
`tests/test_no_kubecon_outside_talk_folder.py`: case-insensitive
"kubecon" scan over every file in the tree; allowlist GCP project ID
placeholder + the kubeauto-ai-day external repo name + the
presentations/kubecon-na-2026/ subtree. Fails the suite on regression.

## Commit Strategy
- One commit per phase. Run full static suite before each commit.
- Test count increases by 1 in G5; refresh PROJECT_STATE.md count.
- After G5, push staging → main per the project's autonomous flow.

## Exit Conditions
- Pure talk artifacts live in `presentations/kubecon-na-2026/`.
- `grep -ri kubecon` (excluding the allowlist) returns nothing.
- All 141 existing tests still pass + 1 new G5 test = 142 static green.
- README + CLAUDE.md + GitHub description read as a reusable platform.
- PROJECT_STATE.md refreshed to match.
