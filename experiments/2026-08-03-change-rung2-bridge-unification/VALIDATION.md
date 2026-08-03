# Validation for: rung 2, tranche 3 — unify the bridge settings
Re-read REQUEST.md (Amendment 1), SPEC.md, CHECKLIST.md in full before
running anything below. Every check here was re-run fresh in this
validation pass. Branch head at validation: `b3d7dd27`.

## Acceptance checks

S1: `python -c "import inspect; from deepreason import v6_policy as p; src = inspect.getsource(p.engaged_bridge_source); assert 'BridgeConfig(' in src"`
-> exits 0 : PASS
`python -c "from deepreason.v6_policy import engaged_bridge_source as f; assert f() == {'mode': 'grounded_two_stage', 'grounding_review': True, 'max_schema_repair_attempts': 1, 'max_grounding_repair_attempts': 0, 'output_section_limit': 4}"`
-> exits 0 : PASS
`python -m pytest tests/test_v6_policy_preset.py -k test_engaged_bridge_source_enables_the_reviewed_grounded_bridge -q`
-> `1 passed, 14 deselected in 0.06s` : PASS (the EXISTING test, unchanged, still passes — R3's own required proof)

S2: `git diff --stat 899ebb18..HEAD -- src/deepreason/config.py`
-> empty output : PASS (zero lines changed in `config.py` across the
whole tranche)
`python -m pytest tests/test_config_scratch_bridge.py -k test_safe_defaults_are_bounded_and_features_remain_opt_in -q`
-> `1 passed, 13 deselected in 0.06s` : PASS

S3: `python -m pytest tests/test_v6_policy_preset.py -q`
-> `15 passed in 0.09s` : PASS. New test
`test_engaged_bridge_source_is_built_through_bridge_config` confirmed
collectable via `--collect-only -q`.

S4: `python -m pytest tests/test_run_manifest_v4.py tests/test_run_manifest_v5_inquiry.py tests/test_incident_wave_a_v2_fixtures.py tests/test_v6_policy_preset.py tests/test_v6_engaged_public_defaults.py tests/test_config_scratch_bridge.py -q`
-> `75 passed in 14.87s` : PASS

S5: `grep -q "engaged_bridge_source" docs/map/CON-authority.md`
-> PASS. `python tools/docs_verify.py` and `--audit` — see Map section
below.

S6: full gate + root sweep — see below.

## Full gate

Ran ISOLATED (nothing else concurrent, learning from tranche 2's Pass 1
resource-contention false-failure):

    3292 passed, 7 skipped in 566.83s (0:09:26)

One more passed than tranche 2's 3291 baseline, matching this tranche's
one new test. **Verdict: PASS.**

## Record-behavior preservation / root sweep

`python tools/root_sweep.py` run fresh, isolated: `SWEEP COMPLETE: 42
roots`, `11 ERROR` lines (all `UnsupportedRunManifestVersionError`).
Diffed against this tranche's own prior capture (`t3_sweep.txt`, taken
during step 10): **empty diff** — byte-identical. No committed root's
verdict moved.

**Verdict: PASS.**

## Frozen-surface diff

    git diff --stat 899ebb18..HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py \
      src/deepreason/qualification.py

    (empty output)

