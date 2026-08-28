# FIX — disclose every uncarried behavioural switch on the channel built for it

Tranche: `experiments/2026-08-28-defect-manifest-config-disclosure/`.
Reproduced cause: `DIAGNOSIS.md`, `REPRO.md`, `probe/repro_before.out`.

## The design, in one sentence

`compile_run_manifest` already owns a typed disclosure channel —
`CompileNoticeV1` / `compile_notices`, built by the all-configurations tranche
for exactly *"a configuration choice a prior gate would have refused at compile
time"* — so the fix emits one notice per `Config` field the engine-config echo
does not carry whose value differs from its default, and changes nothing else.

## The three roads, priced before choosing (P10's first question)

**Road 1 — carry the fields in `engine_config_json`.** REJECTED, on the
recorded price. Every dropped field enters `source_config_hash` at every schema
version, so `engine_config_json` bytes move, so every manifest `sha256` moves,
so every qualification subject digest moves and every home pays a ~14-minute
battery; 22 frozen manifest wire-byte goldens and the shipped-digest pin move
with them. This is `docs/ERRATA.md` E44 exactly — the incident the
unconditional pops exist to prevent — and the brief forbids it without pricing.

**Road 2 — a new typed disclosure block as a `RunManifest` field.** VIABLE,
and rejected only as the larger of two viable designs. Measured rather than
assumed: `qualification_subject_payload` (`qualification.py:263`) builds its
subject from `manifest.model_dump(mode="json", by_alias=True)`, and
`RunManifest._versioned_serialization` is a `@model_serializer(mode="wrap")`,
so a new `X | None = None` field paired with a `payload.pop("X", None) if X is
None` line in both the serializer and `canonical_bytes` WOULD be digest-neutral
when absent. Verified directly: `compile_notices` is `None` on a default
manifest and is already absent from the subject payload
(`"compile_notices" in subject["manifest_behavior"] == False`). But it adds a
Pydantic model, a schema-version guard, two serializer branches and a validator
to surface 4 for information the existing channel already carries.

**Road 3 — the existing `compile_notices` channel. CHOSEN.** No new field, no
new model, no new validator, no schema-version guard, no serializer branch. A
`Config` whose dropped fields are all at their defaults emits no notice, so
`compile_notices` stays exactly what it is today and every byte, `sha256` and
subject digest is unchanged. `deepreason config compile` already prints
`compile_notices` to stderr (`cli/main.py:920-921`), so the disclosure reaches
the operator with zero CLI work on the compile path.

Carriage — making the run actually take the configured value — is NOT in this
fix. It changes what seven committed configurations would do and it prices
subject digests for every non-default config, which is the operator's call.
Parked as **P15** with the one road that would work, so the decision costs a
paste.

## What changes

### 1. `run_manifest.py` — the drop set, derived rather than restated

```python
def _unconditionally_dropped_config_fields() -> tuple[str, ...]:
    """Config fields no engine-config echo carries, at any schema version."""
```
Computed once, lazily (`run_manifest` must not import `deepreason.config` at
module scope — `config_from_run_manifest` imports it inside the function for
that reason), as
`set(_source_config_data(Config())) - set(_versioned_source_config_data(Config(), 6))`.
Deriving it at the HIGHEST schema version yields exactly the unconditional
`data.pop(...)` lines and excludes `scratchpad`/`bridge`, which are popped only
below v3 and already have their own typed policy fields and their own notices
(`SCRATCH_MANIFEST_V3_REQUIRED`). Derived, not restated, so a future
`data.pop(...)` joins the disclosure automatically instead of silently
escaping it.

### 2. `run_manifest.py` — the emission, in `compile_run_manifest` only

Immediately after `engine_config = _versioned_source_config_data(data, schema_version)`
(line 3800), for each dropped field present in `data` whose value differs from
its `Config` default, emit through the existing sink:

    code       ENGINE_CONFIG_FIELD_NOT_CARRIED
    pointer    /engine_config/<FIELD>
    message    <FIELD>=<configured> is not carried by this manifest's engine
               config; the run will use <default>
    resolution (identity-only fields) the manifest field that does carry the
               effect; (behavioural fields) None

