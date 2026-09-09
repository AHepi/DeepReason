# Verification — the solo road reaches a run, and the judge is optional at every seat count

Success criterion from GOAL.md, road (c) as amended by the operator's words of
2026-09-09. Everything below is a command and its output; no claim rests on a
reading of the diff.

## 1. The goal, driven end to end on real roots

`proof/stub_solo_road.py` builds the SAME one-model shape that minted zero
argumentative warrants before this tranche — one model id in every seat, a
defender, two schools, the same seed question and the same scripted critic —
compiles a v6 manifest through the ordinary configured path, and drives the
scheduler. The judge seat count and the new switch are its only variables.
Full output at `proof/SOLO_ROAD_SEAT_COUNTS.txt`.

| judge seats | `SINGLE_JUDGE_SEAT_PERMITTED` | argumentative warrants | attack edges | typed outcome on the record |
|---|---|---|---|---|
| none (role absent) | off | 0 | 0 | `trial-declined: no-judge-role` |
| one | off (the default) | 0 | 0 | `trial-declined: single-judge-seat` |
| one | on | **1** | **1** | `trial-gate-switched: single-judge-seat`, `trial-gate-switched: solo-road` |
| two | off | **1** | **1** | `trial-gate-switched: solo-road` |

Every one of the four compiled `criticism_policy.authority = defended_trial`
from `ARGUMENTATIVE_AUTHORITY=single_family_trial` — the declared value now
names the road that runs. All four roots replay with zero violations:

```
rF-0-no      violations= 0 warrants= 0 refuted= 0
rF-1-no      violations= 0 warrants= 0 refuted= 0
rF-1-permit  violations= 0 warrants= 1 refuted= 1
rF-2-no      violations= 0 warrants= 1 refuted= 1
```

The reproduction inverts: `proof/REPRO_A_config_path.txt` recorded
`argumentative: 0` and ten `trial-declined:no-critic-school` for this value.
The control is unmoved — `proof/REPRO_B_defended_trial.txt`'s road still mints
exactly one argumentative warrant, so nothing was taken from the road that
already worked.

## 2. Every gate switched says so, and no gate refuses

Compile notices, from the same four runs. At zero and one seat the manifest
carries `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED` — a NOTICE, not a refusal:
the configuration compiles, runs, and is told what it lacks. That is the
2026-08-28 law's "gates are always optional: with warnings", visible in the
manifest rather than asserted here. `CALIBRATION_RECEIPT_REQUIRED` appears in
all four: a run taking a trial road without a calibration receipt is disclosed,
not stopped. Recorded because a reader of these roots will see it and should
know it is designed behaviour, not damage this tranche did.

## 3. The stub tests, mutation-proven in both directions

`python -m pytest tests/test_solo_criticism_authority.py -q` -> **13 passed.**

Seven mutations, each reverting one behaviour this tranche added; every one is
caught, and the test that catches it is named:

| mutation | caught by |
|---|---|
| remove the compile-time translation | `test_single_family_trial_compiles_to_the_manifests_own_word`, `test_the_engaged_knob_still_passes_through_untranslated` |
| make the single-seat switch always on | `test_one_judge_seat_declines_by_default_with_its_historical_spelling` |
| drop the solo-road disclosure | `test_the_road_is_disclosed_on_the_record` |
| drop the single-seat disclosure | `test_one_judge_seat_rules_when_the_run_permits_it_and_says_so` |
| let the switch apply at zero seats | `test_the_switch_cannot_conjure_a_seat_that_is_not_there` |
| remove the granted `data.pop` line | `test_the_granted_contact_moves_no_digest` |
| record the disclosure at the seat check instead of past the declines | `test_a_permitted_lone_seat_that_never_ruled_discloses_nothing` |

The last of those was a defect in this tranche's own first draft, found by
reading the diff adversarially rather than by a failing test: the disclosure
was recorded where the seat check passed, so a trial that went on to decline
`same-school-critic` would still have carried "a lone seat ruled" on its
record. Fixed, then pinned by a test that fails if it comes back.

The fifth needed a second attempt. The first version of that test passed under
its own mutation, which means it proved nothing: with no judge role at all the
upstream role check declines first, so the seat-count guard was never reached.
The guard IS load-bearing for a different shape — a judge role configured with
an empty seat list, where `_judge_all` would dispatch seat 0 into an empty
ensemble — and the test now constructs that shape.

## 4. The frozen surfaces

Granted contact, taken: ONE `data.pop("SINGLE_JUDGE_SEAT_PERMITTED", None)`
line in `run_manifest.py::_versioned_source_config_data`. Insertions only; no
schema, validator, Pydantic model, notice code or record format touched.
Measured before the line existed and again after, byte-identical:

```
qualification subject digest (shipped fixture)
  02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713
source_config_hash(Config())  v1,v2  6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81
source_config_hash(Config())  v3-v6  2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
```

So no home requalifies for this tranche: no battery, no ~14 minutes, no ~1160
provider calls.

Frozen-ADJACENT, NOT granted and NOT touched: `llm/firewall.py` is unchanged by
this tranche (`git diff --quiet` on it exits 0), and `route_fingerprint` over a
fixed route is asserted directly at
`e00efa5d5990b5dea61dba75b88c1a62cbc60b9639d77844dd8c551128223a78`.

`CriticismPolicyV1.authority` is still the closed two-value Literal. The
Config-only word is translated at compile, never admitted to the manifest
vocabulary — which is what makes the digest claim above possible at all.

## 5. What a warrant minted this way is worth

Stated because the capability must not be read as a recommendation. The judge
law as amended (2026-08-28) measures the good regime as the unanimous
cross-independent pair: 0-2.5% false conviction. **Every looser configuration
measured over-convicts at 47-60%** — and a same-family pair, which is what a
one-model run has, is one of those looser configurations. A single seat is
looser still and has no measurement of its own at all.

So this road is a capability the operator's 2026-08-09 solo law requires to
exist, not a setting to leave on. The default is `observe_only` at every seat
count, proven rather than asserted
(`test_the_default_is_observe_only_at_every_seat_count`, driven through the
ordinary criticism rule with a default `Config` at zero, one and two seats).
Nothing here changes what counts as evidence: the seats-generate-never-evidence
law is untouched, and the criticism pack, admission, rank and the record are
byte-identical.

## Residue — what remains unproven

- **No live provider run.** Every figure above is from deterministic stubs. The
  operator supplied a key and asked for real tests; the live arm is the next
  step and is NOT claimed here.
- **A single judge seat has no measurement.** The 47-60% figure is for looser
  ENSEMBLES; nobody has measured a lone seat's false-conviction rate on this
  corpus. The switch discloses; it does not calibrate. Anyone turning it on is
  choosing an unmeasured regime, and the record will say they did.
- **The single-family MULTI-model gap is untouched** — parked with its full
  pricing at `PARKED.md` P1. This tranche closed a different road, and said so.
- **`trial_required` is still undiscoverable.** Of the three `Config` values,
  one now works on a solo run and one works only through the school-free legacy
  circuit, and no document holds the table. Parked as P2.