**Empty**, as designed. Unlike tranche 2, this tranche's whole design
point (Amendment 1's resolution) was to achieve R2/R3 WITHOUT touching
any frozen surface — verified directly during `dr-spec-change` (the
"Key technical finding": `Config(bridge=<5-key-dict>)` and
`Config(bridge=<14-key-model_dump>)` produce byte-identical serialized
output, so no golden-hash risk existed regardless of implementation
shape) and now confirmed by the empty diff itself. No operator
approval gate is needed for this tranche.

## Map

`python tools/docs_verify.py`: 49 documents, 796 checks, 0 failed : PASS
`python tools/docs_verify.py --audit`: 0 finding(s) : PASS
`python tools/docs_verify.py --links`: 0 dangling reference(s), 49
documents : PASS
`python tools/docs_verify.py --coverage`: 6 seams swept, 14 without a
`Sweep:` header, 0 findings — same pre-existing 14 as tranche 2, none
touched by this tranche : PASS, nothing to dismiss

`python tools/docs_verify.py --stale`: 11 documents. Every entry
dismissed with a reason:
- `CON-authority.md` — now 3 commits since its stamp (this tranche's
  `e15103d8` added to tranche 2's two); re-verified clean by the full
  run above; this is the document THIS tranche itself updated (S5), so
  its staleness is expected and its content is exactly what was
  intended.
- `SEAM-manifest-x-schools.md` — now 3 commits (this tranche's
  `e15103d8` added), because it also owns `v6_policy.py`; re-verified
  clean — this tranche's edit only touched `engaged_bridge_source`,
  never anything this SEAM document's own checks reference (those are
  about `engaged_criticism_policy`/`preparation.py`'s call site from
  tranche 2, untouched here).
- `CON-run-identity.md`, `CON-schools.md`, `SEAM-bridge-x-manifest.md`,
  `SEAM-llm-x-manifest.md`, `SUB-manifest.md`, `INV-frozen-surfaces.md`
  — flagged solely for tranche 2's own commits (`9607f739`, `f642f980`),
  already resolved in tranche 2's own delivery; not this tranche's
  responsibility, re-verified clean regardless.
- `SEAM-harness-x-verification.md`, `SUB-verification.md` — flagged for
  `2456da55`, a commit predating both tranches, unrelated; not this
  tranche's responsibility.

New map checks added by this change: one, in `CON-authority.md`'s new
"Adjacent, not authority" section, pinning `engaged_bridge_source`'s
construction through `BridgeConfig` (reuses S1's own check verbatim,
not a duplicate).

## Requirement sweep

R1 (behavior — "Change BridgeConfig's defaults to equal the values the
hard-coded dict actually runs with TODAY"): **NOT implemented as
literally worded, by explicit operator decision.** Amendment 1 records
the operator choosing to build `engaged_bridge_source()` from
`BridgeConfig` via an explicit-override instance instead, leaving
`BridgeConfig`'s shared class defaults untouched — R1's underlying goal
(stop the hard-coded dict silently drifting from `BridgeConfig`) is
achieved via R2's mechanism. Disposition: **done-with-amendment**
(Amendment 1, operator's verbatim words: "Build from BridgeConfig,
don't flip the shared default").

R2 ("Make engaged_bridge_source() build its result from BridgeConfig
instead of the hard-coded dict"): demonstrated by S1 — the function now
constructs a `BridgeConfig` instance and projects onto the same 5 keys.

R3 ("Net behavior change must be ZERO. Prove it with a test asserting
the new path produces exactly the dict the old code hard-coded"):
demonstrated by S1's own existing-test check (unchanged, passing) and
S3's new test (the "built through `BridgeConfig`" property).

R4 ("full gate 0 failed"): demonstrated above — PASS, isolated,
reproduced twice (step 9, this validation pass).

R5 ("root sweep byte-identical"): demonstrated above — PASS, reproduced
twice (step 10, this validation pass), both byte-identical against
tranche 2's own last accepted capture.

R6 ("Map updated in the SAME commit as the code"): demonstrated — code
(`v6_policy.py`), test (`test_v6_policy_preset.py`), and map
(`CON-authority.md`) all landed together in commit `e15103d8`.

R7 ("FLIPPING ANY VALUE TO BridgeConfig's OLD defaults is the
operator's decision, never yours"): held — no value was flipped to an
old default; `BridgeConfig`'s defaults are untouched entirely (S2), and
nothing was flipped in either direction. `PARKED.md`'s inherited note
(from tranche 2, carried into this tranche's own `PARKED.md` if
extended) covers this territory; no new "should have been the old
default" candidate was found or acted on here.

R8 ("Route: dr-change-orchestrator, one tranche, quote this message
verbatim in REQUEST.md"): done — REQUEST.md quotes the full message
verbatim.

R9 ("Read CLAUDE.md first, then proceed with tranche 3 per REQUEST.md's
my authorization"): done — session preflight re-run at this
continuation's actual start (git log, fetch/resync, `deepreason`
importable, env file check) before REQUEST.md was captured.

## Assumptions carried

A1 (Q2): the new test lands in `tests/test_v6_policy_preset.py`, one
new function, alongside the existing (unchanged) bridge-source test.
A2 (Q3): no `BridgeConfig` field type or bounds changes — moot under
Amendment 1.
A3 (Q4, frozen-surface reasoning): no code change to `run_manifest.py`,
`qualification.py`, or any frozen surface — verified directly (SPEC.md's
"Key technical finding") and re-confirmed by this pass's empty
frozen-surface diff.

## Verdict: PASS

Every acceptance check (S1-S6), the full gate (3292 passed, 0 failed,
isolated, reproduced twice), the root sweep (42 rows / 11 ERROR,
byte-identical, reproduced twice), all five `docs_verify` modes, and
all nine requirements (R1-R9, with R1's disposition explicitly recorded
as "not implemented as literally worded, by operator decision, per
Amendment 1") pass. The frozen-surface diff is empty — no operator
approval gate needed, unlike tranche 2. Ready for `dr-deliver-change`.
