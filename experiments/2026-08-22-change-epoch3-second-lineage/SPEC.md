# Spec for: "reach epoch 3 — put a SECOND problem lineage in the root, then launch"

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are
bugs. This is a DESIGN-AND-EXECUTE spec whose design half is settled by
measurement (§Measurements) rather than by reading the parked notes forward.

Map preflight (CLAUDE.md; dr-drive-harness §4). Resolved ids, recorded here
so every later phase starts from the same map:

- `DR-SUB-amendment` — `src/deepreason/amendment/` (`apply.py`, `state.py`):
  the amendment-epoch machinery, which is the vehicle under test.
- `DR-SUB-application` — `src/deepreason/application/text_runs.py`: the ONE
  run path (operator law 2026-08-13), including `continue_run` and the
  epoch-aware request/spec agreement check that decides whether an amended
  root may be continued.
- `DR-SUB-workloads` — `src/deepreason/workloads/text.py`:
  `ReasoningWorkloadSpec` / `seed_reasoning_workload`, which decide how many
  problems a text run can seed and with what criteria.
- `DR-SUB-measures` — `src/deepreason/measures/reach.py`: `reach_sweep`, the
  measure the tranche exists to make fire.
- `DR-CON-run-identity` — run id and the qualification subject digest, both
  of which move when the manifest's capability policy moves.
- `DR-INV-frozen-surfaces` — read before designing; the forecast below is
  the tool-computed result, not a hand check.
- Seam read before the subsystems: `docs/map/INDEX.md`'s matrix carries no
  `SEAM-amendment-x-application.md`, so the two subsystem documents were
  read in its place. **That absent seam is a map finding, recorded in
  PARKED.md (P3-epoch3), not a blocker** — and the defect this spec
  measures (M4) sits exactly on the pair the missing seam would cover.

---

## Measurements

Every load-bearing claim below is a pasted command result. Anything not
measured is in Assumptions, where the operator can see it.

**M1 — the amendment machinery DOES create a second seeded lineage.**
`amend --reshape-question` on a scratch COPY of the epoch-2 root (never the
committed root; dr-drive-harness §3):

    $ python -m deepreason --root <scratch-copy> amend \
        --reshape-question "<sibling question>"
    "epoch": 1,
    "problem_id": "question-07d84c43d59d17282fef7db6ba7adaff",
    "superseded_problem_id": "question-4dd62735b90864a75220e09b302500bc",
    rc=0

    $ # the replayed state, after the amendment
    question-07d84c43d59d17282fef7db6ba7adaff ->
        (SpawnTrigger.SEED, ['uhi-energy-balance@v1',
                             'uhi-nocturnal-release@v1',
                             'uhi-cross-city-modulator@v1'])
    question-4dd62735b90864a75220e09b302500bc ->
        (SpawnTrigger.SEED, ['reasoning-envelope-wf',
                             'uhi-energy-balance@v1',
                             'uhi-nocturnal-release@v1',
                             'uhi-cross-city-modulator@v1'])
    problems total 106   (was 105)

Supports: R6a's mechanism is real. `amendment/apply.py::_apply_ledger_chain`
registers the reshaped question as a `trigger="seed"` problem, so the root
holds TWO seed lineages.

**M2 — the second lineage cannot carry DISTINCT criteria.**
`amendment/apply.py:465-470` builds the successor run input with
`criteria=parent_input.problem.criteria`, and
`apply.py::_successor_workload` `model_copy`s the parent spec updating only
`problem` and `sources`. `workloads/text.py::ReasoningWorkloadSpec` holds
one `problem: WorkloadProblem` and one `criteria` tuple. M1's own output is
the measurement: the new problem's criteria are the parent's three, verbatim.

Supports: R6a's parenthetical "carrying its OWN subject-substantive criteria
(distinct predicates...)" is NOT satisfiable through any amend surface. The
lineage is deliverable; distinct predicates are not.

**M3 — the named root `40e713b3…` is not amend-ready, by its own typed
record.**

    $ python -m deepreason results experiments/2026-08-22-live-reach-rich-run/run --json
    "terminal": {"amend_ready": false,
                 "stop_reason_resumable": false,
                 "terminal_epoch": 0,
                 "valid_typed_terminal": true}
    "run": {"state": "failed", "stop_reason": "operational_failure",
            "cycles_completed": 2}

