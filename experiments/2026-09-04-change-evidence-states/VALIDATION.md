# Validation for: four evidence states over the record, and a per-cycle
# declaration that criticism ran in full

Every acceptance check in SPEC.md re-run here on the assembled whole, in item
order, even where a checklist step already ran it.

## Acceptance checks

### S1 (R1, R2, C2) — the reader and the four states

    $ python -c "from deepreason.views.evidence_states import EvidenceState; \
        assert [s.value for s in EvidenceState] == ['open','supported','refuted','contested']"
    four states, in order: ok

    $ python -m pytest tests/test_evidence_states.py -q
    23 passed in 29.18s

**PASS.**

### S2 (R4, R5) — the per-cycle completeness declaration

    $ python -m pytest tests/test_criticism_dispatch_declaration.py -q
    9 passed in 1.40s

Covers `complete`, `cut:budget`, `cut:seat` and `cut:call` on real scheduler
runs; one declaration per pass; the writer refusing an outcome outside the
closed vocabulary; the event being a Measure with no outputs; and the signal's
registry declaration. **PASS.**

### S3 (R3) — the law line

    $ python -m pytest tests/test_evidence_states_law_line.py -q
    7 passed in 26.52s

**PASS.**

### S4 (R6) — `deepreason results`

    $ deepreason results experiments/2026-09-02-live-p-a2-corrected/run --json
    counts: {'contested': 11, 'open': 63, 'refuted': 12, 'supported': 8}
    sum == non-import artifacts: 94
    frontier column len: 29   frontier ids: 29

The four keys are present, they sum to the root's non-import artifact count,
and the per-artifact column is exactly as long as the frontier listing it
annotates. **PASS.**

### S5 (R6) — `deepreason stop-report`

    $ deepreason stop-report experiments/2026-09-02-live-p-a2-corrected/run \
        | grep -c "EVIDENCE STATES"
    1

    $ python -m pytest tests/test_stop_report.py -q
    19 passed

**PASS.**

### S6 (R10) — typed absence over a record that predates the declaration

    $ python -m pytest \
        tests/test_evidence_states.py::test_a_root_that_predates_the_declaration_says_so \
        tests/test_evidence_states.py::test_the_blind_root_is_the_canonical_open_case \
        tests/test_evidence_states.py::test_reading_a_committed_root_leaves_it_byte_unchanged -q
    3 passed in 16.84s

    $ git status --porcelain experiments/
     M experiments/2026-09-04-change-evidence-states/CHECKLIST.md

The only modified path under `experiments/` is this tranche's own ledger; every
committed run root the readers were run against is byte-unchanged. **PASS.**

### S7 (R7, R8) — `--survivors-only` on both instruments

    $ python experiments/2026-09-03-change-conjecturer-pluggable-interface/analyse_form_arms.py --self-test
    ok

    $ python -m pytest tests/test_survivors_only_switch.py -q
    9 passed in 75.15s

Both default paths byte-identical to the capture taken BEFORE the switch
existed. **PASS.**

### S8 (R11) — the mutation proof

Seven mutants, each watched RED under its own planted violation and green on
revert; transcripts committed under `proof/`.

| M | mutant | test that went red |
|---|---|---|
| M1 | REFUTED branch removed | `test_refuted_matches_the_status_label` |
| M2 | failed attackers dropped from SUPPORTED | `test_supported_when_a_warranted_attack_was_itself_refuted` |
| M3 | ensemble split ignored | `test_contested_on_an_ensemble_split_trial` |
| M4 | OPEN default flipped to SUPPORTED | `test_open_when_nothing_warranted_was_brought` |
| M5 | **the completeness rule dropped** | `test_absence_needs_the_declaration` + 2 more |
| M6 | the reader named inside `scheduler/` | law line, spelling half |
| M7 | the reader appends a measure | law line, behavioural half |

