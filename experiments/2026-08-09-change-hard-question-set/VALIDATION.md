# Validation for: the two-tier hard question set

Every check below was RE-RUN independently against the actual committed
state at HEAD (branch `claude/hard-question-set-x7q2mn`), not read off
CHECKLIST.md's own notes.

## Acceptance checks

S1 (R3/R4/R11, Tier V schema+count): `python
experiments/2026-08-09-change-hard-question-set/schema_check.py
experiments/validation_questions_tier_v.json --kind both` ->
`PASS: experiments/validation_questions_tier_v.json (20 records,
kind=both)` : **PASS**

S2 (R3/R7/R11, Tier O schema+count): `python
experiments/2026-08-09-change-hard-question-set/schema_check.py
experiments/validation_questions_tier_o.json --kind open` ->
`PASS: experiments/validation_questions_tier_o.json (10 records,
kind=open)` : **PASS**

S3 (R6, checkers exist and run): `ls experiments/tier_v_checkers/*.py |
wc -l` -> `20`. Spot-check re-run: `python
experiments/tier_v_checkers/tv-m01_checker.py 44` -> `PASS 44`;
`python experiments/tier_v_checkers/tv-c05_checker.py` (no args, runs
against its own embedded reference solution) -> `PASS` : **PASS**

S4 (R10, PREREG.md exists and precedes pilot output): file exists.
Commit ordering re-verified: PREREG.md committed `9ba61633a`
2026-08-09T07:18:35Z; the first pilot-tier-v run-root file committed
in `c992489402` 2026-08-09T07:26:26Z — PREREG.md precedes by ~8
minutes : **PASS**

S5 (R13, both pilot run roots committed with a typed end state):
`tier-v-driver.log` ends `=== pilot-tier-v end
2026-08-09T07:54:47Z ===`; `tier-o-driver.log` ends `=== pilot-tier-o
end 2026-08-09T08:36:32Z ===`. `git ls-files
experiments/2026-08-09-change-hard-question-set/pilot-tier-v/runs/ |
wc -l` -> 1688 tracked files; `.../pilot-tier-o/runs/` -> 2252 tracked
files : **PASS**

S6 (R18, PARKED.md non-empty): `wc -l PARKED.md` -> 96 lines, 2 dated
findings each with a ready-to-send prompt : **PASS**

S7 (R19/R20, RESULTS.md dated honest ledger): `wc -l RESULTS.md` ->
147 lines, dated `## 2026-08-09` segment header, corpus summary,
failure ledger, both pilots' typed outcomes, explicit
proved/not-proved residue section, gemma-sole-model answer : **PASS**

## Full gate

Re-run independently (not reused from CHECKLIST step 27):

    1 failed, 3434 passed, 7 skipped in 672.41s (0:11:12)

Identical counts to the CHECKLIST step 27 run (681.13s vs 672.41s —
timing varies, counts do not). The one failure is
`tests/test_bronze_report.py::test_census_totals_internally_consistent`,
`assert 159 == 165` on stream `deepseek-v4-pro` — byte-identical
assertion to the one named in
`experiments/2026-08-08-parked-bronze-census-env/PARKED.md`, committed
2026-08-08T21:29:25Z (`b8e66ea50`), a full commit BEFORE this
tranche's own base commit `64743bac7` (2026-08-09T07:07:21Z).
Pre-existing-ness confirmed by an even stronger method than the
prescribed `git stash`/rerun: `git diff --stat
64743bac7..HEAD -- tests/test_bronze_report.py
scripts/bronze_census.py experiments/bronze_flat_2026-07-13/` is
EMPTY — this tranche's diff touches NONE of the files the census
reader depends on, so it cannot be the cause. Routed to the
already-existing PARKED.md (not re-parked by this tranche; it was
already parked before this tranche began). `jsonschema` (the other
named known-environment item) is installed and passing.

**Verdict: PASS** (0 failed net of the pre-existing, provably
unrelated, already-parked item).

## Record-behavior preservation

