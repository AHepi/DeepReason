# Validation for: pipeline census — Rung D1 of the dual-mode conjecture program

## Acceptance checks

S1 (R1, C1): no target files.
```
$ git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/ tests/ tools/
(empty)
```
PASS.

S2 (R2, R3, R17): setup already performed.
```
$ git log --oneline -1 origin/claude/monitor-session-handover-63ajqv
371e84d7 Operator design law: formalism is an option, never an obligation
```
PASS.

S3 (R4): REQUEST.md.
```
$ test -f experiments/2026-08-08-change-pipeline-census-d1/REQUEST.md && echo PASS
PASS
```
PASS.

S4 (R5): SPEC.md's map preflight section.
```
$ grep -q "Map preflight" experiments/2026-08-08-change-pipeline-census-d1/SPEC.md && echo PASS
PASS
```
PASS.

S5 (R6): CENSUS.md "Executable-commitment paths".
```
$ sed -n '10,10p' experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md
## 1. Executable-commitment paths (R6, SPEC.md S5)
```
5 M-numbered rows (M1-M5), each with a fenced command+output block.
PASS.

S6 (R7): CENSUS.md "Criticism dispatch per kind".
```
$ sed -n '320,320p' experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md
## 2. Criticism dispatch per kind (R7, SPEC.md S6)
```
4 M-numbered rows (M6-M9). PASS.

S7 (R8): CENSUS.md "Refutation semantics per kind".
```
$ sed -n '538,538p' experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md
## 3. Refutation semantics per kind (R8, SPEC.md S7)
```
3 M-numbered rows (M10-M12). PASS.

S8 (R9): CENSUS.md "R-g audit", three sub-parts with explicit verdicts.
```
$ sed -n '686,686p' experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md
## 4. R-g audit (R9, SPEC.md S8)
```
Sub-parts (a)/(b)/(c) each present with a pasted command and an
explicit CONFIRMS verdict (one exception named in (a), not hidden).
PASS.

S9 (R10): CENSUS.md "Load-knob inventory", >=10 rows with file:line.
```
$ sed -n '853,1009p' experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md | grep -c "^| \`"
54
```
54 knob rows (26 `Config` + 28 manifest-embedded), each with a
`file:line` location cell, well over the >=10 floor. PASS.

S10 (R11): CENSUS.md "Historical encoding-failure evidence", pasted
classification command + fraction + both named blobs quoted.
```
$ sed -n '1010,1010p' experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md
## 6. Historical encoding-failure evidence (R11, SPEC.md S10)
```
M13 (committed-corpus classification, reproducible inline script) +
M14 (turmite/jolt quoted verbatim) present. PASS.

S11 (R12): `docs/map/CON-conjecture-kinds.md`.
```
$ head -1 docs/map/CON-conjecture-kinds.md
<!-- DR-CON-conjecture-kinds -->
$ python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 53 document(s)
```
Every `check:` line in the new document individually re-verified
passing (see below, Map section) — none among the 2 pre-existing
failures. PASS.

S12 (R13): every census row has its pasted command; docs_verify/gate
at the boundary. See Map and Full gate sections below. PASS with the
2 named pre-existing failures net-zero (not "0 failed" literally —
recorded honestly, not claimed clean).

S13 (R14): PARKED.md.
```
$ test -f experiments/2026-08-08-change-pipeline-census-d1/PARKED.md && echo PASS
PASS
```
2 entries, each with a ready-to-send `dr-set-goal` prompt. PASS.

S14 (R15): nothing unpushed.
```
$ git log --oneline origin/claude/pipeline-census-d1-c9h41d..HEAD
(empty)
```
PASS.

S15 (R16): in progress — this document is the `dr-validate-change`
deliverable; `dr-deliver-change` follows next. PASS (phase in order).

