# SPEC.md — config carriage, road A (change P15)

Traces to `REQUEST.md` R1-R5 and the monitor's ruling recorded there verbatim.
Written BEFORE `run_manifest.py` is touched, as the granted-contact discipline
requires.

## 0. Map preflight

Resolved from `docs/map/INDEX.md`; the seam is read BEFORE the subsystems.

**Read first:** `DR-SEAM-capabilities-x-channels` — the only committed document
that already states what a carrier does to this exact mechanism, and two of its
checks go red BY DESIGN when carriage lands (§5).

**Then:** `DR-SUB-manifest`, `DR-CON-authority`, `DR-CON-discharge-channel`,
`DR-CON-run-identity`, `DR-CON-seats`, `DR-CON-schools`,
`DR-SEAM-llm-x-manifest`, `DR-SEAM-manifest-x-schools`,
`DR-SEAM-adjudication-x-authority`, `DR-INV-evidence-channels`,
`DR-INV-frozen-surfaces`.

## 1. Frozen-surface disposition — surface 4, granted, disposed row by row

`src/deepreason/run_manifest.py` IS frozen surface 4. The grant stands as
originally granted, conditional on this disposition landing before the code and
on the contact being recorded in `docs/map/INV-frozen-surfaces.md` with
re-runnable checks in the SAME commit.

`tools/blast_radius.py`'s own verdict, captured on the clean tree and committed
at `proof/blast_radius.json`:

```json
{
 "frozen_surface_verdict": "CONTACT",
 "frozen_surface_contacts": [
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "DIRECT", "target": "src/deepreason/run_manifest.py",
   "detail": "target file is surface path src/deepreason/run_manifest.py"},
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "SYMBOL_INDIRECT", "target": "_versioned_source_config_data",
   "detail": "'_versioned_source_config_data' referenced in src/deepreason/run_manifest.py"},
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "SYMBOL_INDIRECT", "target": "_emit_uncarried_config_notices",
   "detail": "'_emit_uncarried_config_notices' referenced in src/deepreason/run_manifest.py"},
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "SYMBOL_INDIRECT", "target": "config_from_run_manifest",
   "detail": "'config_from_run_manifest' referenced in src/deepreason/run_manifest.py"}
 ],
 "frozen_adjacent_contacts": []
}
```

### Row 1 — DIRECT, `run_manifest.py` is the surface itself

**What moves.** `CompileNoticeV1` gains one optional field, `value: str | None`,
carrying the canonical JSON of the configured value. `config_from_run_manifest`
gains one `data.update(...)` line. `_dropped_field_effect_is_compiled` is
DELETED. One helper is added on each side.

**What CANNOT move, and the measurement that makes it so.** Surface 4's own
warning is that *"admitting a value a validator previously rejected widens what
counts as a valid manifest, and every qualification subject digest derives from
the manifest"*, and that *"reading the model and not the validator is the
specific mistake to avoid here."* Taken literally:

A bare optional field is NOT safe, and this was measured before the design was
accepted rather than assumed. `qualification_subject_payload` STRIPS notices
coded `ENGINE_CONFIG_FIELD_NOT_CARRIED` but KEEPS every other notice, so a
`"value": null` appearing on an unrelated notice moves both digests:

| variant | manifest sha256 | qualification subject digest |
|---|---|---|
| HEAD (no field) | `1b6ab4e6…` | `cdb59e87…` |
| naive field, no serializer | `62c6ddc0…` | `3db1bc26…` **MOVED** |

The field therefore ships with a `@model_serializer(mode="wrap")` that OMITS
`value` from the dump when it is `None`. That omission is the safety argument,
not a tidiness choice, and `proof/notice_digest_probe.py` re-derives the table
above on demand.

**Why no committed root changes verdict.** 72 committed `run-manifest.json`
files exist and **NONE carries any `compile_notices` entry at all**
(re-measured this session). A manifest with no notice has no carried value, so
`config_from_run_manifest` returns exactly what it returns today, and with the
serializer in place a manifest with an unrelated notice serialises to the same
bytes it does today.

### Row 2 — `_versioned_source_config_data`

**Untouched.** The drop list does not change: the 25 fields stay OUT of
`engine_config_json`, which is what keeps `source_config_hash` still. Carriage
happens through the notice channel, beside the echo, never inside it. This is
the whole reason road A costs nothing.

### Row 3 — `_emit_uncarried_config_notices`

Becomes the WRITE half of the carrier. Its `criticism_policy`/`control_policy`
parameters are removed once `_dropped_field_effect_is_compiled` is deleted —
removing them is deliberate, because leaving a dead parameter is precisely the
"one missed helper" shape that overran this tranche's budget the first time.

### Row 4 — `config_from_run_manifest`

Becomes the READ half. **This is where road A owes a FRESH argument rather than
an inherited one**, and the tranche states it plainly: the 2026-08-28 grant
that built this notice bought its safety on the property that *"no read path
calls `compile_run_manifest`, so no notice attaches, no canonical byte moves,
and no stored verdict can change."* A CARRIER is read by
`config_from_run_manifest`, which IS a read path. That inherited argument does
not transfer.

The replacement argument, and it is narrower: EMISSION remains compile-time
only — `_emit_uncarried_config_notices` has exactly one caller, inside
`compile_run_manifest`. What changes is that a notice already present in a
manifest is now CONSULTED on read. For the 72 committed manifests that consult
is a no-op, because none of them carries a notice. The read is also
fail-closed: a pointer outside `/engine_config/`, a field not in the DERIVED
drop set, or undecodable JSON raises a TYPED refusal, never a silent default —
silently defaulting is the defect being repaired, and a hand-edited record must
not buy a working run (continuation-integrity law, 2026-08-29).