n/a — this tranche adds no reader/validator/writer of the append-only
record; `src/`, `tests/`, `tools/` are byte-untouched (see Frozen
surfaces below). No `verify_root` behavior changed. The two LIVE
pilot runs each ran their own `verify_root` (via `pilot_audit.py`)
against roots THIS tranche created, not against any pre-existing
root — both came back clean by their final audit (`replay_valid:
true`, 0 violations) after an initial transient `foreign-criticism`
finding, documented and PARKED, not smoothed over.

## Frozen surfaces

    git diff --stat 64743bac7..HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py \
      src/deepreason/qualification.py

Output: **(empty)** — no frozen surface touched. **PASS**

## Scope lock (R18, full-tranche invariant)

    git diff --stat 64743bac7..HEAD -- src/ tests/ tools/

Output: **(empty)** across the WHOLE tranche (28 steps, ~30 commits),
not just per-commit. **PASS**

## Packaging surface

Untouched — no `pyproject.toml`, CLI entry point, MCP surface, or
wheel-layout change in this tranche. **Smoke not owed** (recorded
decision, not an omission).

## Map

    docs_verify: 53 documents, 851 checks, 0 failed : PASS
    docs_verify --audit: 0 finding(s) : PASS
    docs_verify --links: 0 dangling reference(s), 53 document(s) : PASS
    docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 0 finding(s) : PASS
      (the 16 "no Sweep: header" seams are pre-existing advisory notes,
      unrelated to any seam this tranche touches — this tranche
      touches no docs/map/ document at all)
    docs_verify --stale: 33 document(s) worth re-reading

**--stale dismissal, all 33 entries, single reason applying to every
one:** this tranche made ZERO commits to any file under `src/`
(confirmed above, Scope lock), so it cannot be the cause of any of the
listed subsystem documents' staleness, and updating documents this
tranche did not touch is out of its own scope (R18). Each of the 33
entries predates this tranche's base commit `64743bac7` and belongs to
whichever prior tranche last touched that subsystem's owned files —
dismissed here as not-this-tranche's-responsibility, not silently
ignored.

**New checks for added behavior:** none — this tranche adds no `src/`
behavior, only data files under `experiments/` plus documentation.
Nothing falsifiable-about-the-harness was added; the falsifiable
claims this tranche DOES make (checker correctness, Tier O openness,
pilot typed outcomes) are proven by CHECKLIST.md's own pasted
evidence, not by a `docs/map/` check, since they are not claims about
`src/` behavior.

**Record observables added vs sweep probes:** none — this tranche
adds no new typed-record field, event type, or finding. The two live
runs exercise entirely EXISTING harness mechanisms (conjecture,
criticism, qualification, `verify_root`, `findings`) unchanged.

**Wheel smoke:** packaging surface untouched — smoke not owed.

## Requirement sweep

