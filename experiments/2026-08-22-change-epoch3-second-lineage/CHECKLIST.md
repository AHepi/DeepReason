# Checklist for: "reach epoch 3 — put a SECOND problem lineage in the root, then launch"
State: next=11 blockers=none
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids this plan was scoped from (SPEC.md header): DR-SUB-amendment,
DR-SUB-application, DR-SUB-workloads, DR-SUB-measures, DR-CON-run-identity,
DR-INV-frozen-surfaces. No `SEAM-amendment-x-application.md` exists; the two
subsystem documents were read in its place and the gap is PARKED (P3-epoch3),
not created here — writing a map document is not in this tranche's scope
(C1 confines the tree to `experiments/`).

No `src/` or `tests/` step appears anywhere in this plan. That is C1, and
step 14 proves it.

- [x] 1. (S4) Fix the P8-reach ladder invocation: in
      `experiments/2026-08-22-live-reach-rich-run/reach_run.sh` line 101,
      replace `python -m deepreason --root "$ROOT" results` with
      `python -m deepreason results "$ROOT"`.
      done-when: `grep -c -- '--root "$ROOT" results'
      experiments/2026-08-22-live-reach-rich-run/reach_run.sh` -> `0`
      AND `grep -c 'deepreason results "$ROOT"'` -> `1`
      AND `bash -n experiments/2026-08-22-live-reach-rich-run/reach_run.sh`
      -> rc=0

- [x] 2. (S4) [COMMIT] Prove the corrected invocation answers, against the
      retired epoch-2 root, and commit the one-line fix.
      done-when: `python -m deepreason results
      experiments/2026-08-22-live-reach-rich-run/run` prints a summary whose
      state is `failed`, stop_reason `operational_failure`, violations 0
      (pasted) — NOT `RESULTS_ROOT_NOT_FOUND`.

- [x] 3. (S1) Write `build_manifest_epoch3.py`: import `QUESTION`,
      `CRITERIA`, `CONFIG_PATH`, `COMPILED_AT` from the reach-rich
      `build_manifest.py` unchanged, and compile with the baseline inquiry
      capability policy `model_copy`d to carry
      `engaged_attached_evidence_policy(attached=True)`.
      done-when: `python build_manifest_epoch3.py <scratch-root>` prints
      `"manifest_sha256": "bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4"`
      and `"compile_notices": []` (pasted).

- [x] 4. (S1) Prove the epoch-3 manifest differs from the reach-rich one in
      exactly the five `attached_evidence` fields and nothing else.
      done-when: a behavior-payload diff (manifest dump minus `compiled_at`
      and `run_input_digest`) lists exactly the five
      `/inquiry_capability_policy/attached_evidence/*` lines of SPEC.md M8
      and no other line (pasted).

- [x] 5. (S1) [COMMIT] Prove the epoch-3 root's seeded problem still carries
      the three subject predicates, by running the reach-rich tranche's OWN
      `preflight_seed.py` against the epoch-3 scratch root (no new code).
      done-when: `python
      experiments/2026-08-22-live-reach-rich-run/preflight_seed.py
      <scratch-root>` exits 0 and reports all three predicates evaluable,
      each PASSing an on-subject answer and FAILing an off-subject one
      (pasted).

- [x] 6. (S2) Write `supplement-nocturnal-collapse.md`, the source the
      amendment attaches to the second lineage.
      done-when: the file exists, is non-empty, and is under 8 KiB
      (`wc -c` pasted; the manifest's frozen authority is 8 MiB total, so
      this is far inside it).

- [x] 7. (S2) [COMMIT] Write `preflight_supplement.py` and run it: the
      supplement's OWN bytes must FAIL at least one of the three subject
      predicates, so a later reach hit cannot be attributed to the model
      copying the attached document.
      done-when: `python preflight_supplement.py` exits 0 and prints a
      per-predicate verdict line for the supplement in which at least one
      verdict is FAIL (pasted). If all three PASS the step FAILS and the
      supplement is rewritten before proceeding.

