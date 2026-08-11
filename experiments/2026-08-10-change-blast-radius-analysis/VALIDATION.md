# Validation for: automatic blast-radius analysis in the skills workflow

Fresh, from-scratch re-derivation (not reuse of CHECKLIST.md's own
execution-time pasted output), per this skill's own discipline and the
X3 precedent it exists to repeat: validation-time re-derivation, not
trust of the record, is what catches a gap execution-time missed.

## Acceptance checks (SPEC.md Items S1-S9)

S1/S2 (R1, R4): tool + checkpoint design in SPEC.md's Items 1-2, built
in `tools/blast_radius.py` and three `.claude/skills/*.md` amendments.
```
$ test -f experiments/2026-08-10-change-blast-radius-analysis/SPEC.md && echo OK
OK
$ python tools/blast_radius.py --self-test
SELF-TEST PASS
```
PASS.

S3 (R2): design premise governs Item 2's grant-request checkpoint.
```
$ grep -c "Design premise, applied" experiments/2026-08-10-change-blast-radius-analysis/SPEC.md
1
```
PASS.

S4 (R3): CENSUS.md committed, contains Parts A/B/C.
```
$ test -f experiments/2026-08-10-change-blast-radius-analysis/CENSUS.md && echo OK
OK
$ grep -c "^## Part A\|^## Part B\|^## Part C" experiments/2026-08-10-change-blast-radius-analysis/CENSUS.md
3
```
PASS.

