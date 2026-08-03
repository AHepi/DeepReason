# Spec for: rung 2, tranche 3 — unify the bridge settings
Traces: every item cites R/C numbers. Untraceable items are bugs.

Map preflight: `DR-CON-authority` and `DR-INV-frozen-surfaces` (same
precedent section as tranche 2 — "Where authority is allowed to live
instead" — applies by analogy: a preset's compiled behavior belongs on
`Config`, and this tranche's whole point is making `engaged_bridge_
source()` actually USE the `Config` home that already exists,
`BridgeConfig`, instead of bypassing it). `src/deepreason/v6_policy.py`
and `src/deepreason/preparation.py` are already `Owns:`-listed by
`docs/map/CON-authority.md` (added in tranche 2) — no new map document
is needed; this tranche extends the existing one further, or extends
`docs/map/CON-schools.md`/`SUB-manifest.md` if a bridge-specific
document turns out to be more appropriate (decided in S5 below).

## Amendment 1's resolution, restated for this spec

`engaged_bridge_source()` must build its result from `BridgeConfig`
(R2), proven to produce zero net behavior change (R3), WITHOUT changing
`BridgeConfig`'s shared class-level field defaults (which stay
`mode="legacy_thesis"`, `max_schema_repair_attempts=2`, `max_grounding_
repair_attempts=4`, `output_section_limit=32` — verified fresh against
the current tree: `python3 -c "from deepreason.config import
BridgeConfig; [print(n, '=', f.default) for n, f in
BridgeConfig.model_fields.items()]"`). R1's literal instruction to
"change BridgeConfig's defaults" is NOT implemented as first worded;
its underlying goal (stop the hard-coded dict silently drifting from
`BridgeConfig`) is achieved by building `engaged_bridge_source()`
FROM a `BridgeConfig` instance instead.

**Correcting a factual count carried over from the earlier
inventory**: the hard-coded dict (`v6_policy.py:179-185`) differs from
`BridgeConfig`'s shared defaults on **4 of its 5 keys**, not "three of
five" — `mode` (`legacy_thesis` → `grounded_two_stage`),
`max_schema_repair_attempts` (`2` → `1`), `max_grounding_repair_
attempts` (`4` → `0`), `output_section_limit` (`32` → `4`) all differ;
only `grounding_review` (`True` → `True`) already matches. Verified via
direct field inspection above and `v6_policy.py:179-185`'s current
literal. This correction changes nothing structurally — it is a factual
correction to INVENTORY.md's Group B count, noted here since SPEC.md is
where corrections to earlier readings get written down.

## Key technical finding (verified, not assumed — per tranche 2's own
lesson about false inferences)

Whether `engaged_bridge_source()` returns a 5-key dict (today) or a
full `BridgeConfig(...).model_dump()` (14 keys), the CONSTRUCTED
`Config.bridge`'s serialized form (`config.model_dump(mode="json")`)
is byte-identical either way — verified directly:

    python3 -c "
    from deepreason.config import Config, BridgeConfig
    five_key = {'mode': 'grounded_two_stage', 'grounding_review': True,
                'max_schema_repair_attempts': 1,
                'max_grounding_repair_attempts': 0,
                'output_section_limit': 4}
    c1 = Config(bridge=five_key)
    full = BridgeConfig(mode='grounded_two_stage', grounding_review=True,
                         max_schema_repair_attempts=1,
                         max_grounding_repair_attempts=0,
                         output_section_limit=4).model_dump()
    c2 = Config(bridge=full)
    assert c1.model_dump(mode='json') == c2.model_dump(mode='json')
    print('IDENTICAL')
    "
    -> IDENTICAL

This is because `_source_config_data`/any `model_dump()` call operates
on the fully-CONSTRUCTED `Config` object's `bridge` field (a
`BridgeConfig` instance), never on the raw dict originally passed to
construct it — pydantic fills every unset field from `BridgeConfig`'s
own class defaults regardless of whether the caller's dict had 5 keys
or 14. **This settles Q4: no golden-hash risk, no frozen-surface touch,
regardless of which key-shape `engaged_bridge_source()` internally
returns** — resolved by direct verification, not by inference (the
mistake tranche 2's Amendment 2 made once already).

## Resolving Q1-Q4 (dr-ask-the-right-question applied; record first)

**Q1 (current values)** — resolved by direct re-read, see the
Amendment-1-resolution section above and the corrected count.

**Q2 (test location)** — resolved from the record:
`tests/test_v6_policy_preset.py::test_engaged_bridge_source_enables_the_
reviewed_grounded_bridge` (lines 68-82) ALREADY asserts
`engaged_bridge_source() == {the exact 5-key dict}` — this is, word for
word, R3's own required proof ("a test asserting the new path produces
exactly the dict the old code hard-coded"), and it stays PASSING
UNCHANGED under this spec's design (S1 preserves the 5-key return
shape). No new test is needed to satisfy R3's literal words; ONE new
test is added anyway (S3) to make the "built THROUGH `BridgeConfig`,
not merely coincidentally identical" property explicit and falsifiable
— matching tranche 2's own precedent of adding one new test per switch,
in the same dedicated file. Recorded as **A1**.