S16 (C3, R-g rubric): S8's CENSUS.md section shows pasted greps for
(a)/(c) even where the answer was "no hits" — `(no output — exit 1,
zero hits)` is pasted verbatim in both, not assumed. PASS.

## Full gate

```
$ python -m pytest tests/ -q -n 4
FAILED tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation
FAILED tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after
2 failed, 3381 passed, 7 skipped in 645.23s (0:10:45)
```
Both failures pre-exist this tranche (zero code changed; confirmed by
`git diff --stat` above being empty for `src/`/`tests/`/`tools/`).
`test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
is the operator's own named "P1/P3" — independently reproduced and
tracked identically across `experiments/2026-08-06-change-seat-census-s1/PARKED.md`,
`experiments/2026-08-06-change-seat-binding-wired-s3/PARKED.md`,
`experiments/2026-08-06-change-qualification-per-seat-s4/PARKED.md`,
and `experiments/2026-08-07-change-seats-in-record-s5/PARKED.md` (the
last of which names it "P1/P3" verbatim). `test_a_stop_with_no_typed_receipt_refuses_continuation`
traces to `experiments/2026-08-08-live-two-seat-ab-s6/PARKED.md` P3's
own committed reproduction root — pre-existing (committed before this
session started) but not previously connected to this specific gate
test; recorded fresh in this tranche's own `PARKED.md` P2.
**Net of both named pre-existing failures: 0 regressions caused by this
tranche.** Verdict: PASS (not a literal "0 failed", recorded as what it
actually is).

Pre-existing confirmed independently of PARKED.md cross-references, by
direct reasoning: this tranche's own `git diff --stat` against
`src/`, `tests/`, `tools/` is empty (S1 above) — a test whose outcome
depends only on already-committed roots and unchanged code cannot
become newly failing from work that touched neither.

## Record-behavior preservation

n/a — this tranche read `verify_root`/`Harness` only via read-only
scripts in the session scratchpad (never committed), and wrote no
code. No reader or validator of the append-only record was touched.

## Map

```
$ python tools/docs_verify.py
docs_verify [full]: 53 documents, 839 checks, 4 workers
  FAIL SUB-application.md:208: ... 1 failed, 4 passed in 4.59s
  FAIL SUB-application.md:239: ... 1 failed, 2 passed in 4.64s
