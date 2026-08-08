# Validation for: Rung O1 of the grounded-overlay program — offline retrodiction

## Acceptance checks

S1 (R1, R2, R3): setup already performed this session.
```
$ git log --oneline -1 origin/claude/monitor-session-handover-63ajqv
2b0b108c Pre-plan: grounded-extension overlays (offline retrodiction first)
```
PASS.

S2 (R4): REQUEST.md.
```
$ test -f experiments/2026-08-08-change-grounded-overlay-o1/REQUEST.md && echo PASS
PASS
```
PASS.

S3 (R5): zero `src/`/`tests/`/`tools/` diff.
```
$ git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/ tests/ tools/
(empty)
```
PASS.

S4 (R6, R11): read-only-only Harness usage, no provider/LLM import.
```
$ grep -rn "Harness(" experiments/2026-08-08-change-grounded-overlay-o1/scripts/*.py
overlay_common.py:23:    return Harness(root, read_only=True)
$ grep -rln "llm\.\|ollama\|adapter\." experiments/2026-08-08-change-grounded-overlay-o1/scripts/*.py
(no hits, exit 1)
```
The one call site every other script imports from (`overlay_common.
open_root`) is read-only. PASS.

S5 (R7): `o1a_semantics_diff.py` — syntax + independent Dung-semantics
sanity checks (CHECKLIST.md step 3).
```
$ python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/o1a_semantics_diff.py').read())"
(exit 0)
```
PASS.

S6 (R7 continuation, C3): TOO_LARGE guardrail.
```
$ python3 experiments/2026-08-08-change-grounded-overlay-o1/scripts/check_o1a_too_large_guardrail.py
TOO_LARGE reported for component size 20 in 0.0002s
```
PASS.

S7 (R8): `o1b_joint_execution_probe.py` syntax.
```
$ python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/o1b_joint_execution_probe.py').read())"
(exit 0)
```
PASS.

S8 (R9): `o1c_floating_foundations.py` syntax.
```
$ python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/o1c_floating_foundations.py').read())"
(exit 0)
```
PASS.

S9 (R10): `o1d_warrant_sensitivity.py` syntax.
```
$ python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/o1d_warrant_sensitivity.py').read())"
(exit 0)
```
PASS.

S10 (shared): driver + `overlay_results.jsonl`.
```
$ python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/run_all_overlays.py').read())"
(exit 0)
$ wc -l experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl
48 experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl
```
48 lines, matching the corpus count from `overlay_common.corpus()`.
PASS.

S11 (R12): `REPORT.md`.
```
$ grep -c "^### M" experiments/2026-08-08-change-grounded-overlay-o1/REPORT.md
7
```
7 M-numbered claims (M1-M7) across the four overlay sections, each
with a pasted command + real output, plus the 48-row per-root table.
PASS.

S12 (R12): `RESULTS.md` residue.
```
$ grep -q "consistency patrol" experiments/2026-08-08-change-grounded-overlay-o1/RESULTS.md && echo PASS
PASS
```
PASS.

S13 (R13): zero-diff tripwire, full gate, docs_verify conditional.
```
$ git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/ tests/ tools/
(empty)
$ python -m pytest tests/ -q -n 4
3400 passed, 7 skipped in 666.16s (0:11:06)
```
Zero failures — the program's own stated new baseline, confirmed
directly. `docs_verify` is n/a: no map document was created (S16).
PASS.

S14 (R14): PARKED.md / no-defects statement.
```
$ test -f experiments/2026-08-08-change-grounded-overlay-o1/PARKED.md && echo "exists" || echo "absent (expected)"
absent (expected)
$ grep -q "No defects found this tranche" experiments/2026-08-08-change-grounded-overlay-o1/RESULTS.md && echo PASS
PASS
```
PASS.

S15 (R15): nothing unpushed.
```
$ git log --oneline origin/claude/grounded-overlay-rung-o1-4hkuoo..HEAD
(empty)
```
PASS.

