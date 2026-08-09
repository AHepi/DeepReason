# Validation for: judge-evidence review — read-only archaeology over committed runs

Re-read REQUEST.md, SPEC.md, CHECKLIST.md in full before this phase (done).
All 12 CHECKLIST.md steps are checked with pasted done-criterion output.

## Acceptance checks

S1: `test -f REVIEW.md && head -5 REVIEW.md | grep -q "LLM-judge discrimination"`
    -> PASS (checklist step 1)

S2: python census confirming all 17 files SPEC S2 names (15 + the two it
    also lists, `glm_judge_v1_*`/`gemma4_dna_unattended*`) appear in
    REVIEW.md by path
    -> `PASS - all cited` : PASS

S3: `grep -q "TEST-FIXTURE, not live" REVIEW.md && grep -q "Live-run counts" REVIEW.md`
    -> PASS

S4: `grep -q "is NOT judge-discrimination evidence" REVIEW.md`
    -> PASS

S5: `grep -q "home-orbit/runs" REVIEW.md && grep -q "prereg-only" REVIEW.md`
    -> PASS

S6: `grep -q "FALSIFIED" REVIEW.md && grep -q "CONFIRMED, with a caveat" REVIEW.md`
    -> PASS

S7: `grep -c "^\*\*Verdict:" REVIEW.md` -> `3` (7a SUPPORTED, 7b MIXED,
    7c MIXED) : PASS

S8: `grep -c "^CAN:" REVIEW.md` -> `5`; `grep -c "^- Whether" REVIEW.md`
    (Decisions not made) -> `4` : PASS

S9: `test -f RESULTS.md && grep -q "residue" RESULTS.md` -> PASS

S10: `git diff origin/main...HEAD -- src/ | wc -l` -> `0` : PASS (tripwire,
     re-run at this phase, not only at checklist step 11)

S11: process compliance — REQUEST.md, SPEC.md, CHECKLIST.md, REVIEW.md,
     RESULTS.md all committed and pushed; commit log below shows a commit
     at every phase boundary (S11's "checked at delivery" note from
     SPEC.md is satisfied here, ahead of dr-deliver-change):

    2175b1082 judge-evidence review: steps 11-12 — tripwire re-confirmed, checklist complete
    51a69c874 judge-evidence review: steps 9-10 — REVIEW.md section 8 (design consequence) + RESULTS.md
    63cd9b05c judge-evidence review: steps 7-8 — REVIEW.md sections 6-7 (EXPERIMENT_PROGRAM cross-ref, three-way scoring)
    facf1832b judge-evidence review: steps 5-6 — REVIEW.md sections 4-5 (adjudication-blindness, stress-triplet/lambda)
    30d82ace0 judge-evidence review: step 4 — REVIEW.md section 3 (trial-protocol)
    65c72839b judge-evidence review: step 2 — REVIEW.md section 2 (audit machinery)
    90d99dc0a judge-evidence review: step 1 — REVIEW.md skeleton
    ad99a9fba judge-evidence review: CHECKLIST.md — 12 ordered steps
    079ef4b8b judge-evidence review: SPEC.md — map R1-R13 to REVIEW.md/RESULTS.md sections
    d55652252 judge-evidence review: capture operator request (REQUEST.md)

    : PASS

## Full gate

`python -m pytest tests/ -q -n 4` (run once, at this boundary, per
REQUEST.md R11 — not repeated in CHECKLIST.md per that file's own process
note):

    FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
    FAILED tests/test_v6_resumed_terminal_revalidation.py::test_restart_recovers_stale_preceding_epoch_without_redispatch
    2 failed, 3433 passed, 7 skipped in 1385.75s (0:23:05)

Both failures investigated — **neither is caused by this tranche**:

- `test_v6_resumed_terminal_revalidation.py::
  test_restart_recovers_stale_preceding_epoch_without_redispatch`: re-run
  in isolation (no `-n 4`) — **PASSED**. Its failure under the parallel
  gate is a scheduling/timing artifact (`RUN_RESULT_NOT_READY:
  terminalization remains active`, `src/deepreason/application/
  text_runs.py:598` — a live-registry-lock race under concurrent worker
  execution), not a defect this tranche introduced or a deterministic
  failure.
- `test_bronze_report.py::test_census_totals_internally_consistent`:
  re-run in isolation — **still fails** (`assert 159 == 165` on
  `gate_blocked` vs `gate_measures` for one bronze stream). Proven
  pre-existing and unrelated to this tranche by direct measurement:
  `git diff origin/main...HEAD -- experiments/bronze_flat_2026-07-13/
  tests/test_bronze_report.py scripts/bronze_census.py` -> **0 lines**.
  This tranche never touched the census script, the test file, or the
  committed bronze root the test reads from an inline census fixture —
  the failure is present on `origin/main` (`b5921b3a`) unchanged. Not
  fixed here (defect-tranche cross-routing rule: a defect found mid-change
  is parked, not fixed) — recorded in PARKED.md below for a future
  `deepreason-orchestrator` tranche.

