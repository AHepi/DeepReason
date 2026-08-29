# DELIVERY.md — config carriage (P15, road A)

Requirement-by-requirement against the operator's verbatim words in
`REQUEST.md`.

## The headline

**A configuration can now turn on the gates it names.** Measured on this tree:

| | before | after |
|---|---|---|
| dropped fields that reach a manifest-launched run | **0 of 25** | **24 of 25** |

The 25th, `CHANNELS_DISABLED`, is host-owned on the managed path and
unreachable for a reason outside this cone — parked **P21**.

## Requirement by requirement

| req | the operator's requirement | verdict |
|---|---|---|
| **R1** | a configuration must be able to turn an echo-dropped gate ON | **MET.** 24 of 25 round-trip; 0 of 25 before |
| **R2** | carriage must not cost a qualification battery for a switch outside the qualification subject | **MET, and better than priced.** 24 of 25 move no subject digest, byte-identical to the pre-carriage measurement |
| **R3** | where carriage IS priced, the price must be disclosed at compile time, typed and visible — never a refusal, never silent | **MET.** The notice names the requalification in the message a person reads |
| **R4** | nothing retroactive | **MET.** 72 committed manifests; the 2 that differ differ identically on the pre-change tree, and 0 reconstruct a different `Config` |
| **R5** | the behaviour must be reachable as configuration, not by editing code | **MET, narrowed.** The emitter reads a declared table and nothing else, so pricing needs no new branch — but adding the row is still an edit to a frozen-surface file, and the tranche says so rather than claiming more |

## The accepted price, stated plainly

The monitor's ruling accepted one price: *"one ~14-minute qualification
battery per home that sets `LEGACY_CRITICISM_ENABLED: false`"*.

**Re-measured, that battery is already owed today — before any carriage
exists.** Setting the field false makes `preparation.build_preparation_manifest`
compile an engaged criticism policy onto the manifest, and that moves the
qualification subject digest at HEAD. The single `MOVED` row in
`proof/price_carriage.out` is identical before and after this change.

So **carriage adds no battery anywhere.** What it changes is that the price
becomes VISIBLE, in a typed notice, and the switch becomes EFFECTIVE. The
accepted price stands as accepted; it is smaller than the ruling priced it,
not larger. Nothing is owed for the past: no committed manifest is
recompiled, and none carries a notice.

One honesty note on the word "effective". The acceptance checks measure a
round trip on the reconstructed configuration. For `JUDGE_SEATS_ENABLED` and
`ADJUDICATION_STATUS_AUTHORITY_ENABLED` that is also an effect at run time —
both have real readers in `scheduler.py`, `authority.py`, `rules/crit.py`.
For `ENGAGED_CRITICISM_AUTHORITY`, `LEGACY_CRITICISM_ENABLED` and
`SCHOOL_SEATS_ENABLED` the only readers are at COMPILE time. Parked as
**P29**, because "carried" is proven for all of them and "changes what the run
does" is proven for two.

## B1's residual finding — road A's acceptance test

> `LEGACY_CRITICISM_ENABLED: false` is NEITHER carried NOR disclosed. B1's own
> success criterion is false for it.

**Closed.** The field is carried, the runtime comes back `False`, and the
notice states its price. It was the one field the old suppression helper hid
entirely — under carriage the notice IS the road back, so suppressing it meant
"not carried", which is why that helper is deleted.

## Frozen surface

Surface 4 contacted under the standing grant, disposed row by row in
`SPEC.md` §1 BEFORE the code, and recorded in
`docs/map/INV-frozen-surfaces.md` with a re-runnable check proven RED under
three mutations. Surface 5 was reached and NOT edited: the carrier keeps the
notice code the subject payload already strips.

## Budget

Re-declared twice by the operator, at the measured figures. Final: source and
total both over their re-declared ceilings again after the review fixes, with
the same grounds — cone unchanged, the additions are correctness the review
found missing. Recorded in `SPEC.md` §6, including the fact that the change
DELETES a function, so insertions-only accounting charges it for a
replacement and credits nothing for the removal.

## What was found wrong in this tranche's own work

An independent skeptic re-ran the claims rather than reading them and found
five confirmed defects. Four are fixed here and one is parked with the
operator's decision. The most serious, and the one the operator themself
surfaced by challenging a premise:

**Carriage restored a value the manifest's own carrier field contradicted.**
`ENGAGED_CRITICISM_AUTHORITY: defended_trial` came back in the rebuilt
configuration while the manifest held `observe_only`, and the notice's own
pointer sent a reader to the field that disagreed. The cause is not carriage:
a second switch, `ADJUDICATION_STATUS_AUTHORITY_ENABLED`, silently overrides
the setting that names the gate. That is the P10 shape one layer above the
one P15 just repaired, and it is parked as **P28** with all three roads
priced, on the operator's decision that changing what criticism may do to a
claim's status needs its own tranche and its own evidence.

Disclosed in the meantime: the notice states the disagreement in words, and
its pointer is dropped, because a pointer that sends a reader to a
contradicting field is worse than no pointer.

## Parked

**P28** the silent authority gate · **P29** three switches with no run-time
reader · **P30** the serializer's end-to-end guard lives in a map check rather
than in the gate every tranche runs · **P21** (inherited) the host-owned
override.
