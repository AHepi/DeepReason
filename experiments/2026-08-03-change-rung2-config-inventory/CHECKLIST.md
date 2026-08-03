# Checklist for: rung 2, tranche 1 — buried choices become visible switches (inventory)
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids scoped (per dr-plan-steps 4b): `DR-INV-frozen-surfaces` (consulted:
"Where authority is allowed to live instead"), `DR-CON-authority`,
`DR-CON-schools`, `DR-CON-conjecture-source`, `DR-CON-criticism-source`,
`DR-CON-scheduler-ranking` (all five rung-1 socket documents, read as the
cross-check baseline). No seam document is created or edited — this
tranche writes zero `docs/map/` content (S1's deliverable is an
`experiments/` inventory). No root sweep step: this tranche touches no
`src/` file (S2), so the sweep has nothing to compare and is not run.

- [ ] 1. (S1) Read `src/deepreason/v6_policy.py`, `src/deepreason/runtime/launch_policy.py`,
      and `src/deepreason/capabilities/policy.py` in full. For each, list
      every hard-coded literal that gates a behavior choice (mode, policy
      value, feature toggle) as opposed to structural/identity data,
      noting exact `file:line` and current value.
      done-when: a working list exists (in the step's execution record)
      naming at least `engaged_criticism_policy`'s
      `authority="observe_only"` (v6_policy.py) with its exact line
      number, plus every other candidate found in the same three files.
- [ ] 2. (S1) Read `src/deepreason/config.py` in full to establish the
      baseline (confirm which candidates from step 1 are ALREADY Config
      fields, so they are excluded, and confirm the
      `ARGUMENTATIVE_AUTHORITY`-shaped precedent's exact field names).
      done-when: the four existing authority-shaped Config fields
      (`ARGUMENTATIVE_AUTHORITY`, `TEXT_RUBRIC_AUTHORITY`,
      `PAIRWISE_AUTHORITY`, `INFRASTRUCTURE_REVIEW_AUTHORITY`) are
      confirmed present in `config.py` by grep, and none of step 1's
      candidates duplicate an existing field name.
- [ ] 3. (S1) Cross-check rung 1's five socket areas (`capture/schools.py`,
      `rules/conj.py`, `rules/crit.py`, `scheduler/scheduler.py`'s ranking,
      `authority.py`) against their already-written
      `docs/map/CON-*.md`/`SUB-*.md` documents for any hard-coded literal
      not already a named `Config` field.
      done-when: a working list of any additional candidates found this
      way (or an explicit "none beyond what rung 1's own documents already
      show as Config-backed" if the sweep finds nothing new).
- [ ] 4. (S1) Write `experiments/2026-08-03-change-rung2-config-inventory/INVENTORY.md`
      with the findings from steps 1-3, one table per logical group
      (candidate / file:symbol pointer / current hard-coded value / note),
      per SPEC.md's A2 format.
      done-when: `test -f experiments/2026-08-03-change-rung2-config-inventory/INVENTORY.md`
      exits 0 AND `grep -q 'observe_only' experiments/2026-08-03-change-rung2-config-inventory/INVENTORY.md`
      (the known, named candidate is present) AND every candidate row's
      file:symbol pointer is spot-checked against the real file (paste at
      least 3 spot-checks).
- [ ] 5. (S1) [COMMIT] Commit step 4, push with retry (2s/4s/8s/16s).
      done-when: new commit on branch AND clean tree.
- [ ] 6. (S2, R3) Scope-boundary proof: confirm zero `src/` changes across
      the whole tranche.
      done-when: `git diff --stat <tranche-base-sha>..HEAD -- src/` prints
      nothing (paste the empty result and the base sha it was measured
      against).
- [ ] 7. (S3, R4) [COMMIT] Final push and cleanliness check.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD` equals `git rev-parse origin/claude/delivery-rungs-handover-m22sdy`.
      Note for DELIVERY.md: this tranche STOPS here per R4 — present the
      inventory, do not open tranche 2 (the `engaged_criticism_policy`
      switch) or any further rung in this tranche.