The effective value is the field's `Config` default and nothing else:
`config_from_run_manifest` is `Config.model_validate(echo)` followed by
`apply_profile_to_config`, which updates only `PACK_TOKEN_BUDGET`, and
`VS_K`/`CRIT_BATCH_K` on the compact profile — none of the dropped fields
(`llm/profiles.py:131-147`).

**Emission is compile-time ONLY.** It is not added to the `mode="after"` model
validator. Loading a committed manifest therefore produces no notice, which is
what keeps every committed root's bytes, digest and verdict fixed.

### 3. `run_manifest.py` — suppression for the three identity-only fields

`DIAGNOSIS.md` classifies 22 dropped fields as BEHAVIOURAL and 3 as
IDENTITY-ONLY. For the identity-only three the notice is suppressed when the
manifest being compiled demonstrably expresses the choice, because there the
drop list's own justification holds and a notice would be a false alarm:

| field | suppressed when |
|---|---|
| `ENGAGED_CRITICISM_AUTHORITY` | `criticism_policy is not None and criticism_policy.authority == value` |
| `LEGACY_CRITICISM_ENABLED=False` | `criticism_policy is not None` |
| `SCHOOL_SEATS_ENABLED=True` | `control_plane_policy.school_execution.mode == "route_bound"` |

Both `preparation.py`'s manifests and `tests/test_reusable_qualification.py`'s
`_manifest` compile from configs with all 25 fields at their defaults, so
neither emits anything and neither pinned digest moves.

### 4. `cli/main.py` — the warning reaches the launch, not only the compile

`_cmd_run` prints nothing from `manifest.compile_notices`, so a run launched
from a manifest someone else compiled sees no warning at the one place the
operator is watching. Three lines: `report_preflight_notices(manifest.compile_notices)`
before dispatch, on the same stderr channel `config compile` uses. Not a frozen
surface.

## Frozen-surface disposition — surface 4, granted contact

The monitor FORECAST contact with surface 4 (`run_manifest.py` — manifest
schemas and validators) and granted it conditionally, to the granted-contact
discipline `INV-frozen-surfaces.md` records (2026-08-21, -22, -23, -24, -26).
Named here, before implementation:

**What moves.** One new module-level helper and one emission block inside
`compile_run_manifest`, plus a `_DROPPED_FIELD_CARRIERS` table for the three
suppressions. **Insertions only, in one function and one new helper.**

