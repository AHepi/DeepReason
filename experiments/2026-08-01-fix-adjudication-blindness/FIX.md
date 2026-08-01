# Fix: report a run whose criticism ran and attacked nothing

Guarantee restored: `epistemic_checks_passed` is false for a run in which
criticism executed and produced no attack — the state
`docs/harness-spec-v1.3.md` §11.3 calls "D3 has died in practice while
remaining true on paper".

## The predicate, and why not "zero attacks"

Zero attacks alone is wrong. Measured over every root under `experiments/`:
all 26 zero-attack roots are real runs with cycles ≥ 1, but unit fixtures such
as `_engaged_root` have 0 cycles and no criticism at all — they never had the
opportunity to attack, so flagging them would be noise, and 22 test files
assert `verify_root(root)["violations"] == []`.

The predicate is therefore **criticism ran in the window AND produced zero
attacks**. Two committed, git-tracked roots give a positive and a negative:

    live_tri_2026-07-27/run-6dab80d6…   Crit=11  assignments=24  att=0   POSITIVE
    live_engaged_2026-07-27/run-f4fa66…  Crit=28  assignments=35  att=1   NEGATIVE

Change sites (exhaustive):

  - `src/deepreason/capture/detection.py`, `adjudicator_metrics` — add
    `criticism_events`, the count of `Crit`-rule events in the same window the
    function already reads (`harness.recent_semantic_events(window)`). Windowed
    like every other metric there, per §11.3's "sustained CAPTURE_W".
  - `src/deepreason/capture/detection.py`, `raw_flags` return dict — add
    `adjudication_blind = criticism_events > 0 and n_attacks == 0`. A NEW flag,
    not a change to `adjudication_ritual`: the spec states the validity-attack
    surface as its own diagnostic, separate from the two-of-four ritual
    conjunction, so contorting that conjunction would both misread the spec and
    perturb existing ritual semantics.
  - `src/deepreason/verification/report.py` — call `raw_flags` where the report
    already holds a `Harness` and emit
    `_finding("epistemic", "adjudication-blindness", …, source="derived")` when
    the flag is set.
  - `src/deepreason/verification/report.py:131-137` — add
    `"adjudication-blindness"` to `_EPISTEMIC_CHECKS` so a legacy-classified
    instance of the same check also routes to epistemic.

## Why the finding goes in report.py, not invariants.py

`invariants.py:4040-4048` is where detection is called today, but its `fail()`
feeds the LEGACY `verify_root(root)["violations"]` list. Adding a violation
there would newly break every test asserting that list is empty on a root with
criticism — 22 files assert exactly that. `report.py` already opens
`Harness(root, read_only=True)` (four sites) and already emits derived findings
through `_finding(...)`, so the finding reaches the epistemic channel without
touching the legacy list at all.

`invariants.py:4040-4048` is left as-is. Its `raw_flags` call remains the
totality check its comment says it is; it is no longer the only caller, so
nothing is lost by leaving it alone. **Not** changing it is deliberate: doing
both would put the same finding in two channels.

## `valid` cannot move, and this was checked before designing

`VerificationReportV2.valid` is `integrity_valid and security_valid`
(`report.py:90-93`) — the epistemic channel does not gate it. And the recorded
summary comparison at `report.py:313` is one-directional: it emits a finding
only when a stored summary says `epistemic_checks_passed is False`, never when
a stored `true` disagrees with a computed `false`. So no root can flip from
valid to invalid, and GOAL.md criterion (c) is satisfiable by construction
rather than by luck.

Regression artifact: `tests/test_adjudication_blindness.py`
  - `::test_a_root_with_no_attacks_reproduces_the_live_shape` — passing, keep.
  - `::test_detection_flags_reach_the_epistemic_channel` — FAILING, must
    invert. This is the plumbing test: it forces every flag True and asserts a
    finding appears.
  - `::test_the_ritual_flag_cannot_fire_when_nothing_was_ever_attacked` — to be
    REWRITTEN. It currently asserts `adjudication_ritual` on a fixture with no
    criticism, which under this design is correctly False. It is replaced by
    record-replay over the two committed roots above: `adjudication_blind` True
    on `run-6dab80d6…`, False on `run-f4fa6663…`.

Existing tests at risk:
  - The 22 files asserting `verify_root(root)["violations"] == []` — all must
    KEEP PASSING, and should, because the finding never enters that list. This
    is the single largest risk in the tranche and is the first thing to measure
    at implement time.
  - Any test asserting `report.epistemic == ()` or
    `epistemic_checks_passed is True` on a root with criticism and no attacks —
    to be found by grep at implement time. Such a fixture would be
    defect-dependent (it asserts the harness is honest about nothing) and may
    be updated minimally; any OTHER failure means the fix is wrong.
  - `tests/test_v6_engaged_repair_verification.py` — unaffected: its fixture
    has no `Crit` events, so the predicate is false and no finding appears.

Predicted effects, to be measured in dr-verify-outcome and not assumed:
  1. `run-6dab80d6…` and the jolt root gain exactly one epistemic finding and
     report `epistemic_checks_passed: False`.
  2. `run-f4fa6663…` gains none.
  3. A verdict sweep over all 31 openable roots: NO root's `valid` changes.
     `epistemic_checks_passed` changes on the subset with criticism and zero
     attacks — that count is to be reported, not predicted, because I have not
     measured how many of the 26 have criticism in-window.
  4. `tests/test_adjudication_blindness.py`: 3 passed.
  5. Full gate: 0 failed.

Explicitly not changed:
  - `src/deepreason/authority.py`. `OBSERVE_ONLY` for text workloads is WHY
    there are no attacks. Making the harness honest about what it did is this
    tranche; changing what it is permitted to do is the operator's design call.
  - `adjudication_ritual` and `MIN_ATTACKS_FOR_RITUAL`. The threshold problem
    is real (two of four conditions unreachable at total blindness) but is a
    separate, weaker statement than the new flag, and changing the conjunction
    would move existing ritual semantics for no gain here. PARKED.
  - `invariants.py`'s totality check, per above.

Estimated diff: ~45 lines across 3 files. Under the 150-line budget.

Approval gate: GOAL.md class is `defect`; estimate ≤150 lines; no frozen
surface touched (no state digest, no event application order, no manifest
schema, no qualification subject, no record format, and `valid` provably
cannot move). Proceeds to `dr-implement-fix`.