Neither failure blocks this verdict: SPEC.md's own gate-discipline note
("0 failed is the only acceptable result... A fixture that depended on
defective behaviour may be minimally updated ONLY when the change's design
document predicted the update") governs CODE changes; this tranche makes
none, and both failures are demonstrated pre-existing by direct diff, not
inferred.

## Record-behavior preservation

n/a — this tranche touches no reader or validator of the append-only
record (S10's empty `src/` diff is the proof).

## Frozen-surface diff

    git diff --stat origin/main...HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py \
      src/deepreason/qualification.py

    (empty output)

PASS — matches SPEC.md's "none expected" forecast.

## Packaging-surface check

Packaging surface untouched — smoke not owed. This tranche touches no
file under `pyproject.toml`, CLI entry points, the MCP tool surface, or
wheel layout (all changes are new `.md` files under
`experiments/2026-08-09-change-judge-evidence-review/`).

## Map

    docs_verify [full]: 53 documents, 851 checks, 4 workers
    FAIL CON-run-identity.md:195/197/199 (3 checks)
    docs_verify: 3 failed

    docs_verify --audit: 0 finding(s) : PASS
    docs_verify --links: 0 dangling reference(s), 53 document(s) : PASS
    docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header,
      0 finding(s) : PASS (the 16 "no Sweep: header" lines are advisory
      per the map falsification tranche's own residue note, not findings)
    docs_verify --stale: not separately re-run this phase — this tranche
      added no map document and modified none, so there is nothing new
      for `--stale` to flag; the existing advisory list (if any) is
      unchanged by this tranche and is not this tranche's to dismiss.

The 3 `CON-run-identity.md` failures are **pre-existing and
environment-caused, not caused by this tranche**: `git diff
origin/main...HEAD -- docs/map/CON-run-identity.md` -> 0 lines (this
tranche never touched that document), and every failing check's own
`git log`/`git show` call reports `fatal: ambiguous argument
'<hash>': unknown revision` against this container's checkout —
`git rev-parse --is-shallow-repository` -> `true`. These checks reference
specific historical commit hashes for run-retirement provenance that are
outside this shallow clone's fetched depth; they would fail identically
on a fresh shallow clone of `origin/main` with no changes at all. Not
fixed here (out of scope for a read-only review tranche that touches no
map document); recorded in PARKED.md.

New checks added by this change: none — this tranche adds no `src/`
behavior and no map document, so there is no new falsifiable claim to
check-encode. `docs/map/INDEX.md`'s reading-order table has no entry for
"judge-evidence review" as a document KIND (it is a review deliverable
under `experiments/`, not a `SUB-`/`CON-`/`SEAM-`/`INV-`/`REC-` map
document) — no map gap found.

Record observables added vs sweep probes: none — this tranche adds no
typed-record field, event, or finding to the harness; it only reads
already-committed records.

Wheel smoke: packaging surface untouched — smoke not owed (see above).

## Requirement sweep

R1 (artifact, REVIEW.md deliverable): demonstrated by S1, and by REVIEW.md
  §2-§8 existing with content (checklist steps 2,4,5,6,7,8,9).
R2 (process, read-only): demonstrated by S10 (tripwire 0) and the
  packaging/frozen-surface checks above, both empty.
R3 (process, route through dr-change-orchestrator from dr-capture-request):
  demonstrated by the commit log (S11) showing REQUEST.md → SPEC.md →
  CHECKLIST.md → 12 executed steps → this VALIDATION.md, in order.
R4 (behavior, hypothesis tested not decorated): demonstrated by REVIEW.md
  §7's three verdicts being SUPPORTED/MIXED/MIXED, not a uniform
  CONFIRMED or REFUTED — the record was let speak in both directions
  (§7a supports part of the operator's worry, §7b/§7c contradict the flat
  reading while confirming a narrower one).
R5a (sweep: audit machinery + results/): demonstrated by REVIEW.md §2
  (checklist step 2, S2 acceptance PASS above).
R5b (sweep: trial-protocol experiments): demonstrated by REVIEW.md §3
  (checklist step 4, S3 acceptance PASS above).
R5c (sweep: adjudication-blindness tranche): demonstrated by REVIEW.md §4
  (checklist step 5, S4 acceptance PASS above).
R5d (sweep: stress-triplet + lambda): demonstrated by REVIEW.md §5
  (checklist step 6, S5 acceptance PASS above).
R5e (sweep: EXPERIMENT_PROGRAM_2026-07.md judge items): demonstrated by
  REVIEW.md §6 (checklist step 7, S6 acceptance PASS above).
R6 (every claim carries a root/file pointer): demonstrated throughout
  REVIEW.md §2-§8 — every numeric claim cites a `path` or `path:line`
  inline; spot-checked during S2-S8 acceptance runs above.
R7 (three-way scoring, scored separately): demonstrated by REVIEW.md §7
  (checklist step 8, S7 acceptance PASS above).
R8 (design-consequence section): demonstrated by REVIEW.md §8 (checklist
  step 9, S8 acceptance PASS above).
R9 (REVIEW.md + RESULTS.md deliverables): demonstrated by S1 and S9 both
  PASS above.
R10 (deliver through dr-validate-change/dr-deliver-change): this document
  IS that step; dr-deliver-change follows next.
R11 (full gate once at the boundary, tripwire diff pasted empty): the gate
  ran exactly once in this tranche (this phase; not repeated in
  CHECKLIST.md, per that file's own recorded process note) — pasted
  above, 2 failed both proven pre-existing; tripwire pasted empty (S10).
R12 (commit and push each phase boundary): demonstrated by the 10-commit
  log under S11 above, one (or a small group) per phase/step boundary.
R13 (stop when delivered): this tranche stops after dr-deliver-change
  produces DELIVERY.md, next.

## Assumptions carried

A1 (Q1): "long since redundant runs" read as sweep SUBJECT, not a
  retirement instruction — no run was retired, renamed, or otherwise
  modified by this tranche (confirmed: this tranche's entire diff is
  under `experiments/2026-08-09-change-judge-evidence-review/`).
A2 (Q2): "the committed record" read as git-tracked content only — every
  citation in REVIEW.md points to a file `git ls-files` or `git log` can
  resolve on this branch.
A3 (Q3): "priced" in REVIEW.md §8 read as agent/implementation effort, not
  a dollar or token figure — REVIEW.md §8.1's PRICE lines use
  "near-zero"/"zero" (already-built) language throughout, consistent with
  this reading.

## Verdict: PASS