**What CANNOT move, and does not.** No Pydantic model gains, loses or retypes a
field. No validator admits a value it previously rejected — the specific
mistake `INV-frozen-surfaces.md` §4 names ("reading the model and not the
validator") cannot arise, because no validator is touched at all. No schema
version guard changes. `_versioned_serialization` and `canonical_bytes` are
untouched, so the canonical byte contract is unchanged at every schema version.
`_versioned_source_config_data` is READ and not edited: no `data.pop` line is
added, removed or made conditional, so `source_config_hash` is byte-identical
at every schema version — the property the 2026-08-23, -26 and Rung 8 grants
each proved for themselves.

**Why no committed root changes verdict — categorically, not by sweep.** A
committed root's manifest is READ, never recompiled. Reading is
`RunManifest.model_validate_json(raw)`, which runs the model validators; the
disclosure is emitted only inside `compile_run_manifest`, which no read path
calls. So for every committed root the object constructed is bit-for-bit the
object constructed today, hence the same `canonical_bytes`, the same `sha256`,
the same `model_dump`, the same qualification subject payload, and the same
`verify_root` inputs. The class of change that could move a stored verdict —
a reader that interprets recorded bytes differently — is not in this diff. The
root sweep is retired as an instrument (operator ruling 2026-08-22) and is not
invoked; the argument above is the proof, and `probe/census_dropped_fields.py`
§3 re-derives its premise (0 of 79 committed manifests carry a notice or a
dropped field) on demand.

**What would trip the monitor's STOP, and the measurement that shows it did
not.** If any qualification subject digest or committed digest pin moves, this
tranche stops and reports before re-pinning. The two pinned digests in
`INV-frozen-surfaces.md`'s own checks —
`b9038b84efdea313…` (split-budget grant) and `f3bb65623852…` (the engaged
preset) — are re-derived at the gate; both configs sit at every dropped field's
default, so both must be unchanged. `VERIFY.md` records the measurement.

## Regression tests (mutation-proven: RED first, output committed)

`tests/test_manifest_config_disclosure.py`:

1. **`test_pt1_builder_shape_discloses_every_uncarried_switch`** — drives
   `build_manifest_pt1.py`'s exact call shape with P-T1's five switches and
   asserts one `ENGINE_CONFIG_FIELD_NOT_CARRIED` notice per switch, each naming
   the configured value and the effective value. This is the test the brief
   requires.
2. **`test_default_config_compiles_byte_identically`** — a default-valued
   config emits no such notice, and the manifest's `sha256` equals the value
   compiled on the tranche base.
3. **`test_identity_only_fields_are_silent_when_the_manifest_carries_them`** —
   a config with `LEGACY_CRITICISM_ENABLED=False` and
   `ENGAGED_CRITICISM_AUTHORITY="defended_trial"` compiled WITH a matching
   `criticism_policy` emits nothing for those two.
4. **`test_the_dropped_set_is_exactly_the_unconditional_pops`** — the derived
   set equals the `data.pop` lines in `_versioned_source_config_data`, so a
   future knob cannot escape the disclosure by being added to the drop list.
5. **`test_loading_a_committed_manifest_adds_no_notice`** — a committed root's
   manifest round-trips with `compile_notices` unchanged. This is the
   categorical argument above, made checkable.

## Map documents moving in the same commit

- `docs/map/INV-frozen-surfaces.md` — the granted contact, with re-runnable
  `check:` lines pinning that the disclosure exists, that
  `source_config_hash` is unchanged at every schema version, and that no
  dropped field leaks into the echo.
- `docs/map/SUB-manifest.md` — `compile_notices` now carries the
  uncarried-field disclosure; a `Traps` entry naming P-T1.
- `docs/map/CON-authority.md` — a `Traps` entry: the two master gates are
  dropped from the echo, so a manifest-built run takes them at their defaults
  unless a notice says otherwise.

## Stop conditions restated

Any subject digest or committed pin moves → STOP and report before re-pinning.
Contact required with any frozen surface other than 4 → STOP. Diff over ~150
production lines → STOP.

---

## Amendment 1 (2026-08-28) — a second frozen surface, discovered by measurement

Implementation of the design above turned four tests red and one of the four is
not a fixture: it is the design telling us something the design doc missed.
Recorded here BEFORE the code stands, per the granted-contact discipline.

**What was missed.** `qualification_subject_payload` builds its subject from
`manifest.model_dump(mode="json", by_alias=True)`, which includes
`compile_notices`. A notice NAMING a dropped `Config` field therefore carries
that field's name and value INTO the qualification subject — defeating, by its
own disclosure, the exclusion three committed tests exist to guarantee (Parts
C/D/E, S2a/S2b/S2d, C9). Measured: `MEASUREMENTS.md`. The rule those tests
encode is right, and this tranche does not weaken it.

**Design amendment.** One rule, seven inserted lines in
`qualification_subject_payload`: a notice whose code is
`ENGINE_CONFIG_FIELD_NOT_CARRIED` does not enter the qualification subject.
Every other notice keeps its contribution unchanged. The rule generalises the
three tests rather than special-casing around them — *a disclosure that a
subject-excluded `Config` field was not carried must not itself enter the
subject, or the exclusion is defeated by its own disclosure.*

### Frozen-surface request — surface 5, NOT GRANTED, this tranche's STOP

The monitor's disposition granted surface 4 and said: *"Any surface other than
4 → STOP."* `qualification.py` is surface 5. This is that stop, stated with the
measurement that makes it answerable:

**What would move.** Seven inserted lines inside `qualification_subject_payload`,
between the two `behavior.pop(...)` lines already there. Insertions only.

**What would NOT move, measured rather than argued (`MEASUREMENTS.md`).** Zero
qualification subject digests. The default fixture stays
`02ee7e098bb92390…`; every P-T1-shaped config stays `02ee7e098bb92390…`
instead of moving to `f40357e9e31b8768…`; a manifest already carrying an
unrelated notice stays `061efe5bdf7eb565…`. `source_config_hash` is
byte-identical at every schema version. No cache entry is invalidated, no home
owes a battery, no committed pin is re-pinned. No schema, validator, Pydantic
model, check name or record format is touched, in either file.

**The alternative if the grant is refused.** Option A in `MEASUREMENTS.md`:
7 of 8 committed configurations get new subject digests and one ~14-minute
battery each, and the three exclusion tests must be inverted — deleting a
guarantee to get green, which CLAUDE.md forbids. Option C (print, do not store)
keeps the disclosure out of the record entirely.

## Amendment 2 — one predicted fixture update

`tests/test_run_manifest.py::test_judge_seats_opt_in_does_not_bypass_cross_family_requirement`
sets `JUDGE_SEATS_ENABLED = True` and asserts the notice list equals exactly
`["SECOND_JUDGE_FAMILY_REQUIRED"]`. With the disclosure, that config also
yields `ENGINE_CONFIG_FIELD_NOT_CARRIED` for `JUDGE_SEATS_ENABLED` — which is
the new behaviour working, on the very flag the test is about. Its stated point
is that the cross-family disclosure is UNAFFECTED by `JUDGE_SEATS_ENABLED`, and
that point survives intact: the assertion becomes that
`SECOND_JUDGE_FAMILY_REQUIRED` is still present and still the only
cross-family notice, with the new disclosure named explicitly so the test
records both facts rather than fewer. Predicted here before the edit, per
CLAUDE.md's rule on fixture updates.

## Amendment 3 — a second predicted fixture update, and the best evidence in the tranche

`tests/test_single_run_path.py::test_the_grounded_tranche_config_enters_through_the_new_door`
recompiles `experiments/2026-08-12-live-grounded-extension-expansion/run-config.yaml`
— an OPERATOR's own committed configuration — through its builder and compares
the result field by field against the manifest that live run committed. With
the disclosure, the recompile gains a `compile_notices` key the August manifest
does not have, so the key-set comparison fails.

That is the fix working on real evidence rather than a fixture, and the test's
own docstring already sets the discipline for it: *"Each delta is asserted below
rather than waived — excluding a field without pinning what changed inside it is
how a second, unnoticed drift would ride along."* The update follows that
discipline: `compile_notices` is named as a new key and its CONTENTS are pinned
exactly.

What the notices say on that config is itself the measurement worth keeping.
The config sets all five switches; the recompile discloses exactly TWO —
`ADJUDICATION_STATUS_AUTHORITY_ENABLED` and `JUDGE_SEATS_ENABLED`, the two
BEHAVIOURAL ones. The three identity-only fields
(`ENGAGED_CRITICISM_AUTHORITY`, `LEGACY_CRITICISM_ENABLED`,
`SCHOOL_SEATS_ENABLED`) are silent because that builder DID re-express them, in
the manifest's own `criticism_policy` and `control_plane_policy.school_execution`
— which is the suppression rule of §3 firing correctly on a case nobody
constructed for it. The 2026-08-12 config is the difference between a builder
that carried what it could and P-T1's, which carried none of it.

The old-runs-owe-nothing law (2026-08-14) applies here exactly as the docstring
already applies it to the two earlier deltas: a committed manifest ceasing to
match a fresh compile is that law in action, not a regression.