Six map checks proven the same way (`proof/map_checks_can_fail.txt`), one of
which was found VACUOUS on the first pass and strengthened before it was
written down. **PASS.**

### S9 (R13) — the census

    $ python experiments/2026-09-04-change-evidence-states/census.py
    # Evidence-state census over 77 committed run roots
    - admitted artifacts read: 8683
      open 7713 (88.8%) | supported 47 (0.5%) | refuted 844 (9.7%) | contested 79 (0.9%)
    - frontier artifacts read: 941
      open 939 (99.8%) | supported 1 (0.1%) | refuted 0 (0.0%) | contested 1 (0.1%)
    - roots carrying a criticism-dispatch declaration: 0 of 77

Pasted in full in `CENSUS.md`. **PASS.**

### S10 (R12) — the map moves in the same commit

`docs/map/CON-evidence-states.md` created with seven checks; `INDEX.md`,
`SUB-application.md` and `SUB-scheduler.md` updated. Outputs under **Map**
below. **PASS.**

## Full gate

    $ python -m pytest tests/ -q -n 4     (alone on an idle box)
    5073 passed, 6 skipped in 1646.95s (0:27:26)

**0 failed: PASS.** No assertion was weakened. Two fixtures moved, both
predicted EXPECTED TO MOVE in SPEC.md's blast-radius census, and both gained a
NAME rather than losing a claim: `test_results_command`'s declared
absence-reason vocabulary, and `test_stop_report`'s sections key set.

## Record-behavior preservation

The change adds a READER over the record, so the verdicts that reader could
have disturbed were re-derived on three committed roots:

    experiments/2026-09-02-live-p-a2-corrected/run
        violations: ['foreign-criticism']
        events=1947 artifacts=94 accepted=82 refuted=12
    experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847
        violations: ['foreign-criticism'] x4
        events=607 artifacts=39 accepted=39 refuted=0
    experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a
        violations: ['terminal-authority']
        events=406 artifacts=53 accepted=53 refuted=0

**Unchanged, by construction as well as by observation.** The six `src/` files
this tranche changed are

    src/deepreason/application/results.py
    src/deepreason/application/stop_report.py
    src/deepreason/runtime/criticism_dispatch.py
    src/deepreason/scheduler/scheduler.py
    src/deepreason/signals.py
    src/deepreason/views/evidence_states.py

and `verify_root` is computed by `invariants.py`, `verification/`,
`adjudication/`, `harness.py` and `ontology/` — none of which appears in that
list. A verdict computed by code the tranche did not change, over a root the
tranche did not touch, cannot have moved.

## Frozen-surface diff

    $ git diff --stat 33f92e88c7..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/
    (empty)

**Empty: PASS.** The mechanical tripwire agrees with SPEC.md's forecast and
with `blast_radius.py`'s `frozen_surface_verdict: CLEAR`, both contact lists
empty, run again after the files existed.

## Map

    docs_verify:            80 documents, 1380 checks, 7 failed : PASS
    docs_verify --audit:    1 finding                            : PASS
    docs_verify --links:    0 dangling, 80 documents             : PASS
    docs_verify --coverage: 2 findings, 7 seams swept, 21 without a Sweep: header : PASS

**The 7 `docs_verify` failures are exactly C4's known-not-yours rows**, one per
row, no more and no less; CHECKLIST.md reconciles them document by document and
each was confirmed pre-existing by running its own command (two are git
revisions this container has no ref for, one is a remote branch it has no ref
for, one is a `find` over experiment JSON committed before this branch existed,
one is an unparseable check, one is a history claim, and one is
`tests/test_jailbreak_gate.py` at 318s against docs_verify's 300s per-check
budget — the test itself is GREEN).

The 1 `--audit` finding is C4's `SEAM-llm-x-rules.md:54`. The 2 `--coverage`
findings are `SEAM-periphery-x-verification.md` (enforcement site
`amendment/apply.py` not named) and `SEAM-schools-x-scratch.md` (enforcement
site `informal/trial.py` not named); this tranche touches neither file and
neither document.

