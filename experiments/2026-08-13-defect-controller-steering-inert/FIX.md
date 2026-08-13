# Fix: anchor each role's control-barrier envelope to the cap the run was actually configured with, and make an unsteerable controller say so

**STATUS: APPROVED 2026-08-13 — Road A.** The operator was presented the
fork below and selected "Approve Road A", authorizing the ~12-line change
to the authorization predicate in `src/deepreason/invariants.py` (frozen
surface #3) on the stated conditions: the change is strictly widening, it
is provably a no-op on all 104 committed logs, and the 42-root sweep is a
proof obligation before the commit lands. That authorization covers
`invariants.py:3609-3620` and nothing else frozen; any further frozen
surface encountered during implementation is a fresh stop.

Original gate text, kept for the record:

**STOPPED FOR OPERATOR APPROVAL.** The correct fix requires a
change inside `src/deepreason/invariants.py`, which
`docs/map/INV-frozen-surfaces.md` names as frozen surface #3. GOAL.md and
the tranche brief both expected "frozen surfaces: none". This document
states the fork, prices it, proves the safety claim from the record, and
recommends. No production code has been changed.

## Added condition (operator, 2026-08-13, verbatim)

> "With the added condition that role assigned limits are optional"

Binding on this fix. A role's assigned limit (its `max_tokens` pin) is
OPTIONAL: a manifest may bind a role with no cap assigned at all, and that
is a supported configuration, never an error and never a denial (the
operator's standing "all configurations should be allowed" law). Two
consequences the implementation must honour:

  - Nothing in this fix may REQUIRE a role to carry an assigned limit.
    `cap_envelope(knob, None)` falls back to the static/default shape;
    no anchoring, no refusal, no exception.
  - A role with no assigned limit must not be SILENTLY skipped either —
    that is the same defect shape in a new place. The controller does not
    invent a limit the operator declined to assign; it records the role as
    unsteerable with the typed reason `no-assigned-limit`.

This widens the typed record from "fires only when the controller can
steer nothing" to "the controller states its authority over this run
once, and again whenever that authority changes": one
`controller-authority` Measure record carrying `full` / `partial` /
`none`, the steerable roles, and every unsteerable role with its reason.
An empty steerable set is the `none` case the original requirement asked
for; the partial case is the one this added condition exposes.

Guarantee restored: **a role the run binds is a role the controller may
calibrate — within the range the operator configured, never outside it —
and if the controller can calibrate nothing at all, the record says so.**

## Why the obvious small fix is wrong — measured, not argued

The tempting minimal fix is "widen the static `ENVELOPES` maxima" or "let
an out-of-envelope cap jump down into the envelope". Both avoid touching
`invariants.py`. Both are refuted by the completion-token usage the
committed root actually recorded (`event.llm.completion_tokens`, 666
calls):

    role                    n    p50    p90    p99    max   configured cap
    judge                 342     63     90    120    141           16384
    argumentative_critic  123    294    580    941    982           16384
    defender              122    362    635   1043   1090           16384
    conjecturer            49   4968   8730  12146  12146           16384
    variator               30   1567   3413   7473   7473           16384

`cap:conjecturer`'s static envelope max is **5,000** — BELOW this run's
median conjecturer completion of 4,968. A fix that moves the conjecturer
cap into the static envelope lands it at 5,000, where ~24 of 49 calls
(49%) would truncate. The controller would then read
`truncation_rate > TRUNC_HI` and try to widen — to
`clamp(5000 * 1.6) = 5000`, the envelope ceiling. **No change possible.**
The role would be pinned at 5,000 with half its calls truncating, and the
controller would be unable to escape. That is strictly worse than today's
inertness.

The static table is not merely incomplete; its numbers predate reasoning
models and are wrong by an order of magnitude for the seat that needs the
most room. Any fix that keeps those numbers as the ceiling is unsafe.

Same table, read the other way, is the prize: `judge` is pinned at 16,384
and has never emitted more than **141** completion tokens. A working
controller settles that seat toward its floor and stops paying for a 116x
headroom on 342 calls.

## The fix (Road A — recommended)

An envelope's bounds become a pure function of the static table AND the
cap the run bound for that role, computed identically by the writer and
the reader from one shared function:

    lower = min(static_min, configured_cap)      # never force a cap UP
    upper = max(static_max, configured_cap)      # never force a cap DOWN
    step, dwell from the static table, or a default for a role the
    table does not name

Consequences, each deliberate:
  - Every role the manifest binds gets an envelope, including the five
    the table never named (`grounding_reviewer`, `property_designer`,
    `summarizer`, `thesis`, `vision_critic`), and including any role
    added later — the coverage is derived, not enumerated, so this
    defect cannot recur for a twelfth role.
  - The controller may NEVER widen a cap past what the operator
    configured. `upper` is the configured cap whenever that cap already
    exceeds the table. This is a stronger safety property than today's
    static ceiling, not a weaker one.
  - `tests/test_controller.py::test_controller_does_not_normalize_an_explicit_cap_outside_its_envelope`
    keeps passing **byte-unchanged**: with a 7,000 baseline the envelope
    becomes `[800, 7000]`, a truncation signal proposes
    `clamp(round(7000*1.6)) = 7000 == cur`, no delta, `step()` returns
    `None`, cap stays 7,000, no `controller-update` record. The
    "no authority to normalize an explicit setting" guarantee is
    preserved by construction rather than retired.
  - The grounded configuration steers: conjecturer 16384 -> 10240 on the
    first clean window and onward geometrically, judge 16384 -> 10240 ->
    ... -> 800 (floor), each move damped by `dwell=2`, each move a logged
    attackable `Refl` policy artifact.

Second half of the fix — the typed nothing-to-steer record. When the
controller is ON and the set of steerable knobs is EMPTY (no endpoint in
the adapter exposes a `max_tokens` at all), it appends one
`controller-inert` Measure record naming the reason and the roles it could
not steer, episode-deduplicated the way
`research-awaiting-agent` already is (one record per continuous episode,
not one per cycle — the pattern `DR-SUB-scheduler`'s "Silence is not
evidence of absence" trap established). Silent inertness becomes
structurally impossible: the controller either moves a knob or records
that it has none.

## Change sites (exhaustive)

  - `src/deepreason/controller.py:44-58` — add `is_generator_knob(knob)`:
    a `cap:<role>` knob is generator-ledger by construction (a completion
    cap is a generation parameter no adjudication input reads), any other
    knob must be in the static `GENERATOR_LEDGER`, and nothing in
    `TRIBUNAL_LEDGER` ever qualifies. The two static frozensets stay
    exactly as they are, so
    `test_forbidden1_ledgers_are_disjoint_and_tribunal_is_untouchable`
    is untouched.
  - `src/deepreason/controller.py:70-85` — add `DEFAULT_CAP_ENVELOPE`
    (the step/dwell/floor used for a role the static table does not
    name) and the shared `cap_envelope(knob, configured_cap)` function
    implementing the two-line rule above. `ENVELOPES` itself is NOT
    edited — its numbers stay as the historical floor/step/dwell source.
  - `src/deepreason/controller.py:101-103` — `clamp()` becomes
    envelope-aware. It currently reads module-level `ENVELOPES[knob]`,
    which would `KeyError` on a derived role and would clamp to the
    stale static max on an anchored one.
  - `src/deepreason/controller.py:113-121` — `__init__` COPIES the
    envelope table before anchoring (today `self.envelopes = envelopes or
    ENVELOPES` aliases the module-level dict; anchoring in place would
    mutate global state across runs in one process — a real bug this fix
    must not introduce), then anchors from `_current_caps()` BEFORE
    `_rehydrate_process_state()`, which validates stored policy knobs
    against the envelopes.
  - `src/deepreason/controller.py:255-283` — `_propose` unchanged in
    logic; both existing `continue`s stay. They stop firing because the
    envelopes now contain the caps, which is the point: the guards remain
    correct, their premise is repaired.
  - `src/deepreason/controller.py:350-376` — `step()` records
    `controller-inert` once per episode when the steerable set is empty;
    the `assert knob in GENERATOR_LEDGER` becomes
    `assert is_generator_knob(knob)`.
  - `src/deepreason/invariants.py:3609-3620` — **THE FROZEN-SURFACE
    CHANGE.** `verify_root` authorizes a per-attempt `max_tokens` only if
    the route pinned it or a prior controller policy recorded it AND that
    policy value passed `ENVELOPES[knob]`. It must call the same shared
    `cap_envelope(knob, configured_cap)`, with `configured_cap` read from
    the manifest's bound route for that role, or every run in which the
    controller actually steers becomes replay-INVALID. This is ~12 lines
    and imports one more name from `deepreason.controller`, which
    `invariants.py:18` already imports from.

### Amendment 1 (2026-08-13, during implementation) — a third change site

`src/deepreason/signals.py` — the signal registry. FIX.md missed it and
the full gate caught it:
`tests/test_signals.py::test_every_emitted_signal_is_registered` failed
with `unregistered signals emitted by the source tree:
['controller-authority']`. Every Measure tag the source tree emits must
carry a registry entry describing it; `controller-update`,
`controller-rehydration` and `controller-hold:` are already there, so
`controller-authority` joining them is the registry working exactly as
designed, not a new obligation. Recorded as an amendment rather than
absorbed silently, per this workflow's rule that an unlisted change site
stops and amends before it is edited. One dictionary entry, no logic.

Estimated diff: ~86 production lines across 3 files (74 controller, 12
invariants, 1 signals registry entry), plus a new test file and the map
documents. Ceiling for the mechanized budget gate: **<=150 insertions**
over those three paths.

## Safety of the frozen-surface change — proved from the record, not argued

`INV-frozen-surfaces.md`'s governing principle: *a change that alters what
a FUTURE run may do is ordinary work; a change that alters how a PAST run
verifies is a defect.*

The change is **strictly widening** — it can only ADD values to
`authorized_controller_limits`, never remove one — so no committed root
can move from valid to invalid. And it is provably a **no-op on every
committed root**, because no committed root has a controller policy for
the widened rule to read:

    for f in $(find experiments -name log.jsonl); do
      n=$(grep -c '"knobs"' "$f"); [ "$n" != 0 ] && echo "$n $f"; done
    # -> no output, across all 104 committed logs

`authorized_controller_limits` is therefore empty in all 104, every past
attempt's `max_tokens` equals its route's, and both branches of the
`attempt-limits` check are unreached by this edit. The 42-root sweep is
the instrument that must confirm it, and it is a required deliverable
before the commit lands.

The frozen item in `INV-frozen-surfaces.md` #3 is the replay-validation
**output shape** ("their output shape is compared across runs and across
time"). This edit changes an authorization predicate, not a record format,
not a finding name, not a report field. But `invariants.py` is named in
that document's `Owns:` line, so it is the operator's call, not mine.

## The alternative, priced honestly (Road B — not recommended)

Widen the static `ENVELOPES` maxima to a global ceiling (e.g. 32768) and
statically add the five missing roles. No `invariants.py` change, ~25
lines.

What it costs:
  - It **retires a designed guarantee**.
    `test_controller_does_not_normalize_an_explicit_cap_outside_its_envelope`
    fails: with a 32,768 ceiling, the 7,000 website cap is in-envelope,
    a truncation signal widens it to 11,200, and both of that test's
    assertions break. The fixture would have to be rewritten, and its
    guarantee — the controller may not override an explicit compiled
    setting — would be gone.
  - It lets the controller widen a cap **past what the operator
    configured**, up to an arbitrary global number with no principle
    behind it.
  - The role list stays enumerated, so a manifest binding a twelfth role
    is silently inert again. The defect class survives the fix.

Road B is smaller and touches nothing frozen. It is worse on every axis
that matters.

## Existing tests at risk

From `grep -rn "deepreason.controller\|ENVELOPES\|Controller(" src/ tests/`:

  - `tests/test_controller.py::test_controller_does_not_normalize_an_explicit_cap_outside_its_envelope`
    — **must keep passing unchanged** under Road A (baseline 7,000 ->
    envelope [800,7000] -> widen clamps to 7,000 -> no delta). It is the
    single best regression guard on this fix and will be run first.
  - `tests/test_controller.py::test_forbidden3_widen_is_clamped_to_envelope_max`
    — baseline 800 -> envelope [800,5000], identical to today. Must keep
    passing unchanged.
  - `tests/test_controller.py::test_resume_rehydrates_only_latest_accepted_controller_policy`
    — baseline 800, rehydrates 1,280, inside [800,5000]. Unchanged.
  - `tests/test_controller.py::test_forbidden1_*`, `test_forbidden2_*`,
    `test_forbidden7_decisions_replay_stable`,
    `test_transport_drops_widen_timeout_within_envelope_and_dwell`,
    `test_non_transport_drops_do_not_move_the_timeout`,
    `test_transport_policy_decisions_replay_stable`,
    `test_run_scheduler_wires_controller_by_default` — all use baseline
    800 endpoints or the transport knob, which this fix does not touch.
    Unchanged.
  - `scripts/live_run.py:795` constructs a `Controller` — signature
    unchanged, no edit needed.
  - No fixture is expected to need updating. **If one does, that is a
    stop**, not a quiet edit.

## Regression artifact

`experiments/2026-08-13-defect-controller-steering-inert/repro_controller_inert.py`
must invert: Part A's eight `None`s become real proposals with policy
artifacts; Part B must keep passing unchanged. Promoted into
`tests/test_controller_steering_parity.py` with four assertions matching
GOAL.md's success criterion:
  1. a run started through `start_manifest_run` from a COMPILED manifest
     records controller attachment;
  2. that run records a policy evaluation, or the typed
     `controller-inert` record when there is genuinely nothing to steer;
  3. envelope coverage asserted for EVERY role the manifest binds;
  4. the managed-path fixture record byte-unchanged.
Plus: a test that `controller-inert` actually fires (an adapter whose
endpoints expose no `max_tokens`), so `docs_verify --audit` cannot call
the new check unfailable.

## Explicitly not changed

  - `ENVELOPES`' existing numbers, `GENERATOR_LEDGER`, `TRIBUNAL_LEDGER`
    — the constitution stays diff-checkable and the two ledgers stay
    disjoint frozensets.
  - `timeout:transport` — the manifest pins `timeout_s: 120`, inside the
    static `[120, 900]`, so that knob was never blocked and needs no
    anchoring. The grounded root recorded 0 `dropped-call` events, so it
    correctly never fired.
  - `config_referee` — DIAGNOSIS.md establishes its absence is the
    operator's default-OFF configuration, recorded in the manifest, not
    inertness. Out of scope.
  - The scheduler's criticism-debt dispatch — PARKED.md P1.

## Decision needed

**One sentence: may the fix change ~12 lines of the authorization
predicate in `src/deepreason/invariants.py` (a named frozen-surface file),
given it is strictly widening and provably a no-op on all 104 committed
logs?**

  - **Approve Road A (recommended)** — the controller steers every bound
    role within the operator's own configured range, the existing
    no-normalization guarantee survives byte-unchanged, and the defect
    cannot recur for a new role. Cost: 12 lines in a frozen-surface file,
    with the 42-root sweep as the proof obligation before commit.
  - **Direct Road B** — nothing frozen is touched, ~25 lines, delivered
    faster. Cost: a designed guarantee is retired, the controller may
    exceed the operator's configured cap, and a future role is silently
    inert again.
