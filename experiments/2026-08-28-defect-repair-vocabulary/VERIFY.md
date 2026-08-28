# Verify: the repair `mode` vocabulary is one shared type, and epoch 5's payload shape now survives

## The question the operator asked, answered first

**Does a re-run of epoch 5's payload shape now survive? YES — offline, at the
call site the record names, driven end to end rather than asserted.**

`tests/test_v6_repair_mode_vocabulary.py::
test_whole_object_syntax_repair_child_recovers_instead_of_killing_the_run`
builds a decomposition child whose repair payload carries
`mode: "whole_object_syntax"`, `authorized_pointers: []`, `repair_index: 1` —
the exact structural signature the audit's census records for all 36
whole-object payloads across the three committed roots — and drives it through
`recover_atomic_child_output`, the function
`experiments/2026-08-27-change-technique-run/failed-epoch5-run-456885c5.../
run-result.json` identifies by its own decomposition shape. Before the fix that
call raised `NonConjectureRecoveryAuthorityError("repair mode is invalid")`
from `nonconjecture_recovery.py:1002`. After it, the child is admitted and its
candidate compiled.

**What this does NOT establish, stated plainly.** No live run has been
executed. What is proven is that the payload SHAPE that killed epoch 5 is now
recovered rather than refused, at the call site the record and the traceback
agree on. A live re-run could still die of something else — epoch 5 was a
cross-family, judge-bearing configuration and this tranche touched none of
that. The claim here is bounded to the vocabulary.

## Success criteria from GOAL.md, one by one

**(1) The regression test — PASS.**

    python -m pytest tests/test_v6_repair_mode_vocabulary.py -q
    -> 7 passed

Seven tests, not the four GOAL.md forecast: three were added during
implementation for the new mode/pointer-agreement check and the writer
guarantee it rests on (FIX.md Amendment 2). Mutation-proven in BOTH
directions, output recorded:

  - pre-fix tree (REPRO.md): `3 failed, 1 passed` — the epoch-5 shape raised
    `NonConjectureRecoveryAuthorityError("repair mode is invalid")` at
    `atomic_recovery.py:69`, and the `patch` sibling passed in the same run of
    the same file, so the rejection was on the mode string and nothing else.
  - agreement check replaced with `True` on the fixed tree: `2 failed, 5
    passed` (one direction reports "repair envelope pointers differ" instead;
    the other stops raising at all). Restored: `7 passed`.

**(2) The reader consumes the producer's type by import — PASS.**

    python -c "... 'V6_REPAIR_TASK_MODES' in inspect.getsource(
                    nonconjecture_recovery._repair_authority)"
    -> exits 0

**(3) `full` is gone from the authority boundary — PASS.**

    grep -n '"full"' src/deepreason/workflow/nonconjecture_recovery.py
    -> no match (exit 1)

**(4) The soak can provoke a repair, in the mode that matters — PASS, with
one measured limitation recorded below.** Three runs, all `--case epoch3
--cycles 8 --induce-repairs 2`, all exit 0:

| `--induce-repair-kind` | induced | D1 disposition | `repair_payloads` | `repair_modes` |
|---|---|---|---|---|
| `invalid` (default, pre-existing behaviour) | `ReasoningConjecturerTurnWireV6` | covered | 1 | `["patch"]` |
| `unparseable` (new) | `ReasoningConjecturerTurnWireV6` | covered | 1 | `["whole_object_syntax"]` |
| `alternate` (new) | `ReasoningConjecturerTurnWireV6` | covered | 1 | `["whole_object_syntax"]` |

The middle row is the point: `whole_object_syntax` — the mode that killed
epoch 5 — is recorded offline for the first time. The `invalid` row is the
pre-existing instrument, unchanged, confirming the default path did not move.