S5 (R5, Fork F4 Road B): `HIDDEN_LEGACY_INVENTORY.md` — promoted to
`docs/` per the operator-approved fork (R6), superseding SPEC.md's
original tranche-local accept text (A4's own assumption, later
overridden by the Decision sheet's own recommendation).
```
$ test -f docs/HIDDEN_LEGACY_INVENTORY.md && echo OK
OK
$ test ! -f experiments/2026-08-10-change-blast-radius-analysis/HIDDEN_LEGACY_INVENTORY.md && echo "OK (old path gone)"
OK (old path gone)
```
PASS.

S6 (C4): frozen-surface contact forecast, checked from scratch — see
4a2 below (the mechanical tripwire), re-run fresh at validation time.

S7 (C5): Decision sheet — five forks (F1-F5), each priced with a
recommendation, all marked RESOLVED with the operator's R6 citation.
```
$ grep -c "^\*\*Fork F" experiments/2026-08-10-change-blast-radius-analysis/SPEC.md
5
$ grep -c "RESOLVED" experiments/2026-08-10-change-blast-radius-analysis/SPEC.md
5
```
5 forks, 5 RESOLVED markers. PASS.

S8 (C6): commit/push discipline at every phase boundary.
```
$ git log --oneline origin/claude/blast-radius-analysis-design-3avwew..HEAD
(empty)
```
PASS — nothing unpushed at validation time.

S9 (C7): R-g and solo-law notes present in Item 1 and Item 2.
```
$ grep -c "R-g and solo law" experiments/2026-08-10-change-blast-radius-analysis/SPEC.md
3
```
PASS.

## Full gate

Re-run fresh (not reused from CHECKLIST.md step 10's own pasted
output), per this skill's own re-derivation discipline:
```
$ python -m pytest tests/ -q -n 4
1 failed, 3454 passed, 7 skipped in 918.70s (0:15:18)
FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
  assert counts["gate_blocked"] == census["streams"][stream]["gate_measures"]
  assert 159 == 165
```
Identical to CHECKLIST.md step 10's own result (same failure, same
counts, same pass/skip totals) — the re-derivation confirms no drift
occurred between execution and validation. This one failure was
verified pre-existing at CHECKLIST.md step 10 (reproduced identically
in an isolated `git worktree` at this tranche's own base commit,
`25686797`, before any of this tranche's changes — `scripts/
bronze_census.py`, `tests/test_bronze_report.py`, and `experiments/
bronze_flat_2026-07-13/` are all outside this tranche's own scope, zero
lines touched). Per this skill's own rule ("a pre-existing failure you
can prove pre-dates the change... is recorded as such and does not
block, but goes to PARKED.md"): routed to PARKED.md below, not blocking
this verdict.

Net of the one named pre-existing failure: **3454 passed, 0 failed
(caused by this tranche), 7 skipped.** PASS.

## Record-behavior preservation

n/a — this tranche touches no reader or validator of the append-only
record (`invariants.py`, `harness.py`, `capabilities/state.py`); it
adds a standalone static-analysis tool (`tools/blast_radius.py`)
operating on the git tree and filesystem, producing its own JSON result
type that is not part of the harness's own typed record. No
`verify_root` spot-check applies.

## Frozen-surface diff — the mechanical tripwire, re-run fresh

```
$ git diff --stat 25686797..HEAD -- \
    src/deepreason/capabilities/state.py src/deepreason/harness.py \
    src/deepreason/invariants.py src/deepreason/run_manifest.py \
    src/deepreason/qualification.py
(empty)
```
Empty, as forecast (SPEC.md's own "NONE — checked against
`INV-frozen-surfaces.md`'s five-item list"). PASS.

## Packaging-surface check

```
$ git diff --stat 25686797..HEAD -- pyproject.toml scripts/wheel_smoke.py scripts/wheel_operational_smoke.py
(empty)
```
Packaging surface untouched — smoke not owed (this is a recorded
decision, not an omission: `tools/blast_radius.py` READS
`pyproject.toml`'s `[project.scripts]` table at runtime for its own
wheel-smoke-pin consumer check, but never writes to it; no CLI entry
point, MCP tool, or wheel layout changed).

## Map validation

```
$ python tools/docs_verify.py
docs_verify [full]: 53 documents, 854 checks, 4 workers
  FAIL CON-run-identity.md:195/197/199 (unknown revision '1637e808', 'f304fec1')
docs_verify: 3 failed
```
3 failed, all pre-existing and unrelated: `git rev-parse
--is-shallow-repository` -> `true` (236 commits reachable); all three
checks cite historical commit hashes this shallow clone does not carry,
in `CON-run-identity.md`, a document this tranche never touches (zero
lines in the frozen-surface/map diffs above). Net of these three:
**0 failed.** PASS.

```
$ python tools/docs_verify.py --audit
docs_verify --audit: 0 finding(s)
```
PASS.

```
$ python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 53 document(s)
```
PASS.

```
$ python tools/docs_verify.py --coverage
docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 0 finding(s)
```
0 findings (the 16 "no Sweep: header" lines are the tool's own
informational "add when next touched" notes on documents this tranche
did not touch, not failures). PASS.

```
$ python tools/docs_verify.py --stale
SEAM-harness-x-verification.md: 1 commit(s) to owned files since 5d848e09
    15ba06b34 step 9-10: assemble validation_questions_tier_v.json (20 records)
docs_verify --stale: 1 document(s) worth re-reading
```
**Dismissed, with reason (state-not-silence, per this skill's own
rule):** commit `15ba06b34` is dated 2026-08-09 07:14:47 and `git
merge-base --is-ancestor 15ba06b34 25686797` confirms it PREDATES this
tranche's own base commit entirely — the staleness is pre-existing,
unrelated to `harness x verification` (a seam this tranche never
touches), and out of this tranche's own scope. Not fixed here (one
tranche, one goal); named for the operator, not silently passed over.

**New checks added by this change:** three, all in
`docs/map/INV-frozen-surfaces.md`'s new "Blast-radius gate (Rung G6)"
subsection and its backfilled Traps entry — `python -c "import ast;
ast.parse(open('tools/blast_radius.py').read())"`, `grep -q
"BLAST_RADIUS_RESULT_V1" tools/blast_radius.py`, and `grep -q
"frozen_surface_verdict" tools/blast_radius.py`. All three exercised
and passing as part of the full `docs_verify` run above (0 failed net
of the three pre-existing, unrelated failures).

**Record observables added vs. sweep probes:** none. This tranche adds
no field, record type, or finding to the harness's own append-only
typed record (`log.jsonl`/`objects/`) — `BLAST_RADIUS_RESULT_V1` is a
standalone tool result, not a harness record type, so `tools/
root_sweep.py`'s probe discipline does not apply; no probe owed.

## Requirement sweep (REQUEST.md R1-R6)

R1 (artifact): "an automatic blast radius analysis... in the skills
workflow" — demonstrated by `tools/blast_radius.py` (Rung G6,
`docs/map/INV-frozen-surfaces.md`) plus three live checkpoints wired
into `.claude/skills/dr-spec-change/SKILL.md`,
`.claude/skills/dr-ask-the-right-question/SKILL.md`, and
`.claude/skills/dr-execute-step/SKILL.md` (CHECKLIST.md steps 1, 5, 6,
7 — all checked, pasted proof).

R2 (process): the design premise (operator's self-assessment ledgered
as context; the system's own disclosure obligation as the target) —
demonstrated by SPEC.md Item 2's "Design premise, applied" subsection
and Checkpoint 2's "MUST embed... verbatim" requirement, now live in
both `dr-spec-change` step 3 and `dr-ask-the-right-question` section 4
(CHECKLIST.md steps 5-6).

R3 (artifact): Part 1 census — demonstrated by `CENSUS.md`, Part A (six
items of existing discipline) and Part B (seven failure cases, each
with what-was-authorized / what-was-undisclosed / what-blast-radius-
would-have-shown), committed `7e6e2693f`.

R4 (artifact): Part 2 design and build — demonstrated by SPEC.md Items
1-2 (design) and CHECKLIST.md steps 1-7 (build): the tool (772 lines,
20 passing tests, self-test with three mutation proofs), its map wiring
(Rung G6), its gates-ladder entry, and all three skill checkpoints.

R5 (artifact): Part 3 inventory — demonstrated by `docs/
HIDDEN_LEGACY_INVENTORY.md` (five items, the related-pattern section,
and the targeted-sweep section), promoted to a standing, repo-root
ledger location per the operator-approved Fork F4 (CHECKLIST.md step
8).

R6 (process): "Go" — the operator's approval of SPEC.md's Decision
sheet, all five recommended roads — demonstrated by REQUEST.md
Amendment 1 (verbatim), SPEC.md's five forks each marked RESOLVED with
the R6 citation, and this entire CHECKLIST.md execution (11 steps,
all checked with pasted proof) proceeding from that authorization.

All six requirements demonstrated; none deferred.

**Standing constraints (C1-C7) swept alongside:** C3 ("SPEC-AND-STOP,
no code this window") governed the capture-through-SPEC window only,
satisfied at that boundary (REQUEST.md + SPEC.md pushed, tranche
stopped) — R6's later "Go" is new, explicit operator authorization to
continue into implementation, not a violation of C3; this transition is
the reason SPEC.md's own A5 assumption ("Part 2 is a DESIGN this
window, not an implementation") reads as superseded rather than
contradicted. C4 (frozen-surface forecast checked from scratch, not
assumed) — satisfied twice: once in SPEC.md at design time, once in
this validation's own fresh re-run above. C6 (commit/push at every
phase boundary) — satisfied throughout; every CHECKLIST.md step's own
pasted proof shows a commit+push. C7 (all Operator design laws bind) —
R-g and the solo law addressed explicitly in SPEC.md Item 1 and Item 2
(S9 above).

## Assumptions carried (SPEC.md A1-A5)

A1 (Q1): the PARKED/ERRATA sweep is bounded to all 17 `docs/ERRATA.md`
entries, all 37 tranche `PARKED.md` files, and two named leads traced to
ground — stated explicitly in CENSUS.md rather than left as an
unbounded "every". Not superseded; still the operative reading.

A2 (Q2): tool CLI shape, result name (`BLAST_RADIUS_RESULT_V1`), exit
classes, and map placement (`INV-frozen-surfaces.md`'s Rung G6
subsection) — fully specified in SPEC.md Item 1, built exactly as
specified in CHECKLIST.md steps 1-3. Not superseded.

A3 (Q3): dual-granularity tool input (`--files` and `--symbols`) —
built exactly as specified. Not superseded.

A4 (Q4): `CENSUS.md`/`HIDDEN_LEGACY_INVENTORY.md` as tranche-local
documents produced alongside SPEC.md — **partially superseded**:
`CENSUS.md` remains tranche-local (unchanged); `HIDDEN_LEGACY_
INVENTORY.md` was promoted to `docs/` per Fork F4's own recommendation,
operator-approved (R6). SPEC.md's own Decision sheet names this
explicitly as "the one place this Decision sheet recommends AGAINST
what was already delivered" — the supersession was anticipated in
writing, not a surprise.

A5 (Q5): "Part 2 (R4) is a DESIGN this window, not an implementation" —
**superseded** by the operator's R6 ("Go"), which explicitly authorized
proceeding from `dr-plan-steps` through full implementation. The
assumption was correct for the window it described (the SPEC-AND-STOP
phase, C3); it does not describe this tranche's later phases, by the
operator's own later words, not by drift.

## PARKED.md (this validation's own findings)

One item, P1: the pre-existing `tests/test_bronze_report.py::
test_census_totals_internally_consistent` failure (159 vs 165
gate_blocked/gate_measures mismatch), verified to predate this
tranche's own base commit. Not this tranche's to fix (out of scope,
unrelated subsystem — `scripts/bronze_census.py`); filed in
`PARKED.md` per this skill's own routing rule ("a pre-existing
failure... goes to PARKED.md").

## Verdict: PASS

Every acceptance check (S1-S9) PASS; full gate 3454 passed, 0 failed
(caused by this tranche), 7 skipped; frozen-surface diff empty;
packaging surface untouched (recorded decision); map validation 0
failed / 0 audit findings / 0 dangling links / 0 coverage findings, one
pre-existing stale document dismissed with reason; all six requirements
(R1-R6) demonstrated with pasted evidence; all five assumptions
accounted for (three unsuperseded, two explicitly superseded by the
operator's own later words). One pre-existing, out-of-scope failure
routed to PARKED.md, not blocking.