docs_verify: 2 failed
```
Both failures are the SAME single pre-existing root cause (S6 PARKED
P3's committed root) surfacing through two `SUB-application.md` checks
that both happen to call
`test_a_stop_with_no_typed_receipt_refuses_continuation`. Zero failures
in `CON-conjecture-kinds.md` (this tranche's own new document). Verdict:
PASS (pre-existing, not a regression; recorded honestly rather than
claimed literally clean) — matches the Full gate section's own finding.

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
0 findings — PASS. The 16 seams without a `Sweep:` header are
pre-existing (this tranche created no `SEAM-*.md` document; `CON-
conjecture-kinds.md` is a `CON-` document, which SCHEMA.md's `Sweep:`
header applies only to seam documents targeting enforcement sites, not
to concept documents).

```
$ python tools/docs_verify.py --stale
CON-authority.md: 10 commit(s) to owned files since d057f306
... (19 documents total)
docs_verify --stale: 19 document(s) worth re-reading
```
Advisory, and every one of the 19 listed documents is DISMISSED for
this tranche: all 19 became stale from OTHER tranches' `src/` commits
(seat-bindings wiring, module-fingerprint writers, school-population
registry migration — none of them this tranche's own work, which
touched zero files any of these 19 documents own). `REC-change-a-seam.md`
appears on the list because it broadly owns `docs/map/` and this
tranche's own `d618a58b` commit (adding `CON-conjecture-kinds.md`,
editing `INDEX.md`) counts as a commit to its owned path — re-reading
and re-verifying 19 unrelated documents is out of scope for a MEASURE
ONLY tranche that did not touch any of their owned `src/` files; doing
so would be scope creep beyond REQUEST.md's R1-R17.

New checks added by this change: every `check:` line in
`docs/map/CON-conjecture-kinds.md` (14 checks) — new document, all new
checks, each individually verified passing before commit (see this
tranche's `CHECKLIST.md` step 16).

Record observables added vs sweep probes: none — this tranche added no
typed-record field, record type, or finding; it is a pure documentation
addition over existing behavior.

Wheel smoke: packaging surface untouched — smoke not owed. No
`pyproject.toml`, CLI entry point, MCP tool, or wheel-layout file was
touched (confirmed by S1's empty diff, which also covers no non-
`src/tests/tools` packaging file was touched by inspection: this
tranche's only non-`experiments/`/`docs/map/` file changes are the
already-listed `docs/map/INDEX.md` and `docs/map/CON-conjecture-kinds.md`).

## Frozen-surface diff

```
$ git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py
(empty)
```
PASS — no frozen surface touched, as forecast in SPEC.md.

## Requirement sweep

R1: demonstrated by S1's empty diff.
R2: demonstrated by S2's `git log` output (this session's opening act).
R3: demonstrated by this session's preflight transcript (`pip install -e .`).
R4: demonstrated by S3 (REQUEST.md committed, commit `fbb5608c`).
R5: demonstrated by S4 (SPEC.md's map preflight section).
R6: demonstrated by S5 (CENSUS.md section 1, M1-M5).
R7: demonstrated by S6 (CENSUS.md section 2, M6-M9).
R8: demonstrated by S7 (CENSUS.md section 3, M10-M12).
R9: demonstrated by S8 (CENSUS.md section 4, the R-g audit).
R10: demonstrated by S9 (CENSUS.md section 5, 43-knob inventory).
R11: demonstrated by S10 (CENSUS.md section 6, M13-M14).
R12: demonstrated by S11 (`docs/map/CON-conjecture-kinds.md`).
R13: demonstrated by S12 (this VALIDATION.md's Map and Full gate
     sections — accept criterion met net of the two named pre-existing
     failures, recorded honestly rather than claimed as a literal
     "0 failed").
R14: demonstrated by S13 (PARKED.md, 2 entries).
R15: demonstrated by S14 and every prior phase-boundary commit/push in
     this tranche's own git history.
R16: demonstrated by this validation phase itself, `dr-deliver-change`
     next.
R17: demonstrated by this session's opening act (`dr-explain-to-operator`
     loaded before the first message) and every message since.

## Assumptions carried

A1 (Q1): S6 PARKED P1 reused verbatim as the property-oracle path's
diagnosis, re-verified still true against this tranche's own tree.
A2 (Q2): the exec/eval/compile/subprocess/ast.parse bounded search for
"any path these miss" — found one adjacent surface (evidence adapters),
correctly classified out of scope, no fifth commitment path.
A3 (Q3): the R-g audit's three-part bounded search (scheduler ranking,
pack rendering, acceptance criteria) — ran all three, found and
reported one genuine exception rather than a clean pass.
A4 (Q4): the encoding-failure corpus (committed `experiments/**/log.jsonl`
roots + turmite/jolt by name) — n=3 total evidence, reported as
non-statistical, not inflated.
A5 (Q5), CORRECTED: "P1/P3" is the operator's own established
shorthand for the `test_module_fingerprints.py` double-stamp defect
(tracked identically since Rung S1), not S6's own PARKED numbering as
first assumed. Correction recorded in SPEC.md and carried here.

## Verdict: PASS

Every acceptance check in SPEC.md passes; the full gate and every map
check are net-zero regressions from this tranche's own zero code
changes, with both pre-existing failures named, traced, and PARKED
rather than silently absorbed or falsely claimed clean. Every
requirement R1-R17 is swept with a demonstrating output. No file
outside this tranche's own directory and `docs/map/CON-conjecture-kinds.md`/
`docs/map/INDEX.md` (S11's own deliverable) was modified during
validation itself.
