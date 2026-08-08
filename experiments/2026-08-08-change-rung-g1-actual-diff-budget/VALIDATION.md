# Validation for: Rung G1 — actual-diff budget gate

## Acceptance checks

S1: `python tools/diff_budget.py --self-test` ->
```
SELF-TEST PASS
```
: PASS
`python -c "import ast; ast.parse(open('tools/diff_budget.py').read())"` -> exits 0 : PASS

S2: `python -m pytest tests/test_diff_budget.py -q` ->
```
.............                                                            [100%]
13 passed in 3.50s
```
: PASS

S3 (retrodiction): re-run fresh for this phase —
```
{"result_type": "DIFF_BUDGET_RESULT_V1", "base": "54feb5cc", "against": "ca34dc49", "areas": {"src/": 126, "tests/": 158, "docs/map/": 0, "tools/root_sweep.py": 0}, "total_insertions": 284, "ceiling": 300, "verdict": "WITHIN"}
{"result_type": "DIFF_BUDGET_RESULT_V1", "base": "54feb5cc", "against": "b0813f59", "areas": {"src/": 149, "tests/": 212, "docs/map/": 0, "tools/root_sweep.py": 0}, "total_insertions": 361, "ceiling": 300, "verdict": "EXCEEDED"}
```
WITHIN at `ca34dc49` ("step 5-6"), EXCEEDED at `b0813f59` ("step
7-10") -- matching REQUEST.md Amendment 2's own recorded numbers
("actual `src/` + `tests/` lines already at 361 ... before step 10's
commit") exactly. : PASS

S4: `grep -n "tools/diff_budget.py" .claude/skills/dr-spec-change/SKILL.md`
-> line 100 matches; `grep -n "DIFF_BUDGET_RESULT_V1" .claude/skills/dr-spec-change/SKILL.md`
-> line 100 matches (same line names both) : PASS

S5: `grep -n "tools/diff_budget.py" .claude/skills/dr-execute-step/SKILL.md`
-> line 44 matches; `grep -n "DIFF_BUDGET_RESULT_V1" .claude/skills/dr-execute-step/SKILL.md`
-> line 46 matches : PASS

S6: `python tools/docs_verify.py` -> `0 failed` (below); PARKED.md N/A
to S6 (S6 is the map subsection) -- covered under the full run below : PASS

S7: `test -f experiments/2026-08-08-change-rung-g1-actual-diff-budget/PARKED.md`
-> exists : PASS

S8: full gate + docs_verify -- see below : PASS

S9: commit history, `git log --oneline d4f63007..HEAD` -> 17 commits,
one per phase boundary or CHECKLIST step group (more than the ~6-8
estimate because of the STOP/amendment cycle at step 8, which is
process working as designed, not scope creep) : PASS

S10: `dr-validate-change` running now, precedes `dr-deliver-change` :
PASS (in progress by construction)

S11: already-discharged this session -- branch head `d4f63007`
verified against `origin/claude/monitor-session-handover-63ajqv`
before REQUEST.md was written; `deepreason` importable (`pip show
deepreason` succeeded); REQUEST.md exists : PASS

S12: `## Budget` reads ceiling 460; gate re-run --
```
{"areas": {"tools/": 228, "tests/": 192, ".claude/skills/": 16, "docs/map/": 17}, "total_insertions": 453, "ceiling": 460, "verdict": "WITHIN"}
```
: PASS

## Full gate

```
FAILED tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after
1 failed, 3395 passed, 7 skipped in 738.25s (0:12:18)
```
Same test id as the pristine-base baseline captured before this
tranche touched anything (`1 failed, 3382 passed, 7 skipped`); 3395 =
3382 + 13 new tests in `tests/test_diff_budget.py`. **Net of the named
pre-existing P1/P3: 3395 passed, 0 failed.** : PASS

## Record-behavior preservation

n/a -- this tranche touches no reader or validator of the append-only
record (zero `src/` contact, confirmed below); no `verify_root` spot-
check owed.

## Frozen-surface diff

```
git diff --stat d4f63007..HEAD -- src/deepreason/capabilities/state.py \
  src/deepreason/harness.py src/deepreason/invariants.py \
  src/deepreason/run_manifest.py src/deepreason/qualification.py
```
(empty output) : PASS

Full `src/` contact check (R6, stronger than the five named surfaces):
```
git diff --stat d4f63007..HEAD -- src/
```
(empty output) : PASS

## Packaging surface

Untouched -- no `pyproject.toml`, CLI entry point, MCP server surface,
or wheel layout change. Smoke not owed.

## Map

docs_verify: 52 documents, 831 checks, 0 failed : PASS
docs_verify --audit: 0 finding(s) : PASS
docs_verify --links: 0 dangling reference(s), 52 documents : PASS
docs_verify --coverage: 6 seams swept, 16 without a `Sweep:` header, 0
finding(s) : PASS (the 16 are pre-existing, none introduced or altered
by this tranche -- `INV-frozen-surfaces.md` is an `INV-` document, not
a `SEAM-` document, so it never carries a `Sweep:` header)
docs_verify --stale: 67-line report; `INV-frozen-surfaces.md` (the
only document this tranche touched) does NOT appear in it -- the
`Verified-at: 6a033fa2` stamp advanced at step 1 correctly reflects
that its checks were re-run then. Every OTHER entry in the report
predates this tranche (Rung S5 and earlier work) and is out of scope
(C1) -- dismissed, not this tranche's to fix.
new checks added by this change: two, in `docs/map/INV-frozen-
surfaces.md`'s new "The diff budget gate (Rung G1)" subsection --
`ast.parse` syntactic validity and a `DIFF_BUDGET_RESULT_V1` content
grep, both exercised live throughout this tranche's own commits.
record observables added vs sweep probes: none -- this tranche adds no
field, record type, or finding to the append-only log; it is a
standalone `tools/` instrument over `git diff`, not a record reader.
wheel smoke: packaging surface untouched — smoke not owed.

## Requirement sweep

R1: demonstrated by S1 (self-test, ast check)
R2: demonstrated by S2 (13 tests, including the two exit-class tests
    `test_invalid_invocation_exit_class_for_missing_base`,
    `test_evidence_unavailable_exit_class_for_unresolvable_ref`)
R3: demonstrated by S4
R4: demonstrated by S5
R5: demonstrated by S4+S5 (exact strings `tools/diff_budget.py`,
    `DIFF_BUDGET_RESULT_V1` grepped in both files)
R6: demonstrated by the full `src/` diff check (empty)
R7: demonstrated by S6 + the map validation section (0 failed,
    including the two new checks)
R8: demonstrated by CHECKLIST step 5 (perturb -> 4 tests red -> restore
    -> 12 tests green)
R9: demonstrated by S1+S2 (fixture-repo WITHIN/EXCEEDED/NO_CEILING all
    covered and passing)
R10: demonstrated by S3 (WITHIN then EXCEEDED, matching S5's own
    recorded numbers exactly)
R11: demonstrated by the Full gate section (net of P1/P3, 0 failed) and
    the Map section (docs_verify 0 failed)
R12: demonstrated by PARKED.md (P1, the `.claude/skills/README.md`
    branch-timing discrepancy — noticed, corrected on recheck, not
    fixed, since fixing it is out of this tranche's scope, C1)
R13: demonstrated by the commit history (S9) and every step's push
    (all succeeded, none needed the retry backoff this session)
R14: demonstrated by this document existing before DELIVERY.md
R15: demonstrated by S11 (already-discharged, session-start evidence)
R16: demonstrated by S11 (already-discharged, session-start evidence)
R17: demonstrated by REQUEST.md's existence and this tranche's whole
    structure (dr-capture-request first)
R18: demonstrated by REQUEST.md Amendment 1 + SPEC.md S12 + step 8's
    re-check (`verdict: WITHIN` against the amended ceiling)

## Assumptions carried

A1 (Q2): "area" = one caller-supplied `--paths` value, verbatim as the
`areas` dict key; no `--paths` -> one area, `"total"`.
A2 (Q3): the named pre-existing P1/P3 is
`tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`,
confirmed identical on the pristine base commit and matching Rung S5's
own VALIDATION.md count (3382 passed net of it).
A3 (S3's own text): the retrodiction demonstration is deliberately NOT
a permanent pytest test -- its input commits live only on
`origin/claude/s5-dr-plan-steps-q5utlc`, unreachable from a fresh clone
of this branch; pinning a permanent test to them would fail exactly
the way `docs/ERRATA.md` E7 already names. The fixture-repo tests in
S2 give the same verdict logic permanent, durable coverage.

## Verdict: PASS