R1 (deliver the corpus): demonstrated by S1+S2 (both files exist,
schema-valid, correct counts).
R2 (difficulty target: gemma4:31b-class): demonstrated by A2's
sourcing design (SPEC.md) plus the two live pilots' n=1 evidence
(Tier V checker no-match, Tier O junk-acceptance) — both consistent
with, not proof of, the calibration; RESULTS.md states this honestly
as unproven residue.
R3 (existing validation_questions*.json format, extended): demonstrated
by S1+S2's schema (id/q preserved, new fields added per SPEC.md's R3/R11
section).
R4 (Tier V 20-30 problems, hard math+coding, competition not research):
demonstrated by S1 (20 records: 10 math + 10 coding).
R5 (licensing binding, MIT/Apache confirmed, source+license recorded):
demonstrated by both draft-authoring CHECKLIST steps (3-4) citing the
live-confirmed MIT license for Hendrycks MATH and OpenAI HumanEval;
every record in S1's file carries `source`+`license`.
R6 (checkers must actually run before commit): demonstrated by
CHECKLIST steps 6-7's pasted execution output (all 20, known-answer
PASS + wrong-answer FAIL mutation-proof) plus S3's independent re-run.
R7 (Tier O 10-15 problems, own words + attribution + URL): demonstrated
by S2 (10 records, each with `attribution`/`source_url`).
R8 (verify still open, cite where/when checked): demonstrated by
CHECKLIST step 11's independent re-verification pass (2026-08-09,
including the Lonely Runner k<=12 correction found during that pass);
every S2 record carries `still_open_verified`.
R9 (prefer computable finite special cases): demonstrated by S2's
`computable_special_case` field, honestly stated per-problem (6 of 10
genuinely decidable single checks, 4 honestly framed as bounded
search rather than overstated).
R10 (Tier O epistemic hygiene metric, prereg'd before pilot): demonstrated
by S4 (PREREG.md exists, precedes pilot output) and its live application
(Tier O pilot's JUNK-ACCEPTANCE verdict, CHECKLIST step 22).
R11 (per-problem metadata both tiers): demonstrated by S1+S2's schema
(id/tier/statement/source+license-or-attribution/verification, checker
committed beside the Tier V set).
R12 (credential handling): demonstrated by CHECKLIST step 17 (env
written, chmod 600, confirmed gitignored and never staged across the
whole tranche — reconfirmed by `git log --all` never showing the file
tracked).
R13 (two live pilot runs, proven recipe): demonstrated by both pilots'
driver logs (S5) and CHECKLIST steps 19/22's full cycle-budget
exhaustion (10 + 2 + 2 cycles each).
R14 (sole-model gemma, no seat flags): demonstrated by both
`pilot_tier_*_run.sh` scripts (no `--seat` flag present) and both
runs' qualification/reason output showing `model_id: gemma4:31b`
throughout.
R15 (gemma-sole-model calibration bonus, full vs shallow): demonstrated
— both pilots independently qualified at **full** tier (reproduced
twice), answering the operator's standing question; no `--shallow`
retry branch fired in either run.
R16 (pilot judging discipline, typed outcomes only): demonstrated by
`pilot_audit.py`'s design (reads only run-status.json/verify_root/
findings --json) and its proven-before-live-use test against an
existing committed root (CHECKLIST step 18).
R17 (no-key fallback): not exercised — REQUEST.md's Q1 resolved the
key was present; the fallback branch is documented but untested by
this tranche (a legitimate deferral, not a gap — the operator's own
words in this session confirmed the key was provided).
R18 (scope lock, PARKED discipline, failure budget 6): demonstrated
above (Scope lock: empty diff) and by PARKED.md (2 findings) plus
RESULTS.md's failure ledger (0/6 spent).
R19 (full gate once at boundary, known exceptions named): demonstrated
above (Full gate section) — run TWICE independently (CHECKLIST step 27
and this validation phase) with identical counts both times.
R20 (deliver through dr-validate-change/dr-deliver-change, honest
RESULTS.md): this document + RESULTS.md.
R21 (commit/push discipline with retry): demonstrated by every
CHECKLIST step's pasted commit hash and the final clean-tree check
(CHECKLIST step 28) — every push in this tranche's history succeeded
on the first attempt (no retry was ever needed, backoff logic was
present but unexercised).

C1 (tokens cheap, agent not — prefer live evidence): honored — the
Tier O hygiene question was answered by an actual live run, not
reasoned about offline; checkers were RUN, not just written.
C2 (formalism is an option, never an obligation): honored — neither
tier's schema nor scoring rule requires or rewards formal commitment;
Tier V's `accept`/checker mechanism is a ground-truth check on the
ANSWER, not a formality requirement on how it was derived; Tier O's
hygiene metric penalizes ONLY false-resolution claims, never
penalizes informality.
C3 (scope hard: src/tests/tools untouched): demonstrated above (Scope
lock section, empty diff across the whole tranche).

## Assumptions carried (SPEC.md A1-A5)

A1: one representative question per tier run live, not the full
corpus (`deepreason reason` takes one question at a time).
A2: difficulty established by SOURCE (MATH Level 4-5 split;
hand-picked non-trivial HumanEval problems), not by a live per-problem
probe — falsifiable by, not proven by, the pilot's own n=1 results.
A3: Tier V sized to the low end of R4's range (20, not up to 30).
A4: Tier O sized to the low end of R7's range (10, not up to 15).
A5: pilot model config (context=131072, completion=8192,
reasoning=none) reused from `easy.py`'s own proven `"gemma4_31b"`
preset rather than guessed.

## Verdict: PASS
