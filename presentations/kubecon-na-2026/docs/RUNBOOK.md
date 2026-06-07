# burritbot Demo-Day Runbook

Operational runbook for running the burritbot demo live at KubeCon NA 2026.
Every section here is something Whitney or Michael should be able to run
without thinking — this is the "chess clock is ticking" document, not the
architecture doc.

---

## Pre-flight

Run this checklist T-60 minutes before the talk. Everything here is
**read-only** — nothing in this section modifies cluster state.

1. **Cluster reachable:**
   ```bash
   kubectl cluster-info
   kubectl get nodes
   ```
   Expect: all nodes `Ready`, no `NotReady` or `SchedulingDisabled`.

2. **All burritbot namespaces exist:**
   ```bash
   kubectl get ns argocd monitoring security burritbot-net \
     burritbot-unguarded burritbot-guarded audience
   ```
   Expect: 7 × `Active`.

3. **ArgoCD root app is `Synced` + `Healthy`:**
   ```bash
   kubectl -n argocd get applications root \
     -o jsonpath='{.status.sync.status}/{.status.health.status}'
   ```
   Expect: `Synced/Healthy`. Anything else → go to **Rollback**.

4. **Guarded path pods alive:**
   ```bash
   kubectl -n burritbot-net get pods -l app.kubernetes.io/part-of=burritbot
   kubectl -n burritbot-guarded get pods
   kubectl -n burritbot-unguarded get pods
   ```
   Expect: all `Running` + `1/1 Ready`.

5. **Kyverno + Falco operational:**
   ```bash
   kubectl -n security get pods -l app.kubernetes.io/component=admission-controller
   kubectl -n security get ds falco
   ```
   Expect: admission-controller `Running`; Falco DaemonSet
   `desired == ready`.

6. **Observability dashboards load:**
   Open Grafana. Verify the three burritbot dashboards render with live
   data: `The Eyes — Overview`, `BurritBot Prompt / Response Traces`,
   `Cast the Net — Before / After Comparison`.

7. **Traffic starts in the unguarded position:**
   ```bash
   ./scripts/cast-net.sh status
   ```
   Expect: `BURRITBOT_TARGET=burritbot-unguarded`. If not, run
   `./scripts/cast-net.sh recall`.

8. **Audience URL reachable from phones:**
   Hit the audience frontend URL from the venue Wi-Fi before the lights
   come down. The venue NAT often breaks things that passed in rehearsal.

---

## Act 1 — The Unguarded Demo

Chipotle incident narration. Audience sees a wide-open BurritBot.

1. Confirm traffic is pointed at the unguarded target:
   ```bash
   ./scripts/cast-net.sh status
   ```

2. Narrate the Chipotle chatbot incident. Invite the audience to try to
   jailbreak BurritBot live. Expected audience behaviour: prompt-injection
   attempts, off-topic questions, attempts to exfiltrate the system prompt.

3. While the audience plays: pull up the `Cast the Net — Before / After`
   dashboard on the shared screen. The left panel will start lighting up
   red as unguarded BurritBot leaks.

4. **Hard rule: never let Act 1 run longer than five minutes.** The demo
   joke is funnier than a broken chatbot at minute six. Move on.

---

## Cast the Net

The central reveal. One command, under 500ms on a warm cluster.

1. From the demo laptop shell:
   ```bash
   ./scripts/cast-net.sh cast
   ```
   This patches the `BURRITBOT_TARGET` env var on the audience-frontend
   Deployment to `burritbot-guarded`. ArgoCD will not race the patch
   because `cast-net.sh` uses `kubectl patch --type=json` (never `apply`).

2. Immediately re-run status to confirm:
   ```bash
   ./scripts/cast-net.sh status
   ```
   Expect: `BURRITBOT_TARGET=burritbot-guarded`.

3. Flip the shared screen back to the Grafana `Cast the Net` dashboard.
   The block-rate panel should start climbing within seconds as the
   audience's leftover attacks now hit The Net.

---

## Act 2 — The Guarded Demo

Same audience, same prompts — The Net catches the problems.

1. Invite the audience to try the exact same prompts from Act 1. Point
   out the block events appearing on the dashboard in real time.

2. Walk through the layers as each one catches something:
   - **The Eyes**: OTel Collector decorates every call with `gen_ai.*`
     attributes — you can see them in the trace table.
   - **The Net**: NeMo Colang rails refuse off-topic and jailbreak
     attempts. The content scanners block prompt-injection and sanitize
     model replies. Kyverno enforces burritbot.io labels on every guarded
     pod. Falco alerts on any shell that escapes.
   - **The Web**: ArgoCD sync status, Gateway API routes, SPIFFE
     identities — the platform scaffolding holding the live demo up.

3. Close the act with the scorecard: pull up `docs/SCORECARD.md` in the
   browser, talk through what's real vs. aspirational. Do not green-wash.

---

## Teardown

Post-talk cleanup. Not time-pressured — do it back at the hotel.

1. Recall traffic and stop any in-flight probes:
   ```bash
   ./scripts/cast-net.sh recall
   ```

2. Drain the cluster gracefully. Scale ArgoCD down first so it does not
   try to re-sync deleted resources mid-teardown:
   ```bash
   kubectl -n argocd scale deploy argocd-application-controller --replicas=0
   kubectl -n argocd scale deploy argocd-applicationset-controller --replicas=0
   ```

3. Run the teardown script (destroys Terraform-managed infra):
   ```bash
   ./scripts/teardown.sh
   ```

4. Verify no lingering GCP resources. The script prints a final
   `gcloud container clusters list` and `gcloud compute networks list`
   for a visual sanity check. Spot-check in the GCP console.

5. Revoke demo-day credentials: rotate the Vertex Secret Manager entry
   and the audience-frontend public URL.

---

## Rollback

Use this if the pre-flight checklist fails or if the cluster looks wrong
mid-demo. **Rollback is preferred over debugging live.**

1. **ArgoCD OutOfSync or Degraded:**
   ```bash
   kubectl -n argocd get applications
   kubectl -n argocd describe application root
   argocd app sync root --force
   ```
   If still broken: re-apply the bootstrap manifest by hand:
   ```bash
   kubectl apply -f gitops/bootstrap/app-of-apps.yaml
   ```

2. **BurritBot pods crash-looping:**
   ```bash
   kubectl -n burritbot-guarded rollout undo deploy/burritbot
   kubectl -n burritbot-unguarded rollout undo deploy/burritbot
   ```

3. **Cast the Net misfires (toggle stuck):**
   ```bash
   ./scripts/cast-net.sh recall
   # If that still fails, patch by hand:
   kubectl -n audience set env deploy/audience-frontend BURRITBOT_TARGET=burritbot-unguarded
   ```

4. **Full reset:** rerun the Phase 2 bootstrap from a clean state — see
   `spec/phases/phase-02-gitops.md`. Only do this if the talk is not live.

5. **Worst case:** swap to the static screenshots deck in
   `docs/fallback-deck/`. The audience came for the story, not the
   cluster.