**Q3 (field types)** — moot under Amendment 1: no `BridgeConfig` field
default or type changes at all. Recorded as **A2**.

**Q4 (golden-hash risk)** — resolved above by direct verification: no
risk, no frozen-surface touch. Recorded as **A3**.

No reading above differs materially enough to warrant a further stop.
**Questions for operator: none** (Amendment 1 already resolved the one
material fork this tranche had).

## Items

S1 (R1, R2, R3, Amendment 1): Change
`src/deepreason/v6_policy.py::engaged_bridge_source()`'s body from a
bare literal dict to building the same 5 values through a validated
`BridgeConfig` instance, keeping the function's return type and exact
5-key shape unchanged:

    def engaged_bridge_source() -> dict:
        """...(docstring unchanged)..."""
        override = BridgeConfig(
            mode="grounded_two_stage",
            grounding_review=True,
            max_schema_repair_attempts=1,
            max_grounding_repair_attempts=0,
            output_section_limit=4,
        )
        return override.model_dump(
            include={
                "mode",
                "grounding_review",
                "max_schema_repair_attempts",
                "max_grounding_repair_attempts",
                "output_section_limit",
            }
        )

Requires importing `BridgeConfig` into `v6_policy.py` (check it is not
already imported under a different alias before adding).
`BridgeConfig`'s shared class defaults (`config.py:193-222`) are NOT
touched — this satisfies R2 ("build its result from BridgeConfig
instead of the hard-coded dict") while Amendment 1 forbids touching R1's
literal "change BridgeConfig's defaults" instruction.
accept: `python -c "import inspect; from deepreason import v6_policy as p; src = inspect.getsource(p.engaged_bridge_source); assert 'BridgeConfig(' in src"`
AND `python -c "from deepreason.v6_policy import engaged_bridge_source as f; assert f() == {'mode': 'grounded_two_stage', 'grounding_review': True, 'max_schema_repair_attempts': 1, 'max_grounding_repair_attempts': 0, 'output_section_limit': 4}"`
AND `python -m pytest tests/test_v6_policy_preset.py -k test_engaged_bridge_source_enables_the_reviewed_grounded_bridge -q` 0 failed (the EXISTING test, unchanged, still passes — this is R3's own required proof).

S2 (Amendment 1, explicit non-goal): `BridgeConfig`'s class-level field
defaults in `src/deepreason/config.py` (lines 193-222) receive NO
changes. This item exists to make the non-change checkable, not just
assumed.
accept: `git diff --stat <tranche-base>..HEAD -- src/deepreason/config.py` is EMPTY (zero lines changed in that file across this whole tranche) AND `python -m pytest tests/test_config_scratch_bridge.py -q` 0 failed, specifically `test_safe_defaults_are_bounded_and_features_remain_opt_in` still asserting `config.bridge.mode == "legacy_thesis"`.

S3 (R3): Add ONE new test to `tests/test_v6_policy_preset.py` (A1)
making the "built through `BridgeConfig`" property explicit: assert
`engaged_bridge_source()` produces the same dict as directly
constructing `BridgeConfig(mode="grounded_two_stage",
grounding_review=True, max_schema_repair_attempts=1,
max_grounding_repair_attempts=0,
output_section_limit=4).model_dump(include={...same 5 keys...})`, i.e.
prove the function's output equals a freshly-built `BridgeConfig`'s
projection onto those 5 fields — not merely equal to a second hard-coded
literal (which would just duplicate the risk this tranche removes).
accept: `python -m pytest tests/test_v6_policy_preset.py -q` 0 failed,
new test named and collectable.

S4 (R2, golden-hash verification — proving A3, not just asserting it):
run the full set of pinned canonical-hash / incident-fixture goldens
that tranche 2's Amendment 2 discovered are sensitive to `Config`
construction, to directly confirm zero drift (belt-and-braces beyond
S1's own dict-equality check, since this is exactly the class of risk
that bit tranche 2).
accept: `python -m pytest tests/test_run_manifest_v4.py tests/test_run_manifest_v5_inquiry.py tests/test_incident_wave_a_v2_fixtures.py tests/test_v6_policy_preset.py tests/test_v6_engaged_public_defaults.py tests/test_config_scratch_bridge.py -q` 0 failed.

S5 (R6): Update `docs/map/CON-authority.md` in the SAME commit as S1 and
S3: this document already owns `v6_policy.py` (added in tranche 2 for
`ENGAGED_CRITICISM_AUTHORITY`) — extend its existing content to note
that `engaged_bridge_source()` now builds through `BridgeConfig` rather
than a bare literal, and why (drift-prevention, not a new `Config`
knob — no new field, no new "Where it lives" row needed, since
`BridgeConfig` was ALREADY a documented `Config` home before this
tranche, just bypassed). Add one new checked claim proving `engaged_
bridge_source()` constructs through `BridgeConfig` (reusing S1's own
accept check, not duplicating it) and, if `CON-authority.md` is judged
the wrong home on reflection (it is about the AUTHORITY concept
specifically, not general preset-construction hygiene), route this to
whichever `docs/map/` document actually owns the bridge/preset
relationship instead — decided during `dr-plan-steps`, not guessed here,
since `INDEX.md` should be consulted fresh rather than assumed.
accept: `python tools/docs_verify.py` 0 failed AND `--audit` 0 findings
AND the new claim's check references `v6_policy.py::
engaged_bridge_source` by name.

S6 (R4, R5): Full gate and root sweep after S1-S5 land: `python -m
pytest tests/ -q -n 4` (expect ~3291 passed, 0 failed — rerun once if
only the known flake fails, per C4); `python tools/root_sweep.py`
compared against the last accepted baseline — must be byte-identical
(42 rows, 11 ERROR expected per ERRATA E5/E6/E8).

## Assumptions (operator may override)

A1 (Q2): the new test lands in `tests/test_v6_policy_preset.py`, one
new function, alongside the existing (unchanged) `test_engaged_bridge_
source_enables_the_reviewed_grounded_bridge` — not a new file, not an
edit to that existing test.

A2 (Q3): no `BridgeConfig` field type or bounds changes — Amendment 1
already forecloses any default change, and no type mismatch was found
between the hard-coded values and the field constraints (`1` and `0`
both satisfy `ge=0`; `4` satisfies `gt=0`).

A3 (Q4, frozen-surface reasoning — recorded for the operator's
visibility, not itself an open question): no code change to
`run_manifest.py`, `qualification.py`, or any frozen surface — verified
directly (see "Key technical finding" above) rather than inferred, and
re-confirmed by S4's golden-test run.

## Questions for operator

None (Amendment 1 already resolved this tranche's one material fork).

## Out of scope (explicit)

- Changing any of `BridgeConfig`'s OTHER 9 fields (`allow_partial`,
  `allow_abstention`, `require_claim_ledger`, `require_claim_uses`,
  `reviewer_seats`, `target_profile`, `ledger_role`, `composer_role`,
  `reviewer_role`) — `engaged_bridge_source()`'s dict never touched
  these; they continue to come from `BridgeConfig`'s own class defaults
  exactly as today, unchanged by this tranche.
- Flipping `BridgeConfig`'s shared class-level defaults to the engaged
  preset's values (R1's literal words) — explicitly overridden by
  Amendment 1; if a case exists for that flip later, it is the
  operator's own future decision, not implemented here.
- Rung 2's other inventory candidates (Group C env-var switches, Group D
  `STANCE_LIBRARY`) — not requested this tranche.
- The `deepreason config compile` CLI subcommand's own bare-`Config()`
  path — confirmed unaffected either way since `BridgeConfig`'s shared
  defaults are untouched; not itself modified.

## Budget

~10 lines (`v6_policy.py`'s `engaged_bridge_source` body + import),
~15-20 lines (one new test), ~15-20 lines (`CON-authority.md` update).
Total ~45-55 lines, 1 commit (code + map together per R6). Well under
the 300-line guideline. Frozen surfaces touched: none — verified
directly (Key technical finding), not assumed; `config.py` itself is
read, not written (S2 proves zero lines changed there).
