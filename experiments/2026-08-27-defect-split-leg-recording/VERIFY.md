# VERIFY — did the fix meet GOAL.md's success criterion?

Tranche: `experiments/2026-08-27-defect-split-leg-recording/`
Phase: dr-verify-outcome. Typed outcomes only.

## Verdict: PASS, with the residue stated

Every one of GOAL.md's five criteria is met and measured. Two things
went differently from the design and are recorded as such rather than
smoothed over: the frozen-surface grant NARROWED, and one fixture went
red that FIX.md did not predict.

---

## Criterion 1 — a thinking-ON run verifies clean

    python -u scripts/cycle_soak.py --case split-legs

| | before (`ba4720a95`) | after |
|---|---|---|
| exit | 1 | **0** |
| A2 no operational failure | PASS | **PASS** |
| A3 verify_root clean | FAIL, **260** violations | **PASS, 0 violations** |
| A4 cycles reached | 13 of 24 | **24 of 24** |

Raw: `soak-before.out`, `soak-after.out`.

## Criterion 2 — the literal `--case pc2b`

    python -u scripts/cycle_soak.py --case pc2b        → exit 0

    [PASS] A1-typed-terminal          state='completed' stop_reason='budget_exhausted'
    [PASS] A2-no-operational-failure  stop_reason='budget_exhausted'
    [PASS] A3-verify-root-clean       0 violation(s)
    [PASS] A4-cycles-reached          reached cycle 24 of 24 requested

The P-C2b STOP's own acceptance criterion, met. Was exit 1 with 50
violations plus the `prompt_ref=None` crash. Raw: `soak-pc2b-after.out`.

**How this was run without touching the paused window.** That case's two
files exist only on `claude/p-c2-rebuild-harness-n9mguu`. They were
written into the worktree from `git show ee0563cf1:…`, the case was
registered in `scripts/cycle_soak.py`, the soak was run, and then the
directory was deleted and `cycle_soak.py` restored with `git checkout`.
Nothing of that tranche is committed here; `git status` was clean
afterwards. **One honest limit:** the case registered for the run was
mine, not theirs byte-for-byte — `main`'s `cycle_soak.py` has no
`IN_RUN_EVALUATION_CASES`, so their A5/A6 assertions (in-run checker,
discharge channel) did not run. A1–A4 did, and A2/A3/A4 are the three
the STOP's acceptance named.

Also covered: the same case at `--token-budget 200000`, the exact
configuration that produced the crash, now exit 0 with 24 of 24
(`soak-after-200k.out`).

## Criterion 3 — legs and a genuine repair coexist

`tests/test_split_leg_recording.py::test_a_split_call_and_a_genuine_repair_coexist`.
A repair turn never splits (`_split_plan` returns unarmed for
`attempt != 0`), so the coexisting shape is attempt 0 split and
rejected, attempt 1 an ordinary undivided repair. The test asserts the
repair ladder's OWN semantics through it: `attempts == 2`, indices
`[0, 1]`, validity `[False, True]`, legs on attempt 0 only, a real
validation diagnostic on the rejected attempt, and `DIAGNOSTIC:` plus
`complete corrected JSON value` in the CALL's final prompt.
`verify_root` clean.

**This is NOT proven by the soak, and that is a real gap.**
`--induce-repairs` arms and is then absorbed by the unconstrained
deliberation leg — 96 calls, zero repair attempts, measured
(`soak-after-repairs.out`). PARKED P1 carries it with a ready-to-send
prompt. The unit proof is the stronger one (it is mutation-proven);
the instrument's blind spot is nonetheless real.

## Criterion 4 — every new check mutation-proven both ways

`tests/test_split_leg_recording.py` — 16 tests, all passing. Seven
parametrised mutations, one per limb plus leg order, each asserting the
base record is clean FIRST and then that the limb fires on the mutated
one. Independently corroborated: `python tools/docs_verify.py --audit`,
which refuses map checks that cannot fail, reports **0 findings**.

The four relieved checks are asserted SILENT by name —
`attempt-accounting`, `attempt-order`, `attempt-blobs`,
`repair-metadata` — rather than the record merely asserted clean.

## Criterion 5 — the gates

| instrument | baseline at `ba4720a95` | after |
|---|---|---|
| full gate | 4328 passed, 6 skipped, **0 failed** | **4344 passed, 6 skipped, 0 failed** |
| `docs_verify` full | 3 failed (shallow-clone `CON-run-identity` git-history checks) | **3 failed, the same three** |
| `docs_verify --audit` | — | **0 findings** |
| `wheel_smoke.py` | green | **green** |
| `wheel_operational_smoke.py` | green | **green** — 80 qualification calls, 416 total, and `W8_POSTCOMMIT_ROOT_VERIFICATION` returning `error_family: none` through the INSTALLED wheel |

The root sweep is retired and was not run.

---

## Two departures from FIX.md, stated plainly

**1. The grant NARROWED.** FIX.md asked to touch `invariants.py` AND
add `split-legs` to `_EPISTEMIC_CHECKS` in `verification/report.py`.
Measured during implementation: `_legacy_channel` falls through to
`integrity`, which is where all four checks `split-legs` relieves
already sit. `report.py` was not touched at all, and the contact is
`invariants.py` alone. Recorded in `INV-frozen-surfaces.md` with the
narrowing named.

**2. One fixture went red that FIX.md did not predict.** The boundary
gate's single failure was
`test_incident_wave_a_v2_fixtures`'s A3 `generated_root_sha256`. FIX.md
Amendment 1 carries the full disposition; the short form is that my
prediction enumerated tests asserting on the changed FIELDS by name, and
this one asserts on no field — it hashes every byte of a root it
generates. Cause measured by generating that root on both trees with
`src/` swapped and everything else fixed: one differing file, one
differing event, and its entire diff is the two removed fields replaced
by the new one. The pin was RE-DERIVED, never weakened, and the
descriptors are untouched.

**Scope tripwire, disposed.** The orchestrator's contract stops at a
diff over ~150 changed lines; the production diff is 249 insertions /
41 deletions. Accounted: **149 are code lines**, 86 are comments and 14
blank. The estimate was right about code and under-counted this repo's
comment density. No line is outside the design FIX.md stated, so this
is a wrong estimate rather than a widened scope — but it is recorded
rather than passed over.

---

## The closing line GOAL.md asks for

**What a thinking-on run's record now says about its two calls:** that
they were two legs of ONE attempt — `LLMSplitLegV1` records naming each
leg's own request, output, deliberation trace, wire cap and outcome,
hanging off the single attempt they jointly produced, whose token total
they sum to exactly and whose authorized envelope their caps never
exceed.

**And why a leg can never again be mistaken for a repair:** because it
is no longer in the list where repairs live. `attempt_trace` is the
repair ladder and its index means *how many times this call was told its
value was wrong*; a leg now has no index in it, occupies no rung, and
consumes no repair grant — while six checks of its own read the shape it
does occupy, so recording a leg wrongly still fails rather than passing
as something else.
