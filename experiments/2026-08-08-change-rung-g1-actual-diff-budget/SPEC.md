# Spec for: Rung G1 — actual-diff budget gate
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Items

S1 (R1, R2, R6): new file `tools/diff_budget.py`.
before: no gate exists; budget-vs-ceiling checks at [COMMIT] steps are
free-text prose comparisons an executor can get wrong (S5's own
history: headline 220–300 contradicted its own itemization ~325–435,
caught late).
after: `python tools/diff_budget.py <base> [--against REF] [--ceiling N]
[--paths PATH ...]` computes actual cumulative insertions (git
`--numstat`, insertions only, never deletions) between `<base>` and
either the working tree (default, matching dr-execute-step's existing
`git diff --stat <tranche-base>..HEAD` plus working-tree convention) or
`--against REF` (a second commit-ish, needed only for the historical
retrodiction demonstration in S3 below — the plan's literal CLI
`<base> [--ceiling N] [--paths ...]` covers the live/working-tree case;
`--against` is the minimal addition R10's own acceptance criterion
requires, since a historical replay cannot diff against "the working
tree"). Emits one `DIFF_BUDGET_RESULT_V1` JSON object to stdout:

    {
      "result_type": "DIFF_BUDGET_RESULT_V1",
      "base": "<base ref as given>",
      "against": "<against ref as given, or null for working tree>",
      "areas": {"<path-or-'total'>": <insertions:int>, ...},
      "total_insertions": <int>,
      "ceiling": <int|null>,
      "verdict": "WITHIN" | "EXCEEDED" | "NO_CEILING"
    }

`areas` has one key `"total"` when `--paths` is omitted, else one key
per `--paths` value (path exactly as given), insertions restricted to
that pathspec. `total_insertions` is always the sum across the whole
diff (equal to the single `"total"` value when no `--paths` given, and
independent of any double-counting from overlapping `--paths` since it
is computed once, unrestricted). `verdict` is `NO_CEILING` when
`--ceiling` is omitted, else `WITHIN` (`total_insertions <= ceiling`)
or `EXCEEDED` (`total_insertions > ceiling`) — the comparison the S5
prose check performed by hand and got right in the end, now mechanical
and against the ACTUAL diff, not a plan-time estimate.

Exit classes (Shape rules: "stable exit classes separate
result-emitted / invalid-invocation / evidence-unavailable, semantic
verdict inside the result"):
  - `0`: result emitted — JSON on stdout. True for EXCEEDED too; the
    gate reports a fact, the calling skill decides policy (Shape
    rules).
  - `2`: invalid invocation — missing `<base>`, unparseable/negative
    `--ceiling`, or an unrecognized flag. No JSON on stdout; message on
    stderr.
  - `3`: evidence unavailable — not inside a git work tree, or `<base>`
    / `--against` does not resolve to a commit. No JSON on stdout;
    message on stderr.

accept: `python tools/diff_budget.py --self-test` exits 0 and prints
`SELF-TEST PASS` (fixture-repo verdicts WITHIN / EXCEEDED / NO_CEILING,
per-area breakdown, and both non-zero exit classes, all asserted
in-process against a throwaway `git init` temp dir — see S2, which is
the same fixture logic exposed as durable pytest, not a duplicate
tool). `python -c "import ast; ast.parse(open('tools/diff_budget.py').read())"`
exits 0 (syntactically valid).

S2 (R8, R9): new file `tests/test_diff_budget.py`.
before: no test coverage for the gate (it does not exist yet).
after: permanent pytest tests against a `tmp_path` git fixture (`git
init`, configured identity, commits with known insertion counts) that
invoke `tools/diff_budget.py` as a subprocess (exercising the real CLI
contract, not internals) and assert: WITHIN verdict when actual <=
ceiling; EXCEEDED when actual > ceiling; NO_CEILING when `--ceiling`
omitted; correct per-area breakdown for two-or-more `--paths`;
`total_insertions` independent of `--paths` overlap; exit class 2 for a
missing `<base>` argument; exit class 3 for an unresolvable `<base>`
ref. One permanent companion mutation test (dr-execute-step "Durable
tests" rule 3: equality/threshold logic keeps a companion): a
fixture-repo case pinned at exactly `total_insertions == ceiling`
(the WITHIN/EXCEEDED boundary), asserting `<=` and not `<` — this is
what a `>` -> `>=` mutation in the comparison would flip, so it is the
one test in the file that a single-operator mutation is guaranteed to
kill.
accept: `python -m pytest tests/test_diff_budget.py -q` -> `N passed,
0 failed`.

S3 (R10): retrodiction demonstration against Rung S5's real history
(`54feb5cc..2e009ba7` on `origin/claude/s5-dr-plan-steps-q5utlc`) — a
`dr-execute-step`/`dr-validate-change` evidence capture, not a new file
this tranche owns, and deliberately NOT added as a permanent pytest
test: those commits live only on a feature branch this tranche does
not merge, so a fresh clone of THIS branch would not have the commit
objects, and a test pinned to unreachable commits fails exactly the
way `docs/ERRATA.md` E7 already named ("pinned to never-committed
roots, passed on one machine, failed on every fresh clone") —
recorded as Assumption A3 below.
before: no instrument would have caught S5's Amendment-2 overrun
mechanically; it was "discovered by the executor noticing, not by any
instrument" (plan text).
after: `tools/diff_budget.py 54feb5cc --against ca34dc49 --ceiling 300
--paths src/ tests/ docs/map/ tools/root_sweep.py` reports
`total_insertions: 284`, `verdict: WITHIN`; the SAME command with
`--against b0813f59` reports `total_insertions: 361`, `verdict:
EXCEEDED` — `b0813f59` is exactly the commit ("step 7-10") whose
pending [COMMIT] Amendment 2 records as where the overrun was caught
by hand ("actual `src/` + `tests/` lines already at 361 ... before
step 10's commit", REQUEST.md Amendment 2). Ceiling 300 is SPEC.md's
own upper bound ("Estimated 220-300 lines") for that tranche, the
number the record itself says the actual diff was never checked
against at commit time.
accept: both command outputs pasted in CHECKLIST.md/VALIDATION.md,
verdicts WITHIN then EXCEEDED in that order across those two specific
commits.

S4 (R3, R5): `.claude/skills/dr-spec-change/SKILL.md`, procedure step 6
("Set the budget").
before: "Set the budget: total estimated changed lines and commits. If
over ~300 lines, propose a split..." — no rule ties the headline number
to the itemization beneath it; this is the exact gap S5's Amendment 2
exploited (headline 220-300, itemization summed to 435).
after: step 6 gains one paragraph: the Budget section's headline
number(s) MUST equal the computed sum of the per-item estimates listed
in that same SPEC.md (low bound = sum of item low bounds, high bound =
sum of item high bounds), pasted as a computed arithmetic sum (e.g.
`python3 -c "print(sum([...]))"` or equivalent), never restated by
hand. Names `tools/diff_budget.py` and `DIFF_BUDGET_RESULT_V1` by exact
path/type — as the sibling instrument `dr-execute-step` runs against
this same headline once code lands (R5's "naming the tool path and
result type exactly").
accept: `grep -n "tools/diff_budget.py" .claude/skills/dr-spec-change/SKILL.md`
and `grep -n "DIFF_BUDGET_RESULT_V1" .claude/skills/dr-spec-change/SKILL.md`
both match; this SPEC.md's own Budget section (below) demonstrates the
practice (computed sum pasted).

S5 (R4, R5): `.claude/skills/dr-execute-step/SKILL.md`, step 6 (the
`[COMMIT]`/budget-ceiling paragraph landed by the precedent tranche
`2026-08-05-change-budget-ceiling-at-commit`).
before: "before committing, compare the tranche's ACTUAL changed lines
(`git diff --stat <tranche-base>..HEAD` plus the working tree) against
SPEC.md's budget ceiling. Exceeding the ceiling is a STOP..." — a
prose comparison the executor performs by reading `git diff --stat`
output and doing the arithmetic themselves.
after: the paragraph is rewritten to invoke `tools/diff_budget.py
<tranche-base> --ceiling <SPEC.md's ceiling> --paths <SPEC.md's
declared areas>` and read its `DIFF_BUDGET_RESULT_V1.verdict` field
directly: `WITHIN`/`NO_CEILING` -> continue; `EXCEEDED` -> the STOP,
in the standard format (decision, priced options, recommendation),
raised at the commit that crosses the line — unchanged in spirit from
the existing paragraph, now backed by the gate's own JSON instead of
manual arithmetic. Names `tools/diff_budget.py` and
`DIFF_BUDGET_RESULT_V1` exactly.
accept: `grep -n "tools/diff_budget.py" .claude/skills/dr-execute-step/SKILL.md`
and `grep -n "DIFF_BUDGET_RESULT_V1" .claude/skills/dr-execute-step/SKILL.md`
both match; step 6's EXCEEDED-is-a-STOP sentence survives verbatim in
spirit (still a STOP, still the standard format).

S6 (R7): `docs/map/INV-frozen-surfaces.md` — new subsection after "The
two instruments that prove you did not break anything", naming a third:
the diff budget gate. Two `check:` lines mirroring `tools/root_sweep.py`'s
own pattern (syntactic validity + a content grep proving the file is
the real tool and not a stub), so `docs_verify` holds this gate's
existence the way it holds every other claim (Shape rules: "a `check:`
line in the relevant map document").
before: no map document names `tools/diff_budget.py`.
after: new subsection with `check: python -c "import ast;
ast.parse(open('tools/diff_budget.py').read())"` and `check: grep -q
"DIFF_BUDGET_RESULT_V1" tools/diff_budget.py`.
accept: `python tools/docs_verify.py` -> `0 failed`, including the two
new checks; `docs/map/INDEX.md`'s subsystem/invariant tables need no
change (`INV-frozen-surfaces.md` is already indexed there).

S7 (R12, Q1): `PARKED.md` in this tranche directory.
before: no record of the `.claude/skills/README.md` discrepancy (task
instruction names a file that does not exist in this repo).
after: one entry, WHAT + a ready-to-send follow-up prompt, per
`dr-change-orchestrator`'s park-time discipline. Not fixed this
tranche (C1: scope is G1 alone).
accept: `PARKED.md` exists and contains the entry.

S8 (R11): full gate + docs_verify at the tranche's delivery boundary.
before: N/A (validation-phase obligation, not a file change).
after: `python -m pytest tests/ -q -n 4` -> `0 failed` net of the named
pre-existing P1/P3 (`tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`,
confirmed present on the PRISTINE base commit before this tranche
touched anything — see Measurements below, resolving Q3); `python
tools/docs_verify.py` -> `0 failed`.
accept: both commands' tail output pasted in VALIDATION.md.

S9 (R13): commit-and-push discipline at every phase boundary.
before: N/A (process obligation).
after: one commit per phase (REQUEST.md, SPEC.md, CHECKLIST.md, each
executed step, VALIDATION.md, DELIVERY.md), each pushed with the
4x-retry backoff (2s/4s/8s/16s) on failure.
accept: `git log --oneline <tranche-start>..HEAD` shows one commit per
phase/step; each push in the session transcript succeeded (directly or
after retry).

S10 (R14): deliver through `dr-validate-change` then `dr-deliver-change`.
before: N/A (process obligation; already implied by routing table).
after: VALIDATION.md (verdict PASS) precedes DELIVERY.md; DELIVERY.md
carries the R-by-R reconciliation table.
accept: both files exist, in that order by commit history.

S11 (R15, R16, R17 — already discharged, recorded here for
traceability, no further action): branch based on
`origin/claude/monitor-session-handover-63ajqv` (head verified
`d4f63007`), session preflight run (`deepreason` importable), routed
through `dr-change-orchestrator` starting at `dr-capture-request`.
accept: already satisfied — `git rev-parse
origin/claude/monitor-session-handover-63ajqv` = `d4f630075...` (this
session's preflight, pasted above in-session); `pip show deepreason`
succeeded; REQUEST.md exists (this tranche).

## Assumptions (operator may override)

A1 (Q2): "area" is not defined by the plan beyond the CLI's own
`[--paths ...]`. Assumed, smallest reading: an area is exactly one
caller-supplied `--paths` value (a git pathspec), reported verbatim as
the `areas` dict key; omitting `--paths` yields one area, `"total"`,
covering the unrestricted diff. No auto-derived grouping (e.g.
"top-level directory") is invented — the plan's own example
(`src/+tests/+docs/map/+tools/root_sweep.py` combined, S5 Amendment 2)
is caller-specified path prefixes, not a derived scheme.

A2 (Q3): the "named pre-existing P1/P3" (R11) is
`tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`,
confirmed by running the full gate on the pristine base commit (this
session's baseline, before any tranche file existed): `1 failed, 3382
passed, 7 skipped` — the same single failure, same test id, and the
same `3382 passed` count Rung S5's own VALIDATION.md recorded net of
P1/P3 ("Net of P1/P3: 3382 passed, 0 failed"), confirming this is the
SAME already-tracked defect (`P1/P3` across Rungs S1-S5's own
PARKED.md files), not a new one. Not this tranche's finding; not fixed
(C1, C4).

A3 (S3's own text): the retrodiction demonstration (R10) is captured
as pasted CHECKLIST/VALIDATION evidence, not a permanent pytest test,
because its input commits (`54feb5cc`..`2e009ba7`) are reachable only
via `origin/claude/s5-dr-plan-steps-q5utlc`, a branch this tranche does
not merge; a permanent test pinned to them would pass in this session
(which fetched that branch) and fail on any fresh clone that has not
— the exact failure mode `docs/ERRATA.md` E7 already names. The
FIXTURE-repo tests in S2 give the same verdict logic permanent,
durable coverage; S3 additionally proves it against the real recorded
overrun, once, on the record.

## Questions for operator (STOP if non-empty)

(none — both open questions from REQUEST.md resolved as Assumptions
above; neither forks the implementation by file, behavior, or >2x
effort)

## Out of scope (explicit)

- Rungs G2-G5 of the pre-plan (mutation attestation, census manifest,
  final-tree evidence, premise-currency) — not requested (C1).
- Per-area ceilings (a ceiling per `--paths` value rather than one
  total ceiling) — not requested; the plan's own example and S5's own
  precedent both check ONE combined ceiling across areas.
- Wiring the gate into a git hook or CI check — not requested; the
  plan places it inside `dr-execute-step`'s existing manual procedure.
- Retroactively running the gate against any tranche other than S5's
  named retrodiction range — not requested.
- Fixing the `.claude/skills/README.md` discrepancy (Q1) — PARKED
  (S7), not fixed (C1, C4).
- Fixing the `P1/P3` pre-existing failure — PARKED already, in four
  prior tranches' own PARKED.md files; not this tranche's finding (C4,
  A2).

## Frozen-surface contact forecast

none expected — checked against `docs/map/INV-frozen-surfaces.md`'s
five surfaces (`capabilities/state.py`, `harness.py`, `invariants.py`
+ `verification/`, `run_manifest.py` schemas+validators,
`qualification.py`) and the frozen-adjacent `llm/firewall.py
route_fingerprint`. This tranche's file list — `tools/diff_budget.py`,
`tests/test_diff_budget.py`, `.claude/skills/dr-spec-change/SKILL.md`,
`.claude/skills/dr-execute-step/SKILL.md`,
`docs/map/INV-frozen-surfaces.md` (additive subsection only, no
existing header/check touched), this tranche's own `PARKED.md` — none
is a frozen surface or a file under `src/deepreason/`. Zero `src/`
contact (R6), confirmed by construction: no spec item names a `src/`
path.

## Blast-radius census

`grep -rn "diff_budget" tests/ docs/map/ .claude/skills/` -> no hits
(new symbol; the new test file and map subsection introduce the only
references).
`grep -rn "DIFF_BUDGET_RESULT_V1" tests/ docs/map/ .claude/skills/` ->
no hits (new symbol).
`grep -rln "dr-spec-change" tests/ docs/map/` -> no hits (nothing
outside the skill's own file asserts on its content).
`grep -rln "dr-execute-step" tests/ docs/map/` -> no hits.
`grep -rln "budget ceiling\|Budget ceiling" tests/ docs/map/` -> no
hits.
`grep -rn "INV-frozen-surfaces" tests/ docs/map/` -> 18 hits, all
`DR-INV-frozen-surfaces` cross-links from other map documents (SEAM-*,
SUB-*, CON-*) -> MUST NOT MOVE, and none do: the doc's `<!-- DR-INV-
frozen-surfaces -->` id, its existing `Owns:`/header lines, and every
existing `##`/`check:` line are unchanged; the new subsection is
purely additive at the end of the file.

## Budget

Itemized (low-high insertions):
S1 `tools/diff_budget.py`: 130-170
S2 `tests/test_diff_budget.py`: 140-190
S4 `dr-spec-change` amendment: 15-25
S5 `dr-execute-step` amendment: 15-25
S6 `INV-frozen-surfaces.md` addition: 10-15
S7 `PARKED.md`: 8-12

Computed sum (`python3 -c "print(sum([130,140,15,15,10,8]),
sum([170,190,25,25,15,12]))"` -> `318 437`):

**Headline: 318-437 insertions, ceiling 450, across
`tools/`+`tests/`+`.claude/skills/`+`docs/map/`+this tranche's own
experiments dir, ~6-8 commits (one per phase boundary plus one per
CHECKLIST step group).** Frozen surfaces touched: none.

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept: yes (R1-R17
  all appear in S1-S11 above; R15-R17 marked already-discharged with
  their own accept evidence)
- blast-radius census pasted (or pasted-empty) and every hit
  classified: yes
- frozen-surface contact forecast recorded: yes (none expected)
- every mechanism the request names traced to code it actually
  reaches: yes (the CLI signature `<base> [--ceiling N] [--paths ...]`
  is the literal plan text; `--against` is the one addition, justified
  in S1/S3 by R10's own acceptance requirement, not invented scope)
- DESIGN-AND-STOP only: n/a, not a DESIGN-AND-STOP request
- nothing in the spec untraceable to an R/C number: yes (anti-invention
  pass complete; Out of scope lists the nearest tempting neighbors)
