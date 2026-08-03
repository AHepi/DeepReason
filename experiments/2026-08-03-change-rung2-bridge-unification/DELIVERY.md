# Delivered: rung 2, tranche 3 — unify the bridge settings
Branch: `claude/delivery-rungs-handover-m22sdy` @ `9652e4db` (pushed,
tree clean).

## What changed

`engaged_bridge_source()` in `src/deepreason/v6_policy.py` no longer
returns a bare, hand-written literal dict — it now constructs a
`BridgeConfig` instance (the typed `Config` home INVENTORY.md's Group B
finding showed it was bypassing) with the same five override values
(`mode`, `grounding_review`, `max_schema_repair_attempts`,
`max_grounding_repair_attempts`, `output_section_limit`) and projects
onto those same five keys. Net behavior is unchanged and proven so
twice over: the pre-existing test that pins the exact dict
(`test_engaged_bridge_source_enables_the_reviewed_grounded_bridge`)
passes unchanged, and a new test
(`test_engaged_bridge_source_is_built_through_bridge_config`) proves the
function's output equals a freshly-constructed `BridgeConfig`'s
projection onto the same five fields — the "built THROUGH `BridgeConfig`,
not merely coincidentally identical" property the hard-coded dict never
had. `docs/map/CON-authority.md` was updated in the same commit
(`e15103d8`) with one new checked claim.

**This tranche's request contained a factual error, caught and resolved
before any code was written, not glossed over here.** The operator's
original instruction said "change `BridgeConfig`'s defaults... `BridgeConfig`'s
current defaults are the dead ones." That premise was false:
`tests/test_config_scratch_bridge.py::test_safe_defaults_are_bounded_and_
features_remain_opt_in` pins bare `Config().bridge.mode ==
"legacy_thesis"` as a deliberate "safe by default, features remain
opt-in" contract, and the `deepreason config compile` CLI subcommand
consumes `BridgeConfig`'s shared defaults directly, without ever
going through `engaged_bridge_source()`. Flipping the shared class
defaults would have broken that test and changed behavior for every
bare `Config()` construction in the codebase, not just the engaged
preset. This was presented to the operator as a genuine two-option fork
(`dr-ask-the-right-question`) BEFORE any implementation began, and the
operator chose: build `engaged_bridge_source()` from `BridgeConfig` via
an explicit-override instance, leave the shared class defaults
untouched (REQUEST.md Amendment 1). R1's literal instruction to "change
`BridgeConfig`'s defaults" is accordingly recorded as NOT implemented —
its underlying goal (stop the hard-coded dict silently drifting from
`BridgeConfig`) is what was actually delivered.

Because the shared defaults were never touched, this tranche never
needed to touch a frozen surface at all — the frozen-surface diff
(`run_manifest.py`, `qualification.py`, etc.) is empty for the whole
tranche, confirmed twice fresh in validation. No operator-approval gate
was needed here, unlike tranche 2.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Change BridgeConfig's defaults to equal the values the hard-coded dict actually runs with TODAY" | **done-with-amendment** (Amendment 1) — NOT implemented as literally worded; the operator's own premise was contradicted by the record and the operator chose the alternative | REQUEST.md Amendment 1 (verbatim operator answer: "Build from BridgeConfig, don't flip the shared default"); VALIDATION.md requirement sweep |
| R2 | "Make engaged_bridge_source() build its result from BridgeConfig instead of the hard-coded dict" | done | commit `e15103d8`; VALIDATION.md S1 |
| R3 | "Net behavior change must be ZERO. Prove it with a test..." | done | pre-existing test unchanged + new test, both passing; VALIDATION.md S1/S3 |
| R4 | "full gate ... 0 failed" | done | 3292 passed, 0 failed, isolated, reproduced twice; VALIDATION.md |
| R5 | "root sweep ... byte-identical" | done | 42 rows, 11 ERROR, byte-identical, reproduced twice; VALIDATION.md |
| R6 | "Map updated in the SAME commit as the code" | done | commit `e15103d8` (code + test + map together) |
| R7 | "FLIPPING ANY VALUE TO BridgeConfig's OLD defaults is the operator's decision, never yours" | done | no value flipped in either direction — `BridgeConfig`'s defaults are entirely untouched (S2, empty diff on `config.py`) |
| R8 | "Route: dr-change-orchestrator, one tranche, quote this message verbatim in REQUEST.md" | done | REQUEST.md quotes the full message verbatim |
| R9 | "Read CLAUDE.md first, then proceed with tranche 3 per REQUEST.md's my authorization" | done | session preflight re-run at this continuation's start, before REQUEST.md's capture |

## Assumptions the operator may override

A1: the new test lands in `tests/test_v6_policy_preset.py`, one new
function, alongside the existing (unchanged) bridge-source test.
A2: no `BridgeConfig` field type or bounds changes — moot once
Amendment 1 foreclosed any default change.
A3: no code change to `run_manifest.py`, `qualification.py`, or any
frozen surface — verified directly during `dr-spec-change` and
reconfirmed by the empty frozen-surface diff in both validation passes.

## Map delta

Changed: `docs/map/CON-authority.md` — one new section ("Adjacent, not
authority: preset-construction hygiene in `v6_policy.py`") with one new
checked claim. Created: none. New checks: 1.

The section's placement is honestly a compromise, not a perfect
thematic fit: `CON-authority.md` is titled "who may change a Status,"
and this claim is about preset-construction hygiene, unrelated to
authority. It lives there because that document is the only established
`Owns:` home for `v6_policy.py`/`preparation.py` (from tranche 2), and
no other `docs/map/` document owns either file — creating a new document
for one small fix was judged disproportionate. Noted in `PARKED.md` as
worth revisiting if a third unrelated claim ever lands in the same
document.

Left stale (advisory `--stale`, all dismissed in VALIDATION.md with
reasons — none need further action from this tranche):
`CON-run-identity.md`, `CON-schools.md`, `SEAM-bridge-x-manifest.md`,
`SEAM-llm-x-manifest.md`, `SUB-manifest.md`, `INV-frozen-surfaces.md`
(all from tranche 2's own commits, already resolved there);
`SEAM-manifest-x-schools.md` (this tranche's commit touched a
co-owned file, `v6_policy.py`, but not anything that document's own
checks reference); `SEAM-harness-x-verification.md`,
`SUB-verification.md` (an unrelated, pre-existing commit).

## Parked (not done, not promised)

See `PARKED.md`. Summary: R1's literal instruction (flipping
`BridgeConfig`'s shared defaults) remains a possible FUTURE decision,
not implemented or recommended here; rung 2's Group C (env-var
switches) and Group D (`STANCE_LIBRARY`) inventory candidates remain
unaddressed; the map-document placement compromise noted above; no
structural guard against a future regression back to a bare literal
dict (value-drift is caught by tests, but a hand-edit reverting the
construction mechanism itself would not be).

This closes rung 2's third tranche (inventory → criticism-authority
switch → bridge unification). No further rung-2 or rung-3 work is
started — the operator picks what comes next.