**docs_verify --stale: 20 documents.** Five name a commit of this tranche, and
each is judged individually rather than passed over:

| document | why my commit appears | disposition |
|---|---|---|
| `SEAM-scheduler-x-rules.md` | owns `scheduler.py` | **Dismissed.** Its subject is what the scheduler passes to `rules/` — the ration, the batch, the keyword-free call. The declaration changes none of it: all 9 of its checks are green, including the three that pin `_arg_crit`'s verbatim shape |
| `SEAM-scheduler-x-workflow.md` | owns `scheduler.py`; `_foreign_arg_crit` gained the `cut:foreign` declaration at entry | **Dismissed with a reason that matters.** Its subject is the foreign-criticism plan and its coverage receipts, and both are untouched; its `_foreign_arg_crit` ordering check is green. The declaration belongs to a different seam, and it IS documented — in `SUB-scheduler.md` and in `CON-evidence-states.md`'s Traps, where the `cut:foreign` choice is stated and its consequence parked as P2 |
| `SEAM-schools-x-scheduler.md` | owns `scheduler.py` | **Dismissed.** School allocation is untouched |
| `CON-scheduler-ranking.md` | owns `scheduler.py` | **Dismissed.** Problem selection and the rank tuple are untouched; the law line forbids the reading from reaching rank at all, and pins it |
| `INV-signal-contract.md` | owns `signals.py`; this tranche adds one `SignalDeclaration` | **Dismissed.** Adding a signal through the declared channel is what that contract PRESCRIBES (`DR-REC-add-signal`), not a change to it. The document carries no signal count, `MIGRATION_DEBT` is an upper bound and the new declaration adds none (its unit and staleness are stated, not `unspecified`), and `tests/test_signal_contract.py` is green |

The other fifteen name only commits from earlier tranches. They are
pre-existing staleness carried in, not this tranche's to close — one tranche,
one goal — and they are what the audit family's docs-drift dimension exists for.

**New checks added by this change:** seven in `docs/map/CON-evidence-states.md`
(six mutation-proven able to fail), one in `docs/map/SUB-scheduler.md` (the
declaration's emission points and outcome ordering, mutation-proven), one in
`docs/map/SUB-application.md` (both surfaces show one derivation and
stop-report opens no `Harness`, mutation-proven), plus the updated
`record_*` census row in `SUB-application.md`.

**Record observables added vs sweep probes:** one observable — the
`criticism.dispatch.v1` Measure. **No sweep probe is owed, and this is a
recorded decision rather than an omission**: `tools/root_sweep.py` is RETIRED
as an instrument by operator ruling of 2026-08-22 ("it just wastes time"), and
CLAUDE.md forbids any tranche from requiring a committed-root sweep. The
equivalent proof is delivered instead as targeted regressions on committed
roots (S6) plus the census over all 77 of them (S9). The observable IS
otherwise guarded: the reader landed before the writer emitted, the
absence-tolerant path is pinned on real committed roots, and the signal is
declared in the registry with an assertion of its own because
`tests/test_signals.py`'s AST scan cannot see a constant-headed signal (parked
as P1).

**Wheel smoke: packaging surface untouched — smoke not owed.** No console entry
point, no MCP tool, no schema, no wheel layout changed; `grep` finds no
reference to `results` or `stop-report` in either smoke; and
`blast_radius.py` reports `consumers.wheel_smoke_pins: []` and
`consumers.qualification_digest: []`.

## Requirement sweep