**Limitation, measured not assumed: `alternate` degenerated to `unparseable`
on this case.** It alternates per INDUCED TITLE, and the epoch3 run induces
only one distinct wire schema title, so the second kind is never reached. It
is not broken — it needs a case whose run dispatches two or more distinct wire
schemas (`pr1`, with cross-family seats and a judge ensemble, is the obvious
candidate) — but on `epoch3` it buys nothing over `unparseable`, and no run in
this tranche has demonstrated it driving both modes. Recorded as residue, not
as a working feature.

**(5) The full gate — PASS.**

    python -m pytest tests/ -q -n 4
    -> 4381 passed, 6 skipped in 783.31s (0:13:03)
    -> 0 FAILED

Baseline was 4374 passed; the delta is exactly the 7 new tests. This gate ran
on the committed tree for everything pytest exercises. Two files changed after
it started — `scripts/cycle_soak.py` (D1's predicate) and `docs/ERRATA.md` —
and neither is imported by any test (`grep -rln cycle_soak tests/` returns one
docstring mention in `test_split_leg_recording.py` and nothing more), so the
result stands for the tree as committed. Stated rather than assumed, because
"the gate was green at some point" is not the same claim as "the gate is green
on this tree".

**(6) `docs_verify` — PASS, exactly at baseline.**

    python tools/docs_verify.py   -> 68 documents, 1133 checks, 4 failed
        CON-run-identity.md:200, :202, :204   (3 x shallow clone: "unknown
                                               revision" — the container has
                                               no history for 1637e808 /
                                               f304fec1)
        INV-frozen-surfaces.md:181            (the pre-existing falsified
                                               transport_failure census)
    python tools/docs_verify.py --audit  -> 0 finding(s)
    python tools/docs_verify.py --links  -> 0 dangling reference(s)

**Delta beyond four, found and closed — my own, and worth recording as a
trap for the next runner.** An intermediate state of this tranche showed SIX
failures: `SEAM-harness-x-workflow.md:43` and `SEAM-scratch-x-workflow.md:44`
had gone red. Neither is about this defect. Both end in TEXT CENSUSES —
`for f in $(grep -rl harness ...); do grep -ql workflow "$f" && echo x; done |
wc -l` equal to 59, and the `scratch`/`workflow` equivalent equal to 48 — and
a code COMMENT I had written in `src/deepreason/llm/repair.py` named
`workflow/repair_transaction.py` and `workflow/nonconjecture_recovery.py` by
path. That put the literal word "workflow" into a file that has no such
import, and both counts moved by one. The comment was reworded to name the
SYMBOLS instead (`V6RepairTurn.mode`, `_repair_authority`), which is better
comment practice anyway and restores both censuses. Recorded because the
failure mode is invisible: a coupling census counts text, so a cross-package
reference in a comment reads as coupling.

**(7) The audit's probe inverts — PASS, and it inverts the way the brief
predicted.**

    python experiments/2026-08-28-audit-run-problems/probes/q5_repair_vocabulary.py
    -> exit 1
       PASS  producer Literal is exactly {initial, whole_object_syntax, patch}
       FAIL  checker set is exactly {patch, full} -- []
       FAIL  the two vocabularies intersect in {'patch'} only -- []
       FAIL  'full' is accepted by the checker and emitted nowhere in src/
       PASS  'whole_object_syntax' is emitted by the producer and rejected by
             the checker

Read this honestly rather than as five verdicts. The probe extracts the
checker's vocabulary with `re.search(r'mode in \{([^}]*)\}, "repair mode is
invalid"')` — a regex shaped for a BRACED LITERAL SET. The source now reads
`mode in V6_REPAIR_TASK_MODES`, so the regex misses and `checker` is the empty
set. The three FAILs are therefore real and are the required inversion; the
final PASS is an ARTEFACT, not evidence — "rejected by the checker" is
trivially true against an empty set. Two of five lines are now uninformative.

This is exactly why the brief called the probe "necessary but not sufficient":
it was built to assert the DEFECT, so on a fixed tree it can only tell you the
defect's source shape is gone, never that the replacement is correct. The
proof of correctness is (1), which drives a real payload through the real call
site. The probe is left as committed — it is the audit's artifact, not this
tranche's, and rewriting another tranche's instrument to keep it green would
destroy the before/after record it exists to hold.

