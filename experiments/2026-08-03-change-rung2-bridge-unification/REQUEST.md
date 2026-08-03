# Request: rung 2, tranche 3 — unify the bridge settings
Captured: 2026-08-03, from this session's conversation. Authority is two
sources: (1) the operator's original "TRANCHE 3" authorization message,
received earlier this session (while tranche 2 was still open, explicitly
gated on tranche 2's delivery); (2) this session's continuation message,
after tranche 2 delivered, giving the explicit go-ahead to open now.

## Verbatim

> Operator authorization for rung 2, TRANCHE 3 (after the
> engaged_criticism_policy switch tranche is delivered — never in the
> same tranche as it).
>
> Task: unify the bridge settings. INVENTORY.md Group B (your own finding,
> experiments/2026-08-03-change-rung2-config-inventory/) showed
> v6_policy.py::engaged_bridge_source() hard-codes a dict that bypasses
> config.py's BridgeConfig, with three of five values differing from
> BridgeConfig's defaults.
>
> The fix, exactly this and no more:
> 1. Change BridgeConfig's defaults to equal the values the hard-coded
>    dict actually runs with TODAY (the dict's values win — they are the
>    current behavior; BridgeConfig's current defaults are the dead ones).
> 2. Make engaged_bridge_source() build its result from BridgeConfig
>    instead of the hard-coded dict.
> 3. Net behavior change must be ZERO. Prove it with a test asserting the
>    new path produces exactly the dict the old code hard-coded, plus the
>    standard acceptance: full gate `python -m pytest tests/ -q -n 4`
>    0 failed; root sweep `python tools/root_sweep.py` byte-identical.
> 4. Map updated in the SAME commit as the code. FLIPPING ANY VALUE TO
>    BridgeConfig's OLD defaults is the operator's decision, never yours —
>    if you believe an old default was the intended value, write it in
>    PARKED.md and leave the running values alone.
>
> Route: dr-change-orchestrator, one tranche, quote this message verbatim
> in REQUEST.md. Ledger note: docs/ERRATA_EXECUTOR.md now has a numbering
> rule — your entries use XE<n> ids from now on (XE1 next), never X<n>.
>
> — operator's message opening rung 2 tranche 3, received during this
> session while tranche 2 was still in progress

> Read CLAUDE.md first, then proceed with tranche 3 per REQUEST.md's my
> authorization
>
> — operator's message this session, after tranche 2 delivered
> (`5ecd5d62`), giving the explicit go-ahead to open this tranche now

## Requirements

R1 (behavior): "unify the bridge settings... Change BridgeConfig's
defaults to equal the values the hard-coded dict actually runs with
TODAY (the dict's values win — they are the current behavior;
BridgeConfig's current defaults are the dead ones)."

R2 (behavior): "Make engaged_bridge_source() build its result from
BridgeConfig instead of the hard-coded dict."

R3 (process): "Net behavior change must be ZERO. Prove it with a test
asserting the new path produces exactly the dict the old code
hard-coded."

R4 (process): "full gate `python -m pytest tests/ -q -n 4` 0 failed."

R5 (process): "root sweep `python tools/root_sweep.py` byte-identical."

R6 (process): "Map updated in the SAME commit as the code."

R7 (process): "FLIPPING ANY VALUE TO BridgeConfig's OLD defaults is the
operator's decision, never yours — if you believe an old default was the
intended value, write it in PARKED.md and leave the running values
alone."

R8 (process): "Route: dr-change-orchestrator, one tranche, quote this
message verbatim in REQUEST.md."

R9 (process): "Read CLAUDE.md first, then proceed with tranche 3 per
REQUEST.md's my authorization" — this session's explicit go-ahead to
open now, after tranche 2's delivery satisfied the original message's
own precondition.

## Standing constraints

C1: "Task: unify the bridge settings... exactly this and no more" — no
other `Config`/preset unification is in scope (not Group C's env-var
switches, not Group D's `STANCE_LIBRARY`, not anything from rung 2's
inventory beyond this one named Group B finding).

C2: "after the engaged_criticism_policy switch tranche is delivered —
never in the same tranche as it" — satisfied: tranche 2 delivered,
`DELIVERY.md` commit `5ecd5d62`, independently confirmed by
`docs/ERRATA_EXECUTOR.md` X10 ("tranche 2 delivered; the X8/X9 arc
closes clean... authorized next is tranche 3 (BridgeConfig
unification)").

C3 (supersedes the Verbatim block's own "Ledger note"): the
`docs/ERRATA_EXECUTOR.md` numbering-rule instruction quoted in the
original TRANCHE 3 message ("your entries use XE<n> ids from now on")
has SINCE been superseded during tranche 2. Commit `87b2828d`'s message,
verbatim: "The executor no longer writes ERRATA_EXECUTOR.md (handover
instruction replaced, charter updated): one ledger, one writer; executor
observations travel via tranche artifacts." Binding on this tranche: no
`XE<n>` entries will be written; any process observation worth recording
goes in this tranche's own `PARKED.md` or phase document instead.

C4 (inherited, standing across this session): frozen surfaces bind
everything (`docs/map/INV-frozen-surfaces.md`); one rung per tranche;
known flake
`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`
can fail once under `-n 4`, rerun before diagnosing; commit and push at
every phase boundary; stop conditions are hard stops; where a spec is
silent, load `dr-ask-the-right-question` and route to the cheapest
authority — do not improvise. (Same standing constraints as tranche 2's
REQUEST.md C1-C5, restated here since this is a new, separate tranche.)

## Open questions (for dr-spec-change)

Q1: R1 says "the values the hard-coded dict actually runs with TODAY" —
this must be re-verified against the CURRENT tree (not just
INVENTORY.md's snapshot from earlier this session), since tranche 2's
own commits touched `v6_policy.py` and could conceivably have shifted
something adjacent. Needs a fresh read of `engaged_bridge_source()`'s
current dict literal before specifying exact target values.

Q2: R3 says "a test asserting the new path produces exactly the dict the
old code hard-coded" — no specific test file is named. Precedent from
tranche 2 (A2: extend the existing dedicated preset-construction test
file) suggests `tests/test_v6_policy_preset.py` again, but this needs
confirming against what that file currently contains.

Q3: R1/R2 do not specify whether `BridgeConfig`'s field TYPES need any
change (e.g., if the hard-coded dict's values don't fit the field's
current type/bounds) — INVENTORY.md's Group B finding should be
re-checked for whether this is a pure value change or also requires a
type/bounds adjustment.

Q4: Given tranche 2's own experience (a Config field addition breaking
pinned canonical-hash goldens across multiple schema versions, requiring
a frozen-surface touch to `run_manifest.py`), does changing
`BridgeConfig`'s DEFAULT VALUES (not adding a field, but changing
existing field defaults) risk a similar golden-hash break? This needs
checking against `_versioned_source_config_data` and the pinned-hash
tests BEFORE specifying the fix, not discovered mid-execution again.

## Amendments

**Amendment 1 — resolving a contradiction between R1's premise and the
record.** R1's parenthetical claim, "BridgeConfig's current defaults are
the dead ones," is contradicted by
`tests/test_config_scratch_bridge.py::test_safe_defaults_are_bounded_and_features_remain_opt_in`,
which explicitly pins `Config().bridge == BridgeConfig()` and
`config.bridge.mode == "legacy_thesis"` as part of a deliberate
"safe defaults, features remain opt-in" contract (the same pattern
`scratchpad.enabled == False` uses). Flipping `BridgeConfig`'s shared
class-level defaults to match `engaged_bridge_source()`'s override
values would break this test and change behavior for every bare
`Config()` construction across the codebase — not just the engaged
preset — including the `deepreason config compile` CLI subcommand
(`cli/main.py`, `load_config(None)` path, which does not go through
`_config_for_profile`/`engaged_bridge_source()` at all).

Presented to the operator as a genuine fork (per `dr-ask-the-right-
question`, since this is a frozen-behavior-adjacent, wide-blast-radius
decision the record does not resolve): (a) build
`engaged_bridge_source()` from `BridgeConfig` via an explicit-override
instance, leaving `BridgeConfig`'s shared class defaults and the
safe-defaults test untouched — satisfies R2/R3, only partially R1's
literal words; or (b) flip the shared class default as R1 literally
says, updating the safe-defaults test to match and accepting that every
bare `Config()` now defaults to the grounded bridge.

**Operator's answer:** "Build from BridgeConfig, don't flip the shared
default (Recommended)" — i.e., option (a). `engaged_bridge_source()`
must build from `BridgeConfig` (R2), proven by a test showing zero net
behavior change (R3), WITHOUT changing `BridgeConfig`'s shared
class-level field defaults. R1's literal instruction to "change
BridgeConfig's defaults" is accordingly NOT implemented as first worded;
R1's underlying goal — stop `engaged_bridge_source()` bypassing
`BridgeConfig` with a hard-coded dict that silently drifts from it — is
achieved via R2's mechanism instead. `test_safe_defaults_are_bounded_and_
features_remain_opt_in` stays unchanged and passing.
