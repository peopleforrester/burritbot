# Phase 8: Hardening, Runbook, and Demo-Day Documentation

**Goal:** Everything the operator needs on stage — runbook, scorecard,
teardown script, rehearsal checklist, and the final honest
self-assessment before any given demo day. Talk-specific runbook /
scorecard artifacts live under `presentations/<event>/`.

**Inputs:** Phases 1-7 complete. All tests green. Live rehearsal has
been run at least once end-to-end.

**Outputs:**

- `presentations/<event>/docs/RUNBOOK.md` — must contain sections:
  - **Pre-flight** (cluster context, secret presence, Grafana board
    sanity check, Envoy route initial state)
  - **Act 1** (unguarded BurritBot rehearsal script, attack prompts,
    expected dangerous answers)
  - **Cast the Net** (the single command and what to watch on Grafana)
  - **Act 2** (guarded BurritBot rehearsal script, same attack prompts,
    expected refusals)
  - **Teardown** (how to take the cluster down after the talk)
  - **Rollback** (what to do if `cast-net.sh cast` fails on stage)
- `presentations/<event>/docs/SCORECARD.md` — must mention "CNCF Project", "Layer", and each
  of `The Eyes`, `The Net`, `The Web`; one row per component with
  honest notes
- `scripts/teardown.sh` — executable, two ABOUTME lines, calls
  `terraform destroy`
- Final PROJECT_STATE.md update marking Phase 8 complete

**Test Criteria (tests/test_phase_08_hardening.py):**

Static only — Phase 8 has no new live infrastructure:

- `test_runbook_exists_and_has_all_sections` — Pre-flight, Act 1,
  Act 2, Cast the Net, Teardown, Rollback
- `test_scorecard_exists_with_cncf_columns`
- `test_teardown_script_exists_and_is_executable` — `terraform
  destroy` appears in the script
- `test_all_shell_scripts_start_with_aboutme`
- `test_project_state_marked_complete`

**Key Technology Decisions:**

- Runbook lives in `docs/RUNBOOK.md`, not in a slide deck. It's
  versioned with the code because the audience will ask for it.
- Scorecard is honest: red cells on components that almost worked are
  more useful to the audience than green cells that lie.
- Teardown is `terraform destroy`, not `gcloud projects delete`. The
  project may be reused for the next event.

**Known Risk:** The scorecard will tempt you to mark everything green.
Resist. Write what happened in rehearsal.

**Completion Promise:** `<promise>PHASE8_DONE</promise>` and, if every
phase prior is also green, `<promise>BURRITBOT_COMPLETE</promise>`.

**Skill:** none — the runbook and scorecard are narrative artifacts
specific to the demo.

**Commits:** 2 expected (runbook + scorecard; teardown script + final
state update)