## Pre-existing failures confirmed NOT mine

`python -u scripts/wheel_operational_smoke.py` exits 1 at
`{"stage": "continuation_resume", "failure_kind": "assertion_failed"}`. Run
again on a clean checkout of `main` (2a5e984c8) with this tranche's work
stashed: **identical stage and failure kind**. Not caused here, not fixed here
(dr-implement-fix: "a pre-existing failure you did not cause: stop, report, do
not fix it while you're there"). Parked as PK1 with a ready-to-send prompt, and
flagged there because no gate runs either wheel smoke, so a red one is
invisible to `pytest tests/`. `python scripts/wheel_smoke.py` — the smoke that
pins the public surface — passes.

`ruff` findings: unchanged on every file this tranche touched
(`repair.py` 5 -> 4, `nonconjecture_recovery.py` 4 -> 4, `cycle_soak.py`
9 -> 9, `wheel_operational_smoke.py` 26 -> 26, measured against the same files
at 2a5e984c8), and the two new findings in the new test file were fixed. No
finding added.

## Frozen surfaces

None touched. `capabilities/state.py`, `harness.py`, `invariants.py`,
`verification/`, `run_manifest.py`, `qualification.py` and the frozen-adjacent
`route_fingerprint` in `llm/firewall.py` are all unmodified —
`git diff --name-only 2a5e984c8` confirms. No committed digest pin moved. No
record FORMAT changed: the payload's written bytes are byte-identical before
and after, and only what a reader ACCEPTS moved — the direction
`INV-frozen-surfaces.md` requires. Committed roots carrying
`whole_object_syntax` payloads became more readable, never less.

`invariants.py:775`'s positive `payload.get("mode") == "patch"` filter is
deliberately untouched: asking "is this one particular mode?" is a correct
question that owns no vocabulary, and widening it would change which provider
rows `verify_root` treats as semantic rejections — a replay-validation record
format question on frozen surface 3.

## Diff budget

    python tools/diff_budget.py 2a5e984c8 --ceiling 150 \
        --paths src/deepreason/llm/repair.py \
                src/deepreason/workflow/nonconjecture_recovery.py
    -> {"areas": {"src/deepreason/llm/repair.py": 29,
                  "src/deepreason/workflow/nonconjecture_recovery.py": 16},
        "total_insertions": 45, "ceiling": 150, "verdict": "WITHIN"}

## Verdict

**PASS.** Every GOAL.md criterion met. One vocabulary, declared once and
consumed by import; `full` emitted by nothing and now accepted by nothing; the
call-site question answered by the record and confirmed by the repro's
traceback; the soak able to provoke the killing mode offline; full gate 0
failed; map moved in the same commit.

## Residue — what this tranche did NOT prove

Stated because "accepted does not mean true":

1. **No live run.** The proof is offline. A live re-run of epoch 5 is a
   separate act with its own cost, and this tranche did not take it.
2. **`alternate` induction is unexercised in its intended use.** It has never
   driven two different repair modes in one soak, because `epoch3` induces one
   wire schema title. Needs a multi-schema case to be worth anything.
3. **Only ONE of the two readers was exercised end to end.**
   `recover_atomic_child_output` is proven. The sibling path,
   `nonconjecture_recovery.py:1194` inside `recover_nonconjecture_admission`,
   shares the fixed `_repair_authority` and is therefore fixed by
   construction, but no test in this tranche drives a `whole_object_syntax`
   payload through it. The existing suite covers that function on other
   payload shapes.
4. **The mode/pointer-agreement check guards a state no writer can reach.**
   Its two direction tests neutralize the payload/preparation digest binding
   to get at it (FIX.md Amendment 2). It is a regression guard against a
   FUTURE writer change, not a live defence against anything today.
5. **PK2 is open for three of four soak seams.** D1's verdict now rests on an
   honest fact; whether D2, D3 and D4 report `covered` on proxies of the same
   kind was not examined.