S16 (R12's conditional, R13): map document decision.
```
$ test -f docs/map/CON-grounded-overlays.md && echo exists || echo "not created"
not created
$ grep -n "No new map document" experiments/2026-08-08-change-grounded-overlay-o1/RESULTS.md
130:## No new map document
$ git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- docs/map/
(empty)
```
No new map document — RESULTS.md's own section states why (the map's
charter, per `docs/map/INDEX.md`'s "Coverage, stated honestly" section,
describes `src/deepreason/` only; this rung owns no `src/` file).
`docs/map/` itself is untouched, confirming the decision was actually
followed through, not just stated. PASS.

S17 (R16): in progress — this document is the `dr-validate-change`
deliverable; `dr-deliver-change` follows next. PASS (phase in order).

## Full gate

```
$ python -m pytest tests/ -q -n 4
3400 passed, 7 skipped in 666.16s (0:11:06)
```
0 failed. This IS the program's new baseline (P1/P3 both fixed on this
branch, per `experiments/2026-08-08-fix-module-fingerprints-double-
stamp/RESULTS.md` and `experiments/2026-08-08-fix-l1-continue-
resumable-crash/RESULTS.md`, both merged before this branch's own
base `2b0b108c`) — confirmed directly by this tranche's own boundary
run, not assumed from those tranches' prior claims. Environment note,
not a defect: `pytest`/`jsonschema`/`pytest-xdist` were installed
locally (uncommitted) before the gate could run — the same
undeclared-dev-extra gap `experiments/2026-08-08-change-pipeline-
census-d1/PARKED.md` already names; `pyproject.toml` untouched.
Verdict: PASS.

## Record-behavior preservation