`workflow/lifecycle.py:28`:
`RESUMABLE_STOP_REASONS = frozenset({"converged", "budget_exhausted"})`, and
`lifecycle.py:273` raises `terminal stop reason does not authorize
continuation` for anything else.

Supports: R6a's premise "state=failed is a typed terminal" is true and
insufficient. A valid typed terminal is one of TWO conditions; the stop
reason is the other, and `operational_failure` fails it.

**M4 — a question-only amendment produces a root `continue` always refuses.**
Attempting the continuation on the M1 scratch copy:

    $ python -m deepreason --root <scratch-copy> continue --budget cycles=1
    RUN_INPUT_MISMATCH: text request differs from the frozen v6 run input
    rc=1

Isolated to exactly one of the five conditions at
`application/text_runs.py:1184-1194`:

    c1 verified vs manifest         False
    c2 runinput vs manifest         False
    c3 epoch_input NOT match spec   False
    c4 dossier digest mismatch      False
    c5 dossier problem_ref mismatch True  question-4dd62735b90864a75220e09b302500bc

Cause: with no `--attach`, `apply.py` sets `successor_dossier =
parent_dossier` ("A question-only amendment cites exactly the dossier its
parent did"), whose `problem_ref` still names the SUPERSEDED problem, while
the continuation's spec now carries the successor problem id. The one
covering gate test, `tests/test_amendment_epochs.py::
test_continuation_runs_the_reshaped_question_under_the_same_root`, always
passes `attach=`, so the question-only path is untested.

Supports: even on a resumable root, `--reshape-question` ALONE is not a
vehicle. This is a defect; PARKED as P1-epoch3 (C2: no harness features in a
live-run tranche).

**M5 — `--attach` is refused on the epoch-2 root's manifest.**

    $ python -m deepreason --root <scratch-copy-2> amend \
        --attach <file>.md --reshape-question "<sibling question>"
    AMEND_EVIDENCE_NOT_AUTHORIZED: this run's manifest does not enable attached evidence

`amendment/apply.py:252-259` gates on
`manifest.inquiry_capability_policy.attached_evidence.enabled`, and the
reach-rich manifest has it `false` (PREREG.md §3 deliberately bound no
dossier).

Supports: M4's only workaround is unavailable on the named root. Together
M3+M4+M5 close vehicle (1) as literally specified.

**M6 — vehicle (2) is closed by the workload model.**
`workloads/text.py:30-42`: `ReasoningWorkloadSpec.problem` is a single
`WorkloadProblem`; there is no plural. `seed_reasoning_workload`
(`text.py:288-311`) registers exactly one problem. No config or manifest
field expresses two sibling problems.

Supports: R6b has no surface. P4-reach's claim is re-derived, not assumed.

**M7 — the vehicle that DOES exist: a manifest with attached evidence
enabled, compiled offline, zero notices.**

    EVIDENCE-ON manifest_sha256 685990000eea3d73b762d3d25bd9997abcca3e36cf9c577cfd8196f8bf1666bb
    baseline                    40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c
    attached enabled            True
    notices                     []

Built by passing `inquiry_capability_policy=<baseline policy>.model_copy(
update={"attached_evidence": engaged_attached_evidence_policy(attached=True)})`
to `compile_run_manifest`. Nothing in `src/` changes; the policy object is
already public (`v6_policy.py:434`).

**M8 — the price of M7, measured not guessed: a full re-qualification.**
`qualification.py:248-282` puts the whole manifest dump (minus `compiled_at`
and `run_input_digest`) into the subject payload. The diff between the two
manifests' behavior payloads:

    DIFF /inquiry_capability_policy/attached_evidence/enabled  :: False -> True
    DIFF /inquiry_capability_policy/attached_evidence/maximum_excerpt_bytes_per_source :: 0 -> 262144
    DIFF /inquiry_capability_policy/attached_evidence/maximum_sources :: 0 -> 16
    DIFF /inquiry_capability_policy/attached_evidence/maximum_sources_per_pack :: 0 -> 8
    DIFF /inquiry_capability_policy/attached_evidence/maximum_total_bytes :: 0 -> 8388608
    manifest_behavior identical: False

So the qualification subject digest moves and the ~14-minute / ~1160-call
battery reruns once. Run identity also moves: the epoch-3 root is
`685990000eea3d73…`, which is why no `RUN_ALREADY_STARTED` retirement of the
reach-rich roots is needed.

**M9 — the operator's stated blocker is a property of TRUNCATION, not of
single-seed runs.** P4-reach and the brief say "a single-seed run puts every
accepted artifact on the seed's own problem — the seed is never FOREIGN to
anything". Measured on a committed single-seed text root that survived to
cycle 8, `experiments/2026-08-12-live-grounded-extension-expansion/run`:

    problems 2894   seeds ['question-6fcc770419da1e9c8fccb2db8ed32bbe']
    prefixes {'<seed>': 1, 'succ': 16, 'disc': 10, 'conn': 53, 'integ': 2814}
    addressed artifacts 262
    addressed target prefixes {'<seed>': 1, 'succ': 5, 'conn': 4}
    artifacts addressed to non-seed: 202
    accepted of those: 186
    run-stop.json reason: budget_exhausted   (cycle 8)

and on the reach-rich epoch-2 root, which died at cycle 2:

    problems by prefix {'<seed>': 1, 'disc': 1, 'conn': 23, 'research': 80}
    artifacts addressed at all: 24
    artifacts addressed to a NON-seed problem only: 0
    problems that are addressed by something: 1

Supports: 186 accepted artifacts addressed to spawned problems is exactly
the carrier the hypothesis needs — for each of them the seed problem IS
foreign. The reach-rich epochs lacked it because they stopped at cycle 2,
before the cascade produced an accepted candidate addressed elsewhere; the
correction is already stated in that tranche's RESULTS.md
("TRUNCATED-BEFORE-CARRIER"). `reach_sweep` reads `carried =
artifact.interface.commitments` (`reach.py:126`) — the ARTIFACT's own
battery, not its problem's criteria — so a `conn:` artifact carrying
`relation-form` alone finds all three of the seed's subject predicates novel
(coverage 3/4 = 0.75, above the untouched `REACH_COVERAGE_MIN` 0.5).

**M10 — a completed cycle budget terminates resumably.**
`experiments/2026-08-12-live-grounded-extension-expansion/run/run-stop.json`:
`"reason":"budget_exhausted"` at `"cycle":8`. So a phase-1 pass bounded by
`--budget cycles=N` reaches a stop reason `continue` accepts.

**M11 — only one ladder carries the P8-reach invocation.**

    $ grep -rn -- "--root.*results|results.*--root" experiments/*/*.sh experiments/*/*.py
    experiments/2026-08-22-live-reach-rich-run/reach_run.sh:101:
        python -m deepreason --root "$ROOT" results > "$HERE/results.txt" 2>&1 || true

Supports: R7's "check whether any OTHER committed ladder carries the same
invocation" — none does.

---

## The material contradiction, recorded rather than resolved silently

R6a names a mechanism — amend the existing root `40e713b3…` — and
dr-spec-change's rule for a NAMED mechanism is to verify it reaches the code
before adopting it. It does not: M3 (not amend-ready), M4 (question-only
amendment cannot be continued), M5 (`--attach` unauthorized on that
manifest). Three independent typed refusals, none fixable inside C1's
"NO src/tests changes".

R6c permits STOP only "if NEITHER vehicle exists without code changes". One
does — the SAME amendment machinery R6a asks for, applied to a root whose
manifest authorizes attached evidence (M7, M8). So this spec DELIVERS THE
PROPERTY R1 asks for (a second problem lineage in the root, via an
amendment epoch) and records the two deviations it costs:

- **D1**: the lineage lands in a NEW root (`685990000eea3d73…`), not in
  `40e713b3…`. That root stays retired and untouched (C6).
- **D2**: the second lineage's criteria are the seed's three predicates
  verbatim (M2), not "distinct predicates". The reach path this buys is
  unchanged either way, because novelty is measured against the artifact's
  own battery (M9), not the problem's criteria.

A third deviation is a genuine judgement call and is put to the operator at
the launch boundary, where their credential is needed anyway (§Questions).

---

## Items

**S1 (R1, R6a, C1) — the epoch-3 manifest builder.**
Files: `experiments/2026-08-22-change-epoch3-second-lineage/build_manifest_epoch3.py` (new).
Before: the reach-rich `build_manifest.py` compiles the frozen design with
`attached_evidence.enabled = false`, so no amendment may attach a source.
After: a sibling builder importing `QUESTION`, `CRITERIA`, `CONFIG_PATH`,
`COMPILED_AT` from that file unchanged, and differing in exactly one field —
the inquiry capability policy's `attached_evidence`, enabled via the public
`v6_policy.engaged_attached_evidence_policy(attached=True)`.
accept: `python build_manifest_epoch3.py <root>` prints
`"manifest_sha256": "685990000eea3d73b762d3d25bd9997abcca3e36cf9c577cfd8196f8bf1666bb"`,
`"compile_notices": []`, and a `manifest_behavior` diff against the
reach-rich manifest touching ONLY the five `attached_evidence` fields of M8.

**S2 (R1, R6a) — the amendment supplement and its control.**
Files: `supplement-nocturnal-collapse.md` (new),
`preflight_supplement.py` (new).
Before: nothing to attach; a supplement whose own text satisfied the seed's
predicates would make a later reach hit unattributable.
After: a short factual note admissible as the amendment's source, plus an
OFFLINE control proving the note's own bytes **FAIL at least one** of
`uhi-energy-balance@v1`, `uhi-nocturnal-release@v1`,
`uhi-cross-city-modulator@v1`.
accept: `python preflight_supplement.py` exits 0 and prints a per-predicate
verdict table in which the supplement is not a passing artifact; a supplement
that passes all three fails the check and the ladder refuses to launch.

**S3 (R1, R6a, R8, R9) — the two-phase epoch-3 ladder.**
File: `epoch3_run.sh` (new).
Before: `reach_run.sh` runs one pass and stops.
After: setup → preflight (reusing the reach-rich `preflight_seed.py` and
`preflight_supplement.py`) → qualify → **phase 1** `run --budget cycles=12
--token-budget 200000` → **amend** `--attach supplement --reshape-question
<sibling question>` → **phase 2** `continue --budget cycles=12
--token-budget 200000` → audit → census. Each stage logs `rc=` and refuses to
proceed on a non-resumable phase-1 terminal.
accept: `bash -n epoch3_run.sh` exits 0; a `DRY_RUN=1` pass executes setup +
both preflights + the P8-correct `results` invocation and stops before
`qualify` with `rc=0`; the committed script contains
`--budget "cycles=$PHASE1_CYCLES"` and `continue --budget
"cycles=$PHASE2_CYCLES"` summing to PREREG's 24 and the two token budgets
summing to 400 000 (R9).

**S4 (R7, M11) — the P8-reach ladder fix.**
File: `experiments/2026-08-22-live-reach-rich-run/reach_run.sh`, line 101.
Before: `python -m deepreason --root "$ROOT" results` — `results` takes its
target positionally, so it fell back to `DEEPREASON_HOME` and wrote
`RESULTS_ROOT_NOT_FOUND` into the committed audit artifact.
After: `python -m deepreason results "$ROOT"`.
accept: `python -m deepreason results
experiments/2026-08-22-live-reach-rich-run/run` prints the run summary
(state `failed`, stop_reason `operational_failure`, violations 0), and
`grep -c -- '--root "$ROOT" results' reach_run.sh` returns 0. No other ladder
matches (M11), so no sibling fix is owed.

**S5 (R6, R13) — the epoch-3 pre-registration.**
File: `PREREG_EPOCH3.md` (new), frozen before any provider call.
Content: the hypothesis inherited verbatim from the reach-rich PREREG §1; the
vehicle choice with M1-M11 as its warrant; the two-phase budget; the typed
judgement table (R10/R11/R12) including the P5 rulings' `E0` vocabulary and
the `coverage == 0.5` full-hit rule; and the deviations D1/D2 stated as
predictions, not discovered afterwards.
accept: the file exists, cites M-numbers, and its judgement section names
SUCCESS / UNSUPPORTED / PRECONDITION-BLOCKED / TRUNCATED-BEFORE-CARRIER with
the typed artifact that decides each.

**S6 (R3, R5, R14, R15) — scope and process proof.**
accept: `git diff --stat origin/main -- src/ tests/` is EMPTY at every phase
boundary, and every phase boundary is a commit pushed with the 2s/4s/8s/16s
retry ladder.

**S7 (R8) — launch discipline.**
After: launch `setsid nohup ./epoch3_run.sh & disown` from the tranche
directory, arm `snapshot_loop.sh` (reused from the reach-rich tranche, by
path), and monitor the newest root's `progress.jsonl` plus the driver log's
`rc=` lines, alerting on failure signatures.
accept: the driver log shows a detached start, the snapshot loop's own log is
non-empty, and each stage's `rc=` line is captured.

**S8 (R10, R11, R12, R13) — the verdict and the ledger.**
accept: `RESULTS.md` in this tranche carries a dated honest-ledger segment
naming the typed terminal, the `verify_root` violation count, the census's
`reach_set` count, any `E0`/`coverage == 0.5` event, and the residue. Zero
reach on both authorized attempts → both roots committed, verdict recorded,
STOP (R11).

**S9 (C2, cross-routing) — parked, never fixed here.**
accept: `PARKED.md` carries P1-epoch3 (M4's question-only amendment defect),
P2-epoch3 (M3's `amend` succeeding on a root `continue` will refuse — the
lifecycle admits an amendment it cannot continue), and P3-epoch3 (the missing
`SEAM-amendment-x-application.md`), each with a ready-to-send prompt.

---

## Assumptions (operator may override)

A1 (Q1, from M1/M2): "a second seed problem carrying its OWN
subject-substantive criteria" is delivered as far as the surface allows — a
second seed LINEAGE, criteria inherited. Smallest reading: the reach path
does not depend on the criteria differing (M9), so nothing is lost.

A2 (Q3): the sibling question stays in the urban-heat-island family and asks
about the COLLAPSE of the night-time gap under wind and cloud, so lineage-2
artifacts are plausibly on-subject for the seed's three predicates while
answering a different question.

A3: phase 1 and phase 2 split PREREG's frozen budget 12+12 cycles and
200 000+200 000 tokens rather than adding to it (R9, "PREREG's bound
stands").

A4: the amendment supplement is attached ONLY at the amendment, never at the
seed. The epoch-3 seed dossier stays empty, so phase 1 is the reach-rich
design with one manifest field moved.

A5: the epoch-3 root is a NEW root; the reach-rich roots are neither renamed
nor touched (C6). No `RUN_ALREADY_STARTED` arises because M7's manifest sha
differs.

---

## Questions for operator (asked at the LAUNCH boundary, where the credential
## is needed anyway — not blocking the offline build)

QO1: proceed with the two-phase epoch-3 ladder (second lineage, one extra
qualification battery of ~14 min / ~1160 calls, M8), or run phase 1 alone on
the UNCHANGED reach-rich manifest (a cache hit, no second lineage, but M9
says the carrier exists either way)? Recommendation: proceed with the
two-phase ladder — R1 is explicit, the added cost is one battery, and the
operator's own law prices provider calls below agent work.

---

## Out of scope (explicit)

- Fixing M4's question-only-amendment defect — not requested, and C1/C2
  forbid it. PARKED as P1-epoch3.
- Fixing M3's asymmetry (amend accepts a root continue will refuse) — PARKED
  as P2-epoch3.
- Writing `SEAM-amendment-x-application.md` — PARKED as P3-epoch3.
- Lowering `REACH_COVERAGE_MIN`, widening the qualifying vocabulary, or
  reclassifying any predicate: ruled out by the census tranche and not
  requested.
- Re-running the retired reach-rich roots, or relabelling that tranche's
  PREREG §4. Not requested; the operator holds that call.

---

## Frozen-surface contact forecast

`tools/blast_radius.py` over every planned target file, verbatim:

    {"result_type": "BLAST_RADIUS_RESULT_V1",
     "targets": {"files": [
        "experiments/2026-08-22-change-epoch3-second-lineage/epoch3_run.sh",
        "experiments/2026-08-22-change-epoch3-second-lineage/build_manifest_epoch3.py",
        "experiments/2026-08-22-change-epoch3-second-lineage/preflight_epoch3.py",
        "experiments/2026-08-22-change-epoch3-second-lineage/census_epoch3.py",
        "experiments/2026-08-22-change-epoch3-second-lineage/snapshot_loop.sh",
        "experiments/2026-08-22-live-reach-rich-run/reach_run.sh"],
      "symbols": []},
     "base": null,
     "frozen_surface_contacts": [],
     "frozen_adjacent_contacts": [],
     "reachability": [],
     "consumers": {"tests": [], "map_checks": [],
                   "qualification_digest": [], "wheel_smoke_pins": []},
     "disclosure_summary": "This change touches none of the five frozen
        surfaces. 0 test file(s) and 0 map document(s) assert on the touched
        targets today.",
     "frozen_surface_verdict": "CLEAR"}

CLEAR. No STOP is owed at this checkpoint. (`preflight_epoch3.py` and
`census_epoch3.py` were declared to the gate and are NOT authored: the
reach-rich `preflight_seed.py` and `census_new_root.py` are invoked by path
instead, which is strictly less new code. Declaring more than is written
cannot understate contact.)

Note on `consumers.qualification_digest` being empty: the gate reports no
DECLARED-FILE consumer of the qualification digest, and that is correct — no
file in the target list is read by `qualification.py`. The subject digest
still MOVES, because the digest is a function of the manifest this tranche
COMPILES at run time, not of any committed file. M8 is that measurement, and
it is stated here so the empty field is not read as "no qualification
impact".

## Blast-radius census

Tool-backed fields above are empty: `consumers.tests []`,
`consumers.map_checks []`. Manual cross-check for the shapes the gate cannot
resolve (shell invocations and string labels):

    $ grep -rn "reach_run.sh" tests/ docs/map/            -> no hits
    $ grep -rn "2026-08-22-live-reach-rich-run" tests/    -> no hits
    $ grep -rn -- "--root.*results" experiments/*/*.sh    -> reach_run.sh:101 only (M11)

EXPECTED TO MOVE: `experiments/2026-08-22-live-reach-rich-run/reach_run.sh`
line 101 (S4, the P8 fix) — its only consumer is the ladder itself.
MUST NOT MOVE: everything under `src/` and `tests/` (C1), every committed run
root (C6), `experiments/2026-08-22-live-reach-rich-run/PREREG.md` (a frozen
pre-registration; epoch 3 gets its own, S5).

## Options

- **A — amend the named root `40e713b3…`, then continue.** Files: ladder
  only. Frozen contact: none. ~120 lines. REJECTED, cites M3 (`amend_ready
  false`, `operational_failure` is not in `RESUMABLE_STOP_REASONS`), M4
  (question-only amendment ⇒ `RUN_INPUT_MISMATCH`), M5
  (`AMEND_EVIDENCE_NOT_AUTHORIZED`). Three typed refusals, all outside C1.
- **B — fresh run seeding two sibling problems from one workload spec.**
  REJECTED, cites M6: `ReasoningWorkloadSpec.problem` is singular and
  `seed_reasoning_workload` registers one problem. Needs a `src/` change
  (C1, C2).
- **C — STOP at SPEC with the capability gap.** REJECTED, cites M7: a
  vehicle exists without code changes, and R6c conditions the stop on
  NEITHER existing.
- **D — fresh run on an attached-evidence-enabled manifest; phase 1 to
  `budget_exhausted`; `amend --attach --reshape-question`; `continue`.
  CHOSEN**, cites M7 (compiles clean, zero notices), M1 (the amendment
  registers a second seed lineage), M10 (a cycle budget terminates
  resumably), and the gate test
  `test_continuation_runs_the_reshaped_question_under_the_same_root`, which
  exercises exactly this `attach=`-carrying path end to end. Files: ladder +
  builder + supplement + control. Frozen contact: none (CLEAR). ~291 lines.
  Priced risk: one extra qualification battery (M8) and a second live phase.

## Budget

Itemized: build_manifest_epoch3.py 75; supplement-nocturnal-collapse.md 25;
preflight_supplement.py 60; epoch3_run.sh 130; reach_run.sh fix 1.

    $ python3 -c "print(sum([75,25,60,130,1]))"
    291

~291 changed lines of instrument, 6+ commits (one per phase boundary).
Tranche ledger documents (REQUEST/SPEC/CHECKLIST/PREREG_EPOCH3/VALIDATION/
DELIVERY/RESULTS/PARKED) are the workflow's own record and are excluded from
this ceiling, as they are in every tranche. Frozen surfaces touched: none
(CLEAR). No split into sub-tranches is proposed: a half-built ladder mints no
evidence, and the instrument is not deliverable in halves.

Rubric: 6/6 yes — every R has an item with a machine-decidable accept
(R1/R6→S1-S3+S5, R2 is the route itself, R3/R5/R14/R15→S6, R4→S7+QO1,
R7→S4, R8→S7, R9→S3/A3, R10-R13→S8); blast-radius census pasted and every
hit classified; frozen-surface forecast recorded from the tool; the named
mechanism traced to code and its failure measured (M3/M4/M5); every claim
measured and every option priced; nothing untraceable to an R/C number.