| R | demonstrated by |
|---|---|
| R1 four derived readings | S1 — the enum, and one test per state including the two CONTESTED roads |
| R2 computed from facts already in the record | S1 — the reader consumes `state.att`, `state.status`, `state.artifacts` and the trial measure signals; it registers nothing and computes no warrant |
| R3 changes no admission, rank, immunity or refutation | S3 — spelling half over the operator's own three packages with an EMPTY exception list, behavioural half proving the reading appends nothing and moves no label; M6/M7 |
| R4 the completeness rule | S2 and S1's `test_absence_needs_the_declaration`; M5 |
| R5 design the declaration first, prefer `record_measure` | SPEC.md §0, written before any code: the measure channel carries it, no new record object kind, no surface-2 contact, no grant needed and therefore no STOP |
| R6 counts per state per cycle on both surfaces, per-artifact frontier column, typed absence | S4, S5, S6 |
| R7 `--survivors-only` on both instruments | S7 |
| R8 no default behaviour changes | S7 — pinned against a capture taken before the switch existed |
| R9 forecast NO CONTACT, run `blast_radius.py`, paste the verdict | SPEC.md's Frozen-surface contact forecast, pasted verbatim; re-run after the files existed, still CLEAR; and the frozen diff above is empty |
| R10 historical roots never edited; OPEN/REFUTED only, and say why | S6 — and the reading over a declaration-less root is discussed honestly in SPEC.md A1, which records where the request's summary sentence is narrower than R1+R4 together |
| R11 mutation-proven tests, the architecture test, the completeness rule proven RED | S8 — including the blind-critic fixture finding, recorded rather than papered over |
| R12 full gate 0 failed, docs_verify FULL, map in the same commit | Full gate 5073 passed 0 failed; docs_verify 7 failed, all C4's; the map moved in commits 1, 2 and 3 beside the code each document describes |
| R13 the final message reports the OPEN-vs-SUPPORTED number | S9 — `CENSUS.md` carries it, re-derivable by `census.py` |

No R is deferred.

## Assumptions carried (SPEC.md — the operator may override any of these)

- **A1.** R10's "OPEN/REFUTED only" is read as the ABSENCE road, not as a
  ceiling on the whole reading: a declaration-less root can still show
  SUPPORTED where an attacker was itself refuted, and CONTESTED where judges
  really split, because those are positive facts the record carries. The
  binding property implemented is that **no artifact is ever read as SUPPORTED
  on the strength of an absence** unless a `complete` declaration licenses it.
- **A2.** "Every planned criticism call was made" is measured at the
  argumentative pass, `Scheduler._arg_crit`. Deterministic upstream criticism
  (`crit_program`, `crit_fuzz`) is not counted, because it cannot be cut by
  budget or a retired seat.
- **A3.** "The diversity instrument" is `measure_diversity_per_problem.py`, not
  `2026-08-28-diversity-generation/analyse.py` — traced, not guessed: the
  latter reads raw provider-call directories, never opens a run root, and the
  switch would be inert in it.
- **A4.** "Typed absence" follows the file's own `{"absent": True, "reason":
  <CODE>}` convention; two codes were added to the closed vocabulary.
- **A5.** The reader lives in `views/`, the declaration's writer in `runtime/`,
  so the scheduler can emit without importing the reading.
- **A6.** Per-cycle counts attribute an artifact to the cycle in which it was
  first registered; artifacts registered before the first heartbeat go to a
  typed `pre-cycle` bucket rather than silently to cycle 0.

Two further things the operator should see, neither an assumption but both
decisions taken in this window:

- **SPEC.md Amendment 1** — the diff budget read EXCEEDED 1797/855 and is
  disposed there in the standard stop format: every insertion traces to a spec
  item, no R gained scope, and the ceiling was re-priced to 2250 (final reading
  WITHIN 2029/2250). The change is twice the size it was specified at. It is
  the same change.
- **The trial-vocabulary correction** — the reader's first version counted
  every declined or blocked trial as a survival, which called 39 of the P-A2
  root's 94 artifacts survivors. Found by running the surface over a committed
  root, not by reading code. The corrected reading gives 8.

## Verdict: PASS
