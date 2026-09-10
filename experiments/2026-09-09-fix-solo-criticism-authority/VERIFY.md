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

## 6. The boundary instruments, and the two defects they caught in this tranche

Both are recorded because a verification report that only lists green is not
one. Neither was found by reading the diff; each was found by an instrument
this repo runs precisely so that a change like this cannot ship on its author's
confidence.

**`docs_verify`, run 1: 10 failed.** Three were MINE and identical in cause —
`SUB-harness.md:143`, `SUB-rules.md:134` and `SUB-scheduler.md:151` all run
`tests/test_signals.py`, and `test_every_emitted_signal_is_registered` went red
on `unregistered signals emitted by the source tree: ['trial-gate-switched']`.
The new disclosure was a string a consumer invented rather than a declared
interface, which is exactly what the modularity law's architecture test exists
to catch. Fixed by declaring it; all three checks re-run green.

The other seven are pre-existing and none is this tranche's. Six match
`docs/AUDIT_BASELINES.md`'s expected list: three `CON-run-identity.md`
git-history rows a shallow clone cannot resolve (`unknown revision`), the
`transport_failure` census, the judge-canary row that needs an unfetched
branch, and the unparseable `SEAM-llm-x-rules.md:54` check. The seventh is NOT
on that list, so it is a delta and a finding — `INV-frozen-surfaces.md`'s
record-claims check names a run root a later tranche retired by rename, and
fails with a JSON decode error three layers from its cause. Proven pre-existing
rather than assumed: the named directory does not exist, `record_claims` says
so directly, and this tranche touches nothing under that path. Parked as P3.

**The full gate, run 1: 1 failed, 5185 passed, 6 skipped (19:59). Run 2, after
the fix: 5186 passed, 0 failed, 6 skipped (18:23).** The failure
was mine and was the first fix's own shortcut:
`test_the_migration_debt_can_only_shrink`, `85 unspecified declarations, was
84`. Registering the signal in the pre-contract migration dict gave it unit and
staleness `unspecified`, and the 2026-08-14 signal-contract law says a signal
DECLARES name, unit, producer-agnostic semantics and a staleness bound —
`REC-add-signal.md` states in so many words that `unspecified` is not available
to a new signal. Re-declared properly: unit `event`, staleness `permanent`,
semantics saying what the signal is NOT evidence of. Mutation-proven: renaming
the emitted tag turns the AST scan red.

**`docs_verify`, run 2: 7 failed** — the six baseline rows plus the parked P3,
and none of mine. The three signal checks are green.

**On the `Verified-at:` stamps.** `CON-schools.md`, `CON-authority.md` and
`SUB-rules.md` are advanced to this tranche's commit: every check in each ran
and passed. `INV-frozen-surfaces.md` is deliberately LEFT STALE at `a36fc8abb`
even though its new granted-contact entry is this tranche's own, because three
of its checks are red for reasons that predate this work. A fresh stamp there
would claim the document was verified when a third of what it says about
itself could not be. `SCHEMA.md`'s rule, taken literally: a stale stamp is
honest, a false one is not.

The honest reading of both: this tranche twice reached for the cheap version of
a declared interface, and the repo's own instruments refused it twice. That is
the modularity law working, not incidental noise, and it is worth the paragraph.

## 7. The live run — the one thing a stub cannot show

Root: `runs/home-solo/runs/run-02818acc38961781e2e820d0d6b591fb`, committed.
Ladder `runs/solo_road_run.sh`, log at `proof/LIVE_LADDER.log`. Provider
`ollama/qwen3.5:397b`, one model in every seat, ONE judge seat — which is what
the managed path gives a single-model run, since `run_manifest` copies one
exact route per role and the two-seat shape needs `--blind-same-model-judges`.
So the live run is the one-seat case the operator's amendment opened, reached
by the ordinary path with no exotic flag.

SOAK: skipped, on the operator's explicit instruction of 2026-09-09 ("Soak is
only for when tokens are sparse. I'd rather get results faster with real
tests"). Recorded because CLAUDE.md's ladder rule otherwise requires one.

