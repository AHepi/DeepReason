# DELIVERY.md — config carriage (change P15)

Requirement-by-requirement reconciliation against `REQUEST.md`, whose
authority is the operator's own words. Gate evidence in `VALIDATION.md`.

## The operator's words, and what was built

> "My intention was that configuration of seats need to be able to turn gates
> on and off at will. Meaning no limits to what model you place where. It also
> means that when and if I decide to replace schools with something different,
> those flags don't gate seat configuration paths. Gates are always optional:
> with warnings."

The 2026-08-28 tranche delivered the WARNINGS. This one delivers the **at
will**: a configuration can now turn on the gates the manifest's engine-config
echo drops.

**Measured, on this tree, before and after:**

| | dropped fields that reach a manifest-launched run |
|---|---|
| before this tranche | **0 of 25** |
| after | **24 of 25** |

## R-by-R

### R1 — a configuration must be able to turn a dropped gate ON — **MET**

`proof/roundtrip_carriage.out`: 24 of 25 fields round-trip through
`config_from_run_manifest` at the value the operator set, including
`JUDGE_SEATS_ENABLED`, `ADJUDICATION_STATUS_AUTHORITY_ENABLED`,
`SCHOOL_SEATS_ENABLED`, `ENGAGED_CRITICISM_AUTHORITY` and `DISCHARGE_POLICY`.

Proven on the operator's OWN committed configuration, not only on a fixture:
`tests/test_single_run_path.py::test_the_grounded_tranche_config_enters_through_the_new_door`
now asserts that all **five** switches that config sets reach the run.

**The 25th is not delivered, and this is stated rather than rounded up.**
`CHANNELS_DISABLED` cannot be carried on the managed path, because
`preparation._config_for_profile` lists it among seven HOST-OWNED fields and
overwrites the operator's value before compile. That is the already-parked
**P21**, it needs frozen surfaces 4 AND 5, and it is why the reachable count
is 24 and not 25.

### R2 — carriage must not cost a battery for a switch outside the subject — **MET**

`proof/price_carriage_after.out` is identical to the pre-carriage run: 24
fields SAME, 1 MOVED. The carrier rides a notice that
`qualification.py::qualification_subject_payload` already strips before
digesting, so the fingerprint a home requalifies on cannot move because of
carriage. The drop list itself is untouched, so `source_config_hash` is
byte-identical at every schema version.

The four committed exclusion tests (Part B/C/D/E, `S2a/S2b/S2d`, `C9`) were
read before designing, as the P15 brief instructed, and are ANSWERED rather
than routed around: they assert a raw `Config` field NAME must not appear in
the subject payload, and after carriage they still pass, unmodified.

### R3 — where carriage IS priced, the price must be typed and visible — **MET**

A configuration setting `LEGACY_CRITICISM_ENABLED: false` compiles — never a
refusal — and its notice reads:

> `LEGACY_CRITICISM_ENABLED=False is not carried by this manifest's engine
> config and is restored at run time from this notice; carrying this value
> engages the criticism policy, which changes the qualification subject; this
> home requalifies once (~14 minutes)`

**The accepted price, stated plainly.** The monitor accepted "one ~14-minute
qualification battery per home that sets `LEGACY_CRITICISM_ENABLED: false`".
Re-measured on this tree, that battery is **already owed today**, before any
carriage exists: setting the field false makes `preparation` compile an
engaged criticism policy onto the manifest, which moves the qualification
subject digest at HEAD (`proof/price_carriage.out`, the single `MOVED` row).

**So carriage adds no battery anywhere.** What it changes is that the price is
now VISIBLE and the switch is now EFFECTIVE. The accepted price stands as
accepted; the measurement makes it smaller than it was priced, not larger, and
nothing is owed retroactively.

### R4 — nothing retroactive — **MET**

72 committed `run-manifest.json` files; **none carries any compile notice**, so
none carries a carried value, so `config_from_run_manifest` returns for each
exactly what it returned before. `proof/manifest_inertness_probe.py` run on
both trees returns the same 2 differing manifests — a pre-existing difference,
delta zero. No committed manifest is recompiled and no battery is owed for the
past.

### R5 — reachable as configuration, not by editing code — **MET**

`_CARRIAGE_REQUALIFIES` is a declared table: a future priced field is a ROW,
not a branch. Pinned by
`test_the_priced_field_table_is_data_not_a_branch`.

## What this tranche found that it did not fix

- **P21** — the seven host-owned overrides are silent. Reproduced
  independently here (it is why `CHANNELS_DISABLED` is uncarriable) and left
  parked: disclosing a host-owned override needs frozen surfaces 4 AND 5.
- **A re-measurement disagreement with the ruling's own cost line**, recorded
  in `SPEC.md` §4 and above: the priced battery is pre-existing, not caused by
  carriage.

## Frozen surface

`run_manifest.py`, surface 4. Grant disposed row by row in `SPEC.md` §1 BEFORE
the file was touched (`63167a110`, one commit earlier than the code), and the
contact recorded in `docs/map/INV-frozen-surfaces.md` with a re-runnable check
in the same commit as the code. The check was proven RED under three
mutations — serializer removed, read half removed, drop line removed — and the
tree verified byte-identical afterwards.