- [x] 8. (S3) Write `epoch3_run.sh`: setup -> preflights -> qualify ->
      phase 1 `run --budget cycles=12 --token-budget 200000` -> assert the
      phase-1 stop reason is resumable -> `amend --attach <supplement>
      --reshape-question <sibling question>` -> phase 2 `continue --budget
      cycles=12 --token-budget 200000` -> audit -> census.
      done-when: `bash -n epoch3_run.sh` -> rc=0, and the file contains
      `deepreason results "$ROOT"` (the P8-correct form), `PHASE1_CYCLES=12`,
      `PHASE2_CYCLES=12`, and the two token budgets summing to 400000
      (grep output pasted).

- [x] 9. (S3) `chmod +x epoch3_run.sh` and confirm the executable bit.
      done-when: `test -x epoch3_run.sh` -> rc=0.

- [x] 10. (S3) [COMMIT] DRY_RUN the ladder end-to-end offline: setup,
      both preflights, and the audit invocation must all run and the script
      must stop before `qualify` without a provider call.
      done-when: `DRY_RUN=1 ./epoch3_run.sh` exits 0, its driver log shows
      `SETUP OK rc=0`, `PREFLIGHT OK rc=0`, `SUPPLEMENT PREFLIGHT OK rc=0`
      and `DRY RUN: stopping before qualify`, and no `run-status.json` was
      created (pasted).

- [ ] 11. (S5) [COMMIT] Write `PREREG_EPOCH3.md`, frozen before any
      provider call: hypothesis, vehicle with its M-number warrant, the
      two-phase budget, deviations D1/D2 as predictions, and the typed
      judgement table naming SUCCESS / UNSUPPORTED / PRECONDITION-BLOCKED /
      TRUNCATED-BEFORE-CARRIER plus the P5 rulings' `E0` and
      `coverage == 0.5` vocabulary.
      done-when: the file exists and `grep -c` finds each of
      `TRUNCATED-BEFORE-CARRIER`, `E0`, `coverage`, `M7`, `M9` >= 1
      (pasted).

- [ ] 12. (S6) Prove the tree is untouched outside `experiments/`.
      done-when: `git diff --stat origin/main -- src/ tests/` prints
      nothing (pasted), and `git diff --stat origin/main --stat | tail -1`
      shows only `experiments/` paths.

- [ ] 13. (S6) Map check — required because the tranche is being committed,
      even though no map document moved.
      done-when: `python tools/docs_verify.py` reports 0 failed (pasted).

