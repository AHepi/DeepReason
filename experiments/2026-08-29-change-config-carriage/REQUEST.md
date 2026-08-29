# REQUEST.md — config carriage (change P15)

Tranche re-run 2026-08-29 after the original lane's work was lost with its
container (`experiments/2026-08-29-ultracode-batch-1/LOSS.md`). The captured
request, the priced roads and the monitor's ruling all survived on `main`;
only the implementation and its `proof/implementation.patch` did not.

## Authority — the operator's verbatim words

The change traces to the operator's law of 2026-08-28, quoted in full in
`CLAUDE.md`. The load-bearing sentences, verbatim:

> "My intention was that configuration of seats need to be able to turn gates
> on and off at will. Meaning no limits to what model you place where. It also
> means that when and if I decide to replace schools with something different,
> those flags don't gate seat configuration paths. Gates are always optional:
> with warnings."

The 2026-08-28 disclosure tranche
(`experiments/2026-08-28-defect-manifest-config-disclosure/`) delivered the
FIRST limb of that law — the silence. It did not deliver the second: a
configuration still cannot turn those gates ON, because the manifest's
engine-config echo drops the fields that carry them.

## Numbered requirements

- **R1** — A configuration that sets one of the echo-dropped behavioural
  switches must be able to turn that gate ON in a manifest-launched run.
  Today it cannot, by any route.
- **R2** — Carriage must not cost a qualification battery for a switch whose
  effect is not part of the qualification subject. The three committed
  exclusion tests state this correctly and the design must ANSWER them, not
  route around them.
- **R3** — Where carriage IS priced, the price must be DISCLOSED at compile
  time, typed and visible — never a refusal (all-configurations law,
  2026-08-12) and never silent (the 2026-08-28 law above).
- **R4** — Nothing retroactive. No committed manifest is recompiled, no
  battery is owed for the past, and a manifest carrying no carriage record
  must behave byte-identically to today.
- **R5** — The behaviour must be reachable as configuration, not by editing
  code (modularity law, 2026-08-26).

## The monitor's ruling — recorded verbatim, before the code lands

Two things were decided above this tranche. Both are recorded here as given,
in the monitor's own words:

> **STOP 2 (Lane B2, P15 carriage — 94/90 source, 513/420 total): BUDGETS
> RE-DECLARED at the measured figures, same grounds discipline (one missed
> helper, no scope creep). And the ROAD IS DECIDED: **ROAD A — carry the 25
> echo-dropped settings.** Authority: the operator's 2026-08-28 law verbatim
> ("configuration of seats need to be able to turn gates on and off at will …
> Gates are always optional: with warnings"); road A delivers it for 23 of 24
> reachable switches at zero qualification cost, and the ONE priced switch —
> LEGACY_CRITICISM_ENABLED=false, one ~14-minute qualification battery per
> home that sets it — is an ACCEPTED, DISCLOSED price, stated in DELIVERY.md.
> Nothing retroactive: no committed manifest is recompiled, no battery is owed
> for the past. B1's residual finding (LEGACY_CRITICISM_ENABLED neither
> carried nor disclosed — the exact field the price analysis flagged) is road
> A's acceptance test: after carriage, that field is carried, and a config
> setting it compiles with the price visible, never silently.

And, on the diff budget, the same discipline the sibling tranche records:

> Condition: the re-declaration and grounds are recorded, and
> `tools/diff_budget.py` stays armed at its normal ceiling for every future
> tranche — this is a re-declaration, not a repeal.

## The priced roads, as measured before the ruling

Carried forward from `BATCH.md` §2 so the ruling can be read against the
numbers that produced it. Measured on all 8 committed operator configs, with
a control row proving a defaults-only configuration is byte-identical to
today.

| road | carries | configs whose fingerprint moves | cost |
|---|---|---|---|
| **A — narrow** | the 25 settings the echo already drops | 7 of 8, all to ONE fingerprint | one battery per home that sets `LEGACY_CRITICISM_ENABLED: false`; **zero for every other switch** |
| **B — full** | the whole config file bar 7 profile-owned fields | 8 of 8, four fingerprints | one battery per home per distinct config |
| **C — warn only** | nothing | 0 of 8 | zero — and still cannot turn a gate ON |

**Road A is the ruling.** This tranche RE-MEASURES the table rather than
inheriting it; where the re-measurement disagrees, the re-measurement wins
and the disagreement is recorded.

## Frozen surface

`src/deepreason/run_manifest.py` is frozen surface 4. The grant stands as
originally granted, CONDITIONAL on the granted-contact discipline: the full
disposition in `SPEC.md` before implementation, and the contact recorded in
`docs/map/INV-frozen-surfaces.md` with re-runnable checks, in the same
commit.

## Offline

No provider credential exists in this container. Every claim is a
compile-time or read-time property of committed code and evidence.