Qualification: 360/360 cases, tier `full`, ~6 minutes. Run: 6 cycles, 378 157
of 400 000 tokens, `state: completed`, `stop_reason: budget_exhausted` — a
CLEAN terminal under the 2026-08-29 law, with `amend_ready: true` and
`continuation_authority: true`.

The typed outcome (`proof/LIVE_RECORD_CENSUS.txt`):

```
warrants: 7  {argumentative: 6, demonstrative: 1}
attack edges: 15
   22  trial-gate-switched:single-judge-seat
   22  trial-gate-switched:solo-road
    8  trial-declined:defence-sustained
    5  trial-declined:execution-backed
    2  trial-declined:paraphrase-flip
    1  trial-declined:referential-integrity
```

**Six argumentative warrants, minted by a lone judge on a one-model run, on a
real question.** Both disclosures are on the record 22 times — once per trial —
so the road is auditable from the record alone.

**The lone seat did not rubber-stamp.** Of 22 trials it convicted 6: eight
defences were sustained, five targets were execution-backed and never reached
prose, two failed the paraphrase screen and one the referential-integrity
check. State this carefully, because it is tempting to over-read: this is a
CONVICTION RATE on unlabelled content, not a false-conviction rate. Nothing
here was planted, so nothing here says how often the seat was WRONG. It is the
first live behaviour anyone has recorded for a single-seat configuration, and
it is not a calibration.

## 8. What the live run found that the stubs could not — and it is not mine

`deepreason results --verify` reports this run `"valid": false` with 76
findings in the SECURITY channel. Seventy-five are one thing:
`transaction-authority :: work sha256:... exceeds frozen authority: unknown v6
task kind 'defended_trial_step'`.

The replay validator disagrees, and both are right about their own question:
`verify_root` returns **0 violations** — the record replays exactly. The
integrity channel is clean; it is the security channel's authority census that
does not recognise the trial's work kind, because
`verification/report.py`'s if/elif chain has no branch for
`defended_trial_step`.

**Proven not to be this tranche's**, by running the road that existed BEFORE
it: a stub driving `ENGAGED_CRITICISM_AUTHORITY=defended_trial`, with none of
this tranche's switches, shows the identical finding at the identical check
(`proof/LIVE_VERIFICATION_CHANNELS.txt`). The gap dates from the
defended-trial wiring of 2026-08-13. What this tranche changed is that a
launchable configuration now reaches a defended trial at all — so a defect that
was unreachable became visible on its first real use. Parked as P4 with the
two-root table and a ready-to-send prompt; NOT fixed here, because
`verification/` is frozen surface 3 and widening what a security check admits
is its own tranche with its own grant.

Said plainly, because it qualifies everything above: **the road works and the
record replays, but the harness's own security census currently calls every
defended trial's record invalid.** That is a real defect on the road this
tranche opened, even though it is not a defect this tranche introduced.

## Residue — what remains unproven

- ~~**No live provider run.**~~ DISCHARGED, section 7: one run, 6 cycles, 6
  argumentative warrants, clean terminal. What it did NOT do is compare against
  the same model WITHOUT the harness — the 2026-09-03 success law's no-harness
  baseline arm. This run shows the road WORKS; it says nothing about whether
  its output is materially better than a bare call, and that is the question
  the law makes the acceptance criterion.
- **A single judge seat still has no CALIBRATION.** The live run gives it a
  conviction rate (6 of 22) but no ground truth, so its false-conviction rate
  remains unmeasured; the 47-60% figure is for looser ensembles, not for one
  seat. The switch discloses; it does not calibrate. Anyone turning it on is
  choosing an unmeasured regime, and the record will say they did.
- **The single-family MULTI-model gap is untouched** — parked with its full
  pricing at `PARKED.md` P1. This tranche closed a different road, and said so.
- **`trial_required` is still undiscoverable.** Of the three `Config` values,
  one now works on a solo run and one works only through the school-free legacy
  circuit, and no document holds the table. Parked as P2.
