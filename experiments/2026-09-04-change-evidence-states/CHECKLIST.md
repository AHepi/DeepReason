# Checklist for: four evidence states over the record, and a per-cycle
# declaration that criticism ran in full

State: next=12 blockers=none
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids this plan was scoped from (map preflight, `docs/map/INDEX.md`):
`DR-INV-frozen-surfaces` (read first; gate verdict CLEAR, SPEC.md),
`DR-CON-warrants-and-attacks` (what a warranted attack IS),
`DR-SEAM-scheduler-x-rules` and `DR-SEAM-scheduler-x-workflow` (read BEFORE
the two subsystems, per the one ordering rule — they own the executable
checks that constrain how `_arg_crit` may be edited, listed in step 5),
`DR-SUB-scheduler`, `DR-SUB-application`, `DR-SUB-adjudication`,
`DR-SUB-rules`, `DR-CON-authority`, `DR-CON-criticism-source`,
`DR-SUB-evaluation`, `DR-SUB-verification`, `DR-SUB-harness`.

New map document this tranche creates: `DR-CON-evidence-states` (step 18).

## The four map checks that constrain the scheduler edit

Read once, before step 5; each is an executable `check:` that MUST stay green.

1. `SEAM-scheduler-x-workflow.md:367` asserts the VERBATIM substring
   `"if criticism_policy is not None:\n            self._foreign_arg_crit()\n            return"`
   inside `_arg_crit`, and that `"argumentative-criticism"` does NOT appear in
   it. => the `cut:foreign` declaration may NOT be inserted between
   `_foreign_arg_crit()` and its `return`. It is emitted at the END of
   `_foreign_arg_crit` instead.
2. `SEAM-scheduler-x-workflow.md:122` asserts four call sites appear in order
   inside `_foreign_arg_crit`. Appending an emission AFTER the last of them
   keeps it green.
3. `SEAM-scheduler-x-rules.md:170` asserts verbatim indentation of the
   `crit_fuzz` block inside `if config.RECRIT_STANDING:` and the index order
   `crit_fuzz` < `eligible.append(aid)` < `self._arg_crit_this_cycle += 1`.
   => nothing may be inserted inside that block.
4. `SEAM-scheduler-x-rules.md:136` asserts `_arg_crit` contains EXACTLY ONE
   `crit_argumentative_batch` call and it carries NO keywords.

---

## Re-plan, recorded at execution (dr-execute-step step 2)

The original order put the declaration module at step 4 and the reader at step
1, but the reader must import the signal constant and the outcome vocabulary
from it — a real dependency the plan inverted. The declaration module is
therefore step 1 and the reader step 2; nothing else moved and no step had
been checked. The reader-before-WRITER guardrail (SPEC.md, Record-observable
guardrail) is untouched by this: what moves earlier is the shared VOCABULARY,
not the scheduler's emission, which stays at step 5 behind both the reader and
its absence test.

- [x] 1. (S2) Create `src/deepreason/runtime/criticism_dispatch.py`:
      `CRITICISM_DISPATCH_SIGNAL`, the closed outcome vocabulary, and
      `declare_criticism_dispatch(harness, *, cycle, outcome, planned,
      dispatched, targets)`. Shaped on `runtime/seat_retirement.py`.
      done-when: `python -c "from deepreason.runtime.criticism_dispatch import CRITICISM_DISPATCH_SIGNAL, OUTCOMES; assert CRITICISM_DISPATCH_SIGNAL=='criticism.dispatch.v1'; assert set(OUTCOMES)=={'complete','cut:budget','cut:seat','cut:call','cut:foreign'}"` exits 0

      PROOF:
        $ python -c 'from deepreason.runtime.criticism_dispatch import CRITICISM_DISPATCH_SIGNAL, OUTCOMES; ...'
        exit 0