### Surface 5 — reached deliberately, and NOT edited

`qualification.py` is NOT in the cone. The rule it states applies directly:
*"a disclosure that a subject-excluded `Config` field was not carried must not
itself enter the qualification subject, or the exclusion is defeated by its own
disclosure."* Road A satisfies it BY CONSTRUCTION and without touching that
file: the carrier keeps the code `ENGINE_CONFIG_FIELD_NOT_CARRIED`, which is
the exact key the existing seven-line strip in `qualification_subject_payload`
removes. Renaming the code for cosmetics would contact surface 5; it is not
renamed.

## 2. The design

**The carrier is the existing notice.** It already names the field (in
`pointer`) and rides a manifest field that survives serialisation. It gains a
typed `value` slot rather than having its human-readable `message` parsed back,
because a value round-tripped through prose is fragile and the message is
written for a person.

**`_dropped_field_effect_is_compiled` is deleted.** That is how
`LEGACY_CRITICISM_ENABLED` becomes carried: under road A the notice IS the
carrier, so suppressing the notice means "not carried", which is exactly B1's
residual finding. The function's premise — that the effect is also visible in a
typed policy field — survives intact as `resolution=_DROPPED_FIELD_CARRIERS[field]`,
which the notice already carries. Deleting it makes emission UNIFORM: every
configured non-default dropped field emits exactly one carriage notice, with no
third state, which is what makes the read side total.

**The priced switch warns.** `_CARRIAGE_REQUALIFIES` is a declared table
holding the warning text for any field whose carriage changes the qualification
subject. Today it has one row, `LEGACY_CRITICISM_ENABLED`. A future priced
field is a table ROW, not a code branch (modularity law, 2026-08-26).

## 3. Acceptance checks, per requirement

| req | acceptance check |
|---|---|
| **R1** | a configuration setting any of the 24 reachable dropped switches round-trips: `config_from_run_manifest(compile(...)).FIELD == configured`, for all 25 fields |
| **R2** | the qualification subject digest is UNMOVED for all 24 unpriced fields, re-derived by `proof/price_carriage.py` |
| **R3** | a config setting `LEGACY_CRITICISM_ENABLED=false` compiles, carries the value, and emits a notice whose message states the requalification price |
| **R4** | the 72 committed manifests are byte-inert: none carries a notice, so none changes; and a manifest with an unrelated notice serialises identically to HEAD |
| **R5** | the priced-field table is data, not a branch: adding a row needs no code edit |

## 4. The re-measurement disagreement, recorded because the measurement wins

`REQUEST.md` carries the ruling's cost statement: *"one battery per home that
sets `LEGACY_CRITICISM_ENABLED: false`"*. Re-measured on this tree, that
battery is **already owed today**, before any carriage exists: setting the
field false makes `preparation.build_preparation_manifest` compile an engaged
criticism policy onto the manifest, which moves the qualification subject
digest at HEAD (`proof/price_carriage.out`, the single `MOVED` row).

So carriage adds **no battery anywhere**. What it changes is that the price
becomes VISIBLE and the switch becomes EFFECTIVE. The accepted price stands as
accepted; it is smaller than the ruling priced it, not larger, and
`DELIVERY.md` states it that way.

## 5. Map documents that ASSERT THE CURRENT DEFECT

Three committed checks pass TODAY by asserting the silent revert, and go RED by
design when carriage lands. They move in the same commit as the code; one says
so in its own assertion message.

| document | what it asserts today |
|---|---|
| `CON-authority.md:264` | `config_from_run_manifest(m).JUDGE_SEATS_ENABLED is False` after setting it True |
| `CON-discharge-channel.md:150` | `…DISCHARGE_POLICY == 'discharge-required.v1'` — *"the pop no longer discards the configured value — F-A may be fixed; re-read this section"* |
| `SEAM-capabilities-x-channels.md:137,145` | `config_from_run_manifest(m).CHANNELS_DISABLED == ()` |

`CHANNELS_DISABLED` is the 25th field and is NOT reachable through the managed
path: `preparation._config_for_profile` lists it among seven HOST-OWNED fields
and overwrites the operator's value before compile. That is parked **P21** and
stays parked. It is why the reachable count is 24 and not 25.

## 6. Budget

Re-declared by the monitor: **source 94**, source+tests+map **513**.

**Measured at implementation: source 113, total 515 — EXCEEDED on both.** Put
to the operator as a STOP with priced options. **Ruling: RE-DECLARED at
113/515**, same grounds discipline as this tranche's first re-declaration and
lane C's two.

Grounds, and one fact that had not come up before:

- **The fix DELETES a function.** `run_manifest.py` is 113 inserted / **49
  deleted** — net **+64**, comfortably inside 94. The instrument counts
  insertions ONLY, by explicit design ("a budget ceiling bounds what is
  ADDED"), so a change that removes machinery is charged for its replacement
  and credited nothing for the removal. Recorded because it will recur on any
  refactor-shaped fix.
- **The cone never moved.** Every line is inside a change site §2 enumerated.
- **16 of the 113 are pure constraint comments** and most of the remainder are
  the three new helpers' docstrings, which carry the fail-closed reasoning and
  the measured serializer argument. CLAUDE.md requires comments that state
  constraints the code cannot show; trimming them to fit a counter would trade
  a standing convention for a number.
- The total overrun is **2 lines** on a 513 ceiling.

Condition, unchanged: `tools/diff_budget.py` stays armed at its normal ceiling
for every future tranche. This is a re-declaration, not a repeal.
