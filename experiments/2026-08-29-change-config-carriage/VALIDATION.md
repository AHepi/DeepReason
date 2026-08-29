# VALIDATION.md — config carriage (P15)

Every acceptance check in `SPEC.md` §3, proven on the delivered tree.
Validation only: nothing here was patched from inside this phase.

## R1 — a configuration can turn the dropped switches ON

    $ python proof/roundtrip_carriage.py
    carried: 24/25   not carried: 1

At HEAD before this tranche: **0 of 25**. The one uncarried field is
`CHANNELS_DISABLED`, host-owned on the managed path — parked **P21**, and the
reason the reachable count is 24 and not 25.

**PASS.**

## R2 — carriage costs no qualification battery

    $ python proof/price_carriage.py
    MOVED   (1): ['LEGACY_CRITICISM_ENABLED']
    SAME    (24): 24 fields

Byte-identical to the same probe run BEFORE carriage existed. The one field
that moves the subject digest moved it already, at HEAD, because `preparation`
compiles an engaged criticism policy for it.

**PASS** — and the price is SMALLER than the ruling priced it: carriage adds
no battery anywhere.

## R3 — the priced switch compiles, carries, and states its price

    LEGACY_CRITICISM_ENABLED=False … restored at run time from this notice;
    carrying this value engages the criticism policy, which changes the
    qualification subject; this home requalifies once (~14 minutes)

Never a refusal, never silent.

**PASS.**

## R4 — nothing retroactive

    $ python proof/manifest_inertness_probe.py
    72 manifests, 2 differ

The SAME 2 differ on the pre-change tree — delta zero. An independent
re-verification compared the reconstructed `Config` field-by-field across both
trees: **0 manifests differ**.

    $ python proof/notice_digest_probe.py
    manifest sha256  : 1b6ab4e6…   subject digest : cdb59e87…

Byte-identical to HEAD. The naive variant (no serializer) moves both.

**PASS.**

## R5 — pricing a field is a table row, not a code branch

`test_pricing_a_field_is_a_table_row_not_a_code_branch` prices a field the
table does not mention and watches its notice message change, then restores.

**PASS, with the claim narrowed.** An earlier form of this test pinned the
table's contents EXACTLY, which made adding a row — the thing its own
docstring called free — turn the test red. That was a pin pointing the wrong
way, caught by an adversarial re-run. The honest claim is that the EMITTER
reads the table and nothing else, so pricing needs no new branch; adding the
row is still an edit to a frozen-surface file.

## The four committed exclusion tests

All four pass. One of them was **inert** and is now not: Part B set
`LEGACY_CRITICISM_ENABLED` to its own DEFAULT, so no carriage notice was ever
emitted and the exclusion it names was never exercised — removing the strip
from `qualification_subject_payload` reddened the other three and left Part B
green. It now uses the non-default value and asserts the notice exists before
asserting the exclusion.

## Ring

    161 passed (before)  →  187 passed, 0 failed (after)

## What validation found that the implementation had wrong

An independent skeptic re-ran this tranche's claims rather than reading them,
and found five confirmed defects plus six suspects. Fixed here:

| # | defect | fix |
|---|---|---|
| C1 | carriage restored a value the manifest's own carrier field CONTRADICTED, and the notice's `resolution` pointed at the contradicting field | the divergence is disclosed in words and the pointer is dropped; the GATE that causes it is parked as **P28** on the operator's decision |
| C2 | the R5 test forbade exactly what its docstring called free | restated to what is true, and it now proves the emitter is table-driven |
| C4 | "fail-closed" was SHAPE-only: `"yes"` coerced to `True`, `"7"` to `7`, and three other cases escaped as UNTYPED `ValidationError` | strict per-field validation; all seven now give `CARRIED_CONFIG_VALUE_INVALID` |
| C5 | a comment claimed a test "below" that did not exist | corrected to name the map check that actually covers it, and that `pytest` does not run it |
| S3 | exclusion Part B was inert | uses the non-default value; proven to redden when the strip is removed |

C3 (a map check left naming a renamed test) was repaired before delivery.
P29 and P30 are parked.

**VERDICT: PASS.**