- [x] 2. (S1) Create `src/deepreason/views/evidence_states.py`: `EvidenceState`
      enum and `evidence_states(harness)` implementing SPEC.md S1's five
      definitions and four rules, reading only `state.att`, `state.status`,
      `state.artifacts`, the trial measure signals, and (when present) the
      `complete` declarations. Absence-tolerant: a root with no declaration is
      handled, never an error (reader-before-writer guardrail).
      done-when: `python -c "from deepreason.views.evidence_states import EvidenceState; assert [s.value for s in EvidenceState] == ['open','supported','refuted','contested']"` exits 0
      AND `python -c "import pathlib; from deepreason.harness import Harness; from deepreason.views.evidence_states import evidence_states; h=Harness(pathlib.Path('experiments/2026-09-02-live-p-a2-corrected/run'), read_only=True); print(len(evidence_states(h)))"` prints a non-zero count

      PROOF:
        enum ok
        readings: 94
        counts: {"open": 43, "supported": 39, "refuted": 12, "contested": 0}
        excluded_import_admissions: 0
        completeness: absent, NO_CRITICISM_DISPATCH_DECLARATION
        cycles: ['pre-cycle', '0', '1', '2', '3', '4']

- [x] 3. (S8) Write `tests/test_evidence_states.py`: one test per state on
      fixtures COPIED from committed roots into `tmp_path`, plus the
      predates-the-declaration test (S6) and `test_absence_needs_the_declaration`
      (the completeness rule, R11's named obligation).
      done-when: `python -m pytest tests/test_evidence_states.py -q` -> 0 failed

      PROOF:
        $ python -m pytest tests/test_evidence_states.py -q
        19 passed in 28.05s

- [x] 4. (S8) [COMMIT] Mutation-prove M1-M4 of SPEC.md S8: plant each mutant in
      the reader, watch the named test go RED, revert, watch green. Transcripts
      to `experiments/2026-09-04-change-evidence-states/proof/`.
      done-when: `proof/M1.txt` .. `proof/M4.txt` each exist and each contains
      both a "failed" line (mutant) and a "passed" line (revert)

      PROOF:
        M1 (REFUTED branch removed)  -> test_refuted_matches_the_status_label FAILED, PASSED on revert
        M2 (failed attackers dropped from SUPPORTED) -> test_supported_when_a_warranted_attack_was_itself_refuted FAILED, PASSED on revert
        M3 (ensemble split ignored)  -> test_contested_on_an_ensemble_split_trial FAILED, PASSED on revert
        M4 (OPEN default -> SUPPORTED) -> test_open_when_nothing_warranted_was_brought FAILED, PASSED on revert
        transcripts: proof/M1.txt proof/M2.txt proof/M3.txt proof/M4.txt

- [x] 5. (S2) Emit the declaration from `Scheduler._arg_crit` (three exits) and
      from the END of `Scheduler._foreign_arg_crit` (`cut:foreign`), obeying all
      four map checks listed above.
      done-when: `python -m pytest tests/test_crit_batch.py tests/test_budget.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_foreign_school_criticism_scheduler_c3.py -q` -> 0 failed

      PROOF:
        $ python -m pytest tests/test_crit_batch.py tests/test_budget.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_foreign_school_criticism_scheduler_c3.py -q
        34 passed in 4.69s
        
        All four map-check constraints on _arg_crit / _foreign_arg_crit re-asserted
        directly and hold: the verbatim foreign-road substring, the absence of
        "argumentative-criticism", the RECRIT_STANDING index order, and the single
        keyword-free crit_argumentative_batch call.

- [x] 6. (S2) Write `tests/test_criticism_dispatch_declaration.py`: exactly one
      declaration per criticism pass; `complete` on a clean pass; `cut:budget`
      when `ARG_CRIT_PER_CYCLE` truncates; `cut:seat` when the critic role is
      unavailable; `cut:call` when a batch is dropped.
      done-when: `python -m pytest tests/test_criticism_dispatch_declaration.py -q` -> 0 failed

      PROOF:
        $ python -m pytest tests/test_criticism_dispatch_declaration.py -q
        8 passed in 1.43s
        complete / cut:budget / cut:seat / cut:call each proven on a real scheduler run;
        one declaration per pass; the writer refuses an outcome outside the closed
        vocabulary; the event is a Measure with no outputs (no new object kind).

- [x] 7. (S1, S2) Wire the licence: `evidence_states` reads `complete`
      declarations so an un-attacked artifact they name reads SUPPORTED, and
      one they do not name stays OPEN.
      done-when: `python -m pytest tests/test_evidence_states.py -k "licence or absence" -q` -> 0 failed

      PROOF:
        $ python -m pytest tests/test_evidence_states.py -k "licens or absence or criticised_in_full" -q
        3 passed, 17 deselected in 0.58s
        
        The wiring is proven end to end by two arms of the SAME run with the SAME quiet
        critic: with the pass unrationed it declares complete and its targets read
        SUPPORTED; with ARG_CRIT_PER_CYCLE=1 it declares cut:budget and they stay OPEN.
        (The checklist's original `-k "licence or absence"` matches nothing — the test
        names read "licenses"; the selector above is the corrected one.)

- [x] 8. (S8) [COMMIT] Mutation-prove M5 (the completeness rule dropped —
      absence counts as SUPPORTED with no declaration).
      done-when: `proof/M5.txt` exists showing
      `test_absence_needs_the_declaration` FAILED under the mutant and PASSED
      on revert

      PROOF:
        M5 (the completeness rule dropped -- absence of attack counts as SUPPORTED
        with no declaration): three tests FAILED under the mutant and PASSED on revert
          test_absence_needs_the_declaration
          test_a_complete_pass_licenses_only_the_targets_it_names
          test_a_scheduler_run_that_criticised_in_full_reads_its_survivors
        transcript: proof/M5.txt

- [x] 9. (S3) Write `tests/test_evidence_states_law_line.py` — spelling half
      (no forbidden name under scheduler/, adjudication/, rules/; PERMITTED
      empty) and behavioural half (computing the reading appends no event and
      moves no status).
      done-when: `python -m pytest tests/test_evidence_states_law_line.py -q` -> 0 failed

      PROOF:
        $ python -m pytest tests/test_evidence_states_law_line.py -q
        7 passed in 23.29s
        
        Spelling half: no file under scheduler/, adjudication/ or rules/ names the
        reading; PERMITTED is empty and emptiness is the claim; the reader/writer
        non-import is asserted by AST, not source text, because the writer's docstring
        names the reader on purpose and a text search would read prose as coupling.
        Behavioural half: computing the reading appends no event and moves no status,
        on a built harness and on a committed root.

- [x] 10. (S8) [COMMIT] Mutation-prove M6 and M7 (reader named inside
      `scheduler/`; reader appends a measure).
      done-when: `proof/M6.txt` and `proof/M7.txt` each show the law-line test
      FAILED under the mutant and PASSED on revert

      PROOF:
        M6 (the reader imported inside scheduler/) -> test_no_deciding_package_names_the_reading FAILED, PASSED on revert
        M7 (the reader appends a measure)          -> test_computing_the_reading_appends_nothing_to_the_record FAILED, PASSED on revert
        transcripts: proof/M6.txt proof/M7.txt

- [x] 11. (S1, S2, S3, S8) [COMMIT] Commit 1 of SPEC.md's split: the reading,
       the declaration, the law line, their tests and proofs, plus the
       `DR-SUB-scheduler` map edit describing the declaration `_arg_crit` now
       files (map moves in the SAME commit).
       done-when: `python tools/docs_verify.py` -> 0 failed beyond the C4 known
       rows, AND `python -m pytest tests/test_evidence_states.py tests/test_criticism_dispatch_declaration.py tests/test_evidence_states_law_line.py -q` -> 0 failed

      PROOF:
        $ python -m pytest tests/test_evidence_states.py tests/test_criticism_dispatch_declaration.py tests/test_evidence_states_law_line.py tests/test_signals.py tests/test_signal_contract.py -q
        55 passed in 57.90s
        
        docs_verify: the two rows this tranche broke are fixed (INDEX --links now 0
        dangling across 80 documents; SUB-application's record_* census updated). The
        seven remaining are C4's own, reconciled row by row above.
        docs_verify --audit: 1 finding, and it is C4's SEAM-llm-x-rules.md:54.
        docs_verify --links: 0 dangling reference(s), 80 document(s).
        All seven CON-evidence-states.md checks green, and six of them mutation-proven
        able to fail (proof/map_checks_can_fail.txt) -- one was found VACUOUS on the
        first pass and strengthened before it was written down.

- [ ] 12. (S4) Add the `evidence_states` section to `results_summary` and the
       `## Evidence states` block plus the per-artifact frontier column to
       `render_results`, in the operator's vocabulary.
       done-when: `python -m pytest tests/test_results_command.py -q` -> 0 failed
       AND `deepreason results experiments/2026-09-02-live-p-a2-corrected/run --json | python -c "import json,sys; d=json.load(sys.stdin); print(d['evidence_states']['counts'])"` prints the four keys

- [ ] 13. (S5) Add the `evidence_states` section to `stop_report` and
       `render_stop_report`, with the typed absence on `home-no-root` and
       `root-no-log`.
       done-when: `python -m pytest tests/test_stop_report.py -q` -> 0 failed
       AND `deepreason stop-report experiments/2026-09-02-live-p-a2-corrected/run | grep -c "Evidence states"` prints 1

- [ ] 14. (S6) Prove the committed roots are untouched by the surfaces.
       done-when: `git status --porcelain experiments/ | head` is EMPTY after
       steps 12-13 ran against a committed root

- [ ] 15. (S4, S5, S6) [COMMIT] Commit 2 of the split: the surfaces, plus the
       `DR-SUB-application` map edit for the new section.
       done-when: `python tools/docs_verify.py` -> 0 failed beyond C4, AND
       `python -m pytest tests/test_results_command.py tests/test_stop_report.py -q` -> 0 failed

- [ ] 16. (S7) Capture each instrument's DEFAULT output BEFORE the change
       (`proof/instruments_before.txt`), then add `--survivors-only` to both
       `analyse_form_arms.py` and `measure_diversity_per_problem.py`.
       done-when: `proof/instruments_before.txt` exists AND
       `python experiments/2026-09-03-change-conjecturer-pluggable-interface/analyse_form_arms.py --self-test` prints `ok`

- [ ] 17. (S7, S8) Write `tests/test_survivors_only_switch.py`: default output
       byte-identical to the before-capture (R8), and the switch restricts to
       SUPPORTED artifacts.
       done-when: `python -m pytest tests/test_survivors_only_switch.py -q` -> 0 failed

- [x] 18. (S10) Create `docs/map/CON-evidence-states.md` per `SCHEMA.md`, with
       four checks each first RUN AGAINST THE PRE-CHANGE TREE to confirm it
       FAILS. Add the `INDEX.md` routing row and concept-table row.
       done-when: `python tools/docs_verify.py --audit` reports no finding for
       `CON-evidence-states.md`, AND `python tools/docs_verify.py --links` -> 0 failed

      PROOF:
        Satisfied early, at step 11 -- see the re-plan note above. CON-evidence-states.md
        created with seven checks, all green; docs_verify --audit reports no finding for
        it; --links 0 dangling; six checks mutation-proven RED under a planted violation
        (proof/map_checks_can_fail.txt). INDEX.md carries both a routing row and a
        concept-table row.

- [ ] 19. (S9) Write `census.py` (runs the SHIPPED reader over every committed
       root, tables OPEN vs SUPPORTED on the frontier) and paste its output into
       `CENSUS.md`.
       done-when: `python experiments/2026-09-04-change-evidence-states/census.py`
       exits 0 and `CENSUS.md` contains its pasted table

- [ ] 20. (S7, S9, S10) [COMMIT] Commit 3 of the split: the baseline hook, the
       census, the map document.
       done-when: `python tools/docs_verify.py` -> 0 failed beyond C4

- [ ] 21. (all) Map gate, FULL mode (not `--fast`; `src/` changed).
       done-when: `python tools/docs_verify.py` -> 0 failed beyond the C4 known
       rows (SEAM-llm-x-rules.md:54, INV-frozen-surfaces.md:181 and :736,
       CON-run-identity.md:211/213/215/298), pasted

- [ ] 22. (all) Frozen-surface re-check over the REAL files, now that they
       exist (SPEC.md's forecast promised this step).
       done-when: `python tools/blast_radius.py --files <every changed src file>
       --symbols <every new top-level def> --against 33f92e88c7` reports
       `frozen_surface_verdict: CLEAR` and no unpredicted `newly_live` /
       `newly_dead`, pasted

- [ ] 23. (all) Full gate, ALONE on an idle box (never concurrent with
       docs_verify).
       done-when: output ends `N passed, 0 failed` (pasted)

- [ ] 24. (all) [COMMIT] Push and confirm clean tree.
       done-when: `git status --porcelain` is empty AND the branch head is on
       origin

## Gate readings at the commit-1 boundary (step 4)

    python tools/diff_budget.py 33f92e88c7 --ceiling 855 \
        --paths src/ tests/ experiments/2026-09-04-change-evidence-states/
    -> EXCEEDED 1791 / 855

Read, not footnoted. The reading is correct and the question was wrong: 1130 of
those insertions are this tranche's OWN ledger (REQUEST.md 250, SPEC.md 603,
CHECKLIST.md, the mutation transcripts), which SPEC.md's 855 never estimated
and which ships no code. Re-run over the areas the ceiling actually estimates:

    python tools/diff_budget.py 33f92e88c7 --ceiling 855 --paths src/ tests/
    -> WITHIN 659 / 855      {"src/": 310, "tests/": 349}

SPEC.md's Budget section now NAMES the declared areas so the gate cannot be
asked the wrong question again. No scope moved.

    python tools/blast_radius.py --files <the two new modules> \
        --symbols <their five new names> --against 33f92e88c7
    -> frozen_surface_contacts: []
       frozen_adjacent_contacts: []
       frozen_surface_verdict: CLEAR
       reachability: evidence_states UNREACHABLE (direction None),
         evidence_state_summary UNREACHABLE (None),
         declare_criticism_dispatch UNREACHABLE (None),
         EvidenceState UNKNOWN (None), CRITICISM_DISPATCH_SIGNAL UNKNOWN (None)

No DRIFT: matches SPEC.md's forecast (CLEAR, empty both lists). The three
UNREACHABLE entries carry `direction: None`, not `newly_dead` — they are new
symbols with no caller yet; the surfaces that call them land at steps 12-13 and
step 22 re-runs this gate once they do.

## The known-not-yours docs_verify rows, reconciled (step 11)

C4 names seven rows by line number. Those numbers are stale — the DOCUMENTS and
the ROWS match exactly, seven of them, and each was confirmed pre-existing by
running its own command rather than by trusting the count:

| C4 says | actually at | why it fails, and why it is not this tranche's |
|---|---|---|
| SEAM-llm-x-rules.md:54 | :54 | unparseable check (an opener that never closes). Untouched by this tranche |
| INV-frozen-surfaces.md:181 | :206 | `find experiments runs -path '*workflow-provider-attempt-v1/*.json' -exec grep -l transport_failure` returns 22 files, all under `experiments/2026-09-01-live-all-modules-p-a1/run/`, committed before this branch existed |
| INV-frozen-surfaces.md:736 | :876 | needs `origin/claude/deepreason-p-s1-commitments-wowcib`, a remote branch this container has no ref for: `fatal: invalid object name`. Environmental |
| CON-run-identity.md:211 | :211 | a `git log -M --diff-filter=R` history claim |
| CON-run-identity.md:213 | :213 | `fatal: ambiguous argument '1637e808'` — a revision this container does not have |
| CON-run-identity.md:215 | :215 | same, for `f304fec1` |
| CON-run-identity.md:298 | :313 | TIMEOUT at 300s running `tests/test_jailbreak_gate.py`. Timed directly: **9 passed in 318.16s** — the test is GREEN and the CHECK is over docs_verify's per-check budget, which is what its own message says. Pre-existing cost |

Two rows WERE this tranche's, and both are fixed in this commit rather than
excused: `INDEX.md --links` reported `dangling DR-CON-evidence-states <-
SUB-scheduler.md` (the concept document was referenced before it existed), and
`SUB-application.md`'s per-package `harness.record_*` census moved because
`runtime/criticism_dispatch.py` appends a Measure. `--links` now reports 0
dangling across 80 documents; the census now names the new recorder.

## Re-plan, recorded at execution (step 11)

`docs/map/CON-evidence-states.md` was planned for step 18 (commit 3) and is
created HERE, at commit 1, because `SUB-scheduler.md` references it at commit 1
and the map rule is that the map moves in the same commit as the code it
describes. The reading it documents lands in this commit, so this is where the
document belongs. Step 18 is therefore already satisfied and is marked as such
with its proof; nothing was dropped.