- [ ] 14. (S6) [COMMIT] No gate is owed for an untouched `src/`/`tests/`
      tree (PREREG.md §5's standing rule, restated in SPEC.md S6); record
      that explicitly rather than silently skipping it, and push.
      done-when: step 12's empty diff is quoted in the commit message, and
      `git status --porcelain` is empty with the branch head on origin.

- [ ] 15. (S7, R4, QO1) LAUNCH STOP. Report to the operator: the vehicle,
      the two deviations D1/D2, the priced fork QO1, and the request for the
      `env` file carrying `OLLAMA_API_KEY` at
      `experiments/2026-08-22-change-epoch3-second-lineage/env`.
      done-when: the operator supplies the credential (or answers QO1).
      NOTHING past this step runs without it — the ladder's own first guard
      exits rc=1 on a missing `env`.

- [ ] 16. (S7) Launch detached and arm the monitors.
      done-when: `setsid nohup ./epoch3_run.sh & disown` from the tranche
      directory returns immediately, the snapshot loop is running against
      the driver, and a monitor is watching the newest root's
      `progress.jsonl` plus the driver log's `rc=` lines.

- [ ] 17. (S8, R10) Judge on typed outcomes only: run state, stop_reason,
      `verify_root`, and the committed census tooling's `reach_set` count.
      done-when: `verify_root.json`, `results.txt`, `findings.json` and
      `reach-census.json` all exist for the epoch-3 root and are committed.

- [ ] 18. (S8, R11) If `reach_set == 0`: one repeat is pre-authorised.
      Retire the root by rename, COMMIT THE RENAME FIRST, relaunch.
      done-when: either a second root exists and was judged the same way, or
      the first attempt recorded `reach_set > 0` and no repeat was needed.

- [ ] 19. (S8, R12, R13) [COMMIT] Write the honest-ledger `RESULTS.md`
      segment: typed terminal, violations, `reach_set` count, any `E0` or
      `coverage == 0.5` event reported under the P5 rulings, and the
      residue. Zero on both attempts -> verdict recorded, both roots
      committed, STOP.
      done-when: `RESULTS.md` exists with a dated segment naming the run
      id(s) and a "Residue" paragraph.

- [ ] 20. (all) [COMMIT] `dr-validate-change` then `dr-deliver-change`:
      VALIDATION.md against every S-item accept, then DELIVERY.md's
      requirement-by-requirement reconciliation.
      done-when: VALIDATION.md verdict line is PASS and DELIVERY.md carries
      an R1-R15 table with no unaddressed row.

---

## Step outputs (pasted; the audit trail)

### Step 1 (S4) — P8-reach ladder invocation fixed

    $ grep -c -- '--root "$ROOT" results' experiments/2026-08-22-live-reach-rich-run/reach_run.sh
    0
    $ grep -c 'deepreason results "$ROOT"' experiments/2026-08-22-live-reach-rich-run/reach_run.sh
    1
    $ bash -n experiments/2026-08-22-live-reach-rich-run/reach_run.sh
    rc=0
    reach_run.sh:101  python -m deepreason results "$ROOT" > "$HERE/results.txt" 2>&1 || true

### Step 2 (S4) — the corrected invocation answers, against the retired root

    $ python -m deepreason results experiments/2026-08-22-live-reach-rich-run/run
    # Results for .../experiments/2026-08-22-live-reach-rich-run/run
      (resolved from a root)
    ## Run
      run id: 40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c
      state: failed
      stop_reason: operational_failure
      cycles completed: 2
      tokens spent vs budget: 0 / 400000
    ## Artifacts
      accepted / refuted / suspended: 55 / 1 / 0

Not `RESULTS_ROOT_NOT_FOUND`. The committed `epoch1-results.txt` of the
reach-rich tranche is left exactly as it was: it is that tranche's honest
record of what its ladder captured, and rewriting it would erase the
evidence for P8-reach.

### Step 3 (S1) — the epoch-3 manifest builder compiles clean

    $ python build_manifest_epoch3.py <scratch-root>
    {
      "attached_evidence_enabled": true,
      "compile_notices": [],
      "criteria": ["uhi-energy-balance@v1", "uhi-nocturnal-release@v1",
                   "uhi-cross-city-modulator@v1"],
      "evidence_dossier_digest": "9250d2a65525d09b209b60c348207b948a585f5b878eb1652ba9b68e6abaef95",
      "manifest_sha256": "bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4",
      "problem_id": "question-4dd62735b90864a75220e09b302500bc",
      "run_input_digest": "84832aad24a47c15da7127c5588c37d7efc4ee8d246f2c441d48f780720fcae6"
    }

Two things were learned writing it, both corrected in SPEC.md M7 rather
than absorbed: the baseline inquiry policy cannot be hand-assembled
(`disabled simulation capability must have zero bounds`), so the builder
compiles once without one and reads the derived policy back; and the
manifest sha first measured in M7 came from a throwaway dossier provenance
string, so the committed builder's honest `supplied_by` moves the
`run_input_digest` and the sha. `qualification.py:265-266` drops
`run_input_digest` from the subject payload, so step 4 is unaffected.

### Step 4 (S1) — exactly the five attached_evidence fields moved

    $ # manifest dump minus compiled_at and run_input_digest, reach-rich vs epoch-3
    DIFF /inquiry_capability_policy/attached_evidence/enabled :: False -> True
    DIFF /inquiry_capability_policy/attached_evidence/maximum_excerpt_bytes_per_source :: 0 -> 262144
    DIFF /inquiry_capability_policy/attached_evidence/maximum_sources :: 0 -> 16
    DIFF /inquiry_capability_policy/attached_evidence/maximum_sources_per_pack :: 0 -> 8
    DIFF /inquiry_capability_policy/attached_evidence/maximum_total_bytes :: 0 -> 8388608
    behavior payloads identical: False

No other line. The qualification subject therefore moves for exactly the
reason SPEC.md M8 predicted and for no other.

### Step 5 (S1) — the three subject predicates still reach the seeded problem

    $ python experiments/2026-08-22-live-reach-rich-run/preflight_seed.py <epoch-3 root>
    reasoning-envelope-wf       evaluable=True  on=fail  off=fail  discriminates=False
    uhi-energy-balance@v1       evaluable=True  on=pass  off=fail  discriminates=True
    uhi-nocturnal-release@v1    evaluable=True  on=pass  off=fail  discriminates=True
    uhi-cross-city-modulator@v1 evaluable=True  on=pass  off=fail  discriminates=True
    seeded criteria: ['reasoning-envelope-wf', 'uhi-energy-balance@v1',
                      'uhi-nocturnal-release@v1', 'uhi-cross-city-modulator@v1']
    rc=0

Run with the reach-rich tranche's OWN script, no new code. It writes its
report into its own tranche directory; `git status --porcelain
experiments/2026-08-22-live-reach-rich-run/` is EMPTY afterwards, so the
regenerated `preflight_seed.json` is byte-identical and no committed
artifact of that tranche moved. The epoch-3 ladder re-checks that after
every invocation (step 8).

### Step 6 (S2) — the amendment's attached source

    $ wc -c supplement-nocturnal-collapse.md
    1656

Field-campaign notes: instrumentation, transect geometry, timing window,
reference pairing, weather screening, rejection rules, scope. Deliberately
procedural — it records contrasts and the conditions they were measured
under, and proposes no mechanism.

### Step 7 (S2) — the control holds: the attachment passes NONE of the three

    $ python preflight_supplement.py
    uhi-energy-balance@v1            evaluable=True  verdict=fail
    uhi-nocturnal-release@v1         evaluable=True  verdict=fail
    uhi-cross-city-modulator@v1      evaluable=True  verdict=fail
    supplement: .../supplement-nocturnal-collapse.md (1656 bytes)
    passing the seed's subject predicates: none
    control holds (not all three pass): True
    rc=0

The step required at least one FAIL; all three fail. So no lineage-2
artifact can clear the seed problem's battery by quoting the attachment —
any reach hit has to come from the model's own account.

### Step 8-9 (S3) — the two-phase ladder

    $ bash -n epoch3_run.sh                        -> rc=0
    $ test -x epoch3_run.sh                        -> rc=0
    $ grep -c 'deepreason results "$ROOT"' epoch3_run.sh
    2                                              (phase-1 audit + final audit)
    27:PHASE1_CYCLES="${PHASE1_CYCLES:-12}"
    28:PHASE1_TOKENS="${PHASE1_TOKENS:-200000}"
    29:PHASE2_CYCLES="${PHASE2_CYCLES:-12}"
    30:PHASE2_TOKENS="${PHASE2_TOKENS:-200000}"

12 + 12 = 24 cycles and 200 000 + 200 000 = 400 000 tokens: PREREG's frozen
bound SPLIT across the phases, not added to (R9).

The ladder refuses to amend unless phase 1's `run-stop.json` reason is
`converged` or `budget_exhausted`, and says so in the driver log instead of
issuing an amendment `continue` could never accept.

### Step 10 (S3) — DRY_RUN passes end to end, offline

    $ DRY_RUN=1 ./epoch3_run.sh    -> rc=0
    [.] SETUP OK rc=0
    [.] PREFLIGHT OK rc=0
    [.] SUPPLEMENT PREFLIGHT OK rc=0
    [.] DRY RUN: stopping before qualify -- no provider call made,
        rehearsal root removed, rc=0
    leftovers: (none)
    git status --porcelain experiments/2026-08-22-live-reach-rich-run/: []

One defect was found and fixed inside this step: the first rehearsal bound
its manifest at `$HERE/run`, the exact path the live launch claims, so the
rehearsal would have made the launch refuse with the leftover-root guard. A
dry run now binds at `$HERE/.dry-run-root` and removes it on the way out.
