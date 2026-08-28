# VERIFY — against GOAL.md's success criterion

## Verdict: PASS on the goal as written; STOPPED on one grant before delivery.

## The success criterion, clause by clause

> Compiling a manifest from a `Config` with the five P-T1 switches produces
> `compile_notices` containing one typed notice per switch that the run-time
> `Config` will not carry, each naming the configured value and the effective
> value.

MET. `probe/repro_after.out`: five `ENGINE_CONFIG_FIELD_NOT_CARRIED` notices,
each naming both values, against `probe/repro_before.out`'s five reverted and
zero disclosed. The reproduction script's exit code inverted from 0 (defect
present) to 1 (no silent revert). Pinned by
`tests/test_manifest_config_disclosure.py::test_pt1_builder_shape_discloses_every_uncarried_switch`,
driving `build_manifest_pt1.py`'s exact call shape.

> and compiling from a `Config()` whose dropped fields are all at their
> defaults produces a manifest BYTE-IDENTICAL to the one today, with an
> unchanged qualification subject digest.

MET, measured. `sha256 = de66096f79454255f3b0a4db932186c8573de9000d1ddcc881fc76c6abe45322`
and subject `02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713`,
both identical to the tranche base (`probe/digests_base.txt` vs
`probe/digests_optionB_narrow.txt`). `source_config_hash` is byte-identical at
every schema version. Pinned by
`test_default_config_compiles_byte_identically` and
`test_source_config_hash_is_unchanged_at_every_schema_version`.

> Failure criterion: any committed manifest's canonical bytes, `sha256`, or
> qualification subject digest moves; or a default-valued config gains a notice.

NOT TRIPPED. Zero qualification subject digests move, for any config measured,
including P-T1's own five-switch shape (`MEASUREMENTS.md`). Committed manifests
are read, never recompiled, and reading attaches no notice — pinned by
`test_loading_a_committed_manifest_adds_no_notice` against a committed root.

## Instruments

| instrument | result | baseline | delta |
|---|---|---|---|
| `python -m pytest tests/ -q -n 4` | **4383 passed, 0 failed**, 6 skipped | 4374 passed, 0 failed | +9, exactly the new regression file |
| `python tools/docs_verify.py` | **4 failed** | 4 (3 shallow-clone `CON-run-identity`, 1 pre-existing `INV-frozen-surfaces.md:181`) | **0** |
| `probe/repro_silent_revert.py` | exit 1 (no silent revert) | exit 0 (defect) | inverted |

Raw output: `probe/full_gate.out`, `probe/docs_verify.out`,
`probe/regression_red.out` → `probe/regression_green.out`,
`probe/repro_before.out` → `probe/repro_after.out`.

The root sweep is not run: retired as an instrument by operator ruling
2026-08-22. Its place is taken by the categorical argument in `FIX.md` — no
read path calls `compile_run_manifest` — and by
`test_loading_a_committed_manifest_adds_no_notice`, which makes that argument
fail if it stops being true.

## Mutation proof

`probe/regression_red.out` was taken on a tree carrying the derived drop-set
helper and NOTHING ELSE: three of the nine tests fail, and they are exactly the
three that assert a disclosure. The other six pass RED as well as GREEN, which
is correct — they pin the half that must NOT move. `probe/regression_green.out`
is the same nine on the finished tree.

## Two fixture updates, both predicted before the edit

`FIX.md` Amendments 2 and 3. Neither weakens an assertion:
`test_judge_seats_opt_in_does_not_bypass_cross_family_requirement` now records
two notices instead of asserting there is one, and still asserts the
cross-family disclosure is the only one of its kind;
`test_the_grounded_tranche_config_enters_through_the_new_door` pins the new
key's exact contents rather than waiving it, per its own docstring's rule.

## Residue — what remains unproven or undone

1. **The grant is not given.** The tree carries seven lines in
   `qualification_subject_payload` (frozen surface 5) whose contact was
   REQUESTED, not granted. `MEASUREMENTS.md` prices the alternative. Until the
   operator answers, this tranche is not delivered.
2. **The disclosure warns; it does not carry.** Twenty-two behavioural fields
   still cannot be turned on by any configuration on any launch path. That is
   the second limb of the 2026-08-28 seat-config law and it is PARKED as P15,
   priced, with the one designed road written down.
3. **`deepreason reason` never reads the operator's config file at all**
   (`preparation._config_for_profile` synthesises one). Found here, PARKED as
   P14. It is a larger goal than this one.
4. **No live run.** This tranche is offline by construction: every claim above
   is a compile-time or read-time property, and a live run would add cost
   without adding evidence. The disclosure's behaviour under a real ladder
   launch is asserted by `test_single_run_path.py` recompiling an operator's
   own committed config, not demonstrated against a provider.

**Accepted does not mean true.** Everything above is read from the committed
record, two instruments, and 79 committed manifests at source `a40450f1c`.