n/a — this tranche read `Harness`/`verify_root`-adjacent state only via
`Harness(root, read_only=True)` in tranche-directory scripts (never
committed as a reader change), and wrote no code under `src/`. No
reader or validator of the append-only record was touched; every root
this tranche opened is unmodified (confirmed by S3/S13's own empty
`src/`/`tests/`/`tools/` diffs, and by `git status --porcelain` never
showing any `experiments/**/log.jsonl`/`objects/`/`blobs/` path as
changed throughout the tranche's own commit history).

## Frozen-surface diff

```
$ git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py
(empty)
```
PASS — no frozen surface touched, as forecast in SPEC.md.

## Packaging-surface check

Packaging surface untouched — smoke not owed. No `pyproject.toml`,
CLI entry point, MCP tool, or wheel-layout file was touched (confirmed
by the tranche-wide diff below, which shows only files under
`experiments/2026-08-08-change-grounded-overlay-o1/`).

```
$ git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- . ':!experiments/2026-08-08-change-grounded-overlay-o1/'
(empty)
```

## Map

n/a — no map document was created or edited this tranche (S16); no
`docs/map/` file appears in the tranche-wide diff above.
`docs_verify` was not run because there is nothing new for it to
check; RESULTS.md's "No new map document" section is the recorded
reasoning per `dr-validate-change`'s own instruction that a skip must
be a recorded decision, not an omission.

New checks added by this change: none — the TOO_LARGE guardrail
(`scripts/check_o1a_too_large_guardrail.py`) is a tranche-directory
script, not a `docs/map/` check (there is no map document for it to
attach to, per S16's own reasoning).

Record observables added vs sweep probes: none — this tranche added no
typed-record field, record type, or finding; it computes derived
overlays over existing `att`/`dep`/`warrants`/`status` fields, all
already read by `tools/root_sweep.py` and documented in `DR-CON-
warrants-and-attacks`/`DR-SUB-adjudication`.

Wheel smoke: packaging surface untouched — smoke not owed (see
Packaging-surface check above).

## Requirement sweep

R1: demonstrated by this session's opening branch verification
    (`git log --oneline -1 origin/claude/monitor-session-handover-63ajqv`
    -> `2b0b108c`, matching the task's own stated head).
R2: demonstrated by this session's opening preflight transcript
    (`pip install -e . --break-system-packages -q`).
R3: demonstrated by this session's opening reads of CLAUDE.md,
    `dr-explain-to-operator/SKILL.md`, and `.claude/skills/README.md`.
R4: demonstrated by S2 (REQUEST.md, committed `70dcfb30`) and this
    validation phase itself, both routed through `dr-change-orchestrator`.
R5: demonstrated by S3/S13's empty `src/`/`tests/`/`tools/` diffs.
R6: demonstrated by S4 (read-only-only `Harness` usage, no provider/LLM
    import) and R11's own reuse of `Harness`/`build_att`/`label0`/
    `final_labels`/`formally_backed`/`oracle.run` rather than a hand
    parser.
R7: demonstrated by S5/S6 (`o1a_semantics_diff.py`, TOO_LARGE guardrail)
    and REPORT.md M1/M2 (zero controversy across the corpus).
R8: demonstrated by S7 (`o1b_joint_execution_probe.py`) and REPORT.md
    M3/M4 (zero comparable pairs, excluded remainder reported honestly).
R9: demonstrated by S8 (`o1c_floating_foundations.py`) and REPORT.md
    M5/M6 (14 multi-node floating chains found and named).
R10: demonstrated by S9 (`o1d_warrant_sensitivity.py`) and REPORT.md
    M7 (zero single-warrant flips across the corpus).
R11: demonstrated by S4's grep and by every overlay script's own
    imports (`from deepreason.adjudication...`, `from deepreason.
    rules.warrants import formally_backed`, etc.) rather than any
    hand-rolled `log.jsonl` parser.
R12: demonstrated by S10/S11/S12 (`overlay_results.jsonl`, REPORT.md,
     RESULTS.md's residue section).
R13: demonstrated by S13 (this document's own Full gate section — 0
     failed, the program's new baseline).
R14: demonstrated by S14 (no defects found, no PARKED.md; RESULTS.md's
     own statement).
R15: demonstrated by S15 and every prior phase-boundary commit/push in
     this tranche's own git history (14 commits from REQUEST.md through
     CHECKLIST.md's completion).
R16: demonstrated by this validation phase itself; `dr-deliver-change`
     next.

## Assumptions carried

A1 (Q1): SCC controversy inventory = SCCs of `att` containing >=1
`label0=="suspended"` node.
A2 (Q2): preferred-extension computation implemented offline via the
standard Dung reduction (grounded extension subset of every complete
extension), 16-node-per-component brute-force cap, typed TOO_LARGE
beyond it.
A3 (Q7): P1/P3 fixed — confirmed directly by this tranche's own
boundary gate run (0 failed), not merely cited from prior tranches.
A4 (Q4): machine-comparable input gates = same-problem, identical-
entry, `program:exec_oracle`-class commitment pairs only — found to
exclude the entire corpus (REPORT.md M3/M4), a genuine finding about
this program's own committed data, not a design flaw.
A5 (Q5): ground = `Provenance.role in {SEED, IMPORT, USER}`.
A6 (Q6a): single-warrant sensitivity only; multi-warrant minimal sets
deferred, named as residue.
A7 (Q8): corpus = every `experiments/**/log.jsonl` root (48 total, 11
pre-v6 ERROR, matching `tools/root_sweep.py`'s own documented
baseline).

## Verdict: PASS

Every acceptance check in SPEC.md passes; the full gate is genuinely
green (3400 passed, 0 failed, 7 skipped) — the program's own stated
new baseline, confirmed directly rather than assumed; every requirement
R1-R16 is swept with a demonstrating output; zero `src/`/`tests/`/
`tools/` diff throughout; no frozen surface touched; no file outside
this tranche's own directory was modified. The one design decision this
phase re-confirms rather than merely re-states: no new map document was
warranted, and `docs/map/` itself is untouched, proving the decision
was followed through.
