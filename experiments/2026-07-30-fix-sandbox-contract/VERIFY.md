# Verification

## Criterion 1 — the regression test

    $ pytest tests/test_simulation_compiler.py tests/test_simulation_capability_v5.py -q
    ...................................                              [100%]
    35 passed in 11.03s

    $ pytest tests/test_simulation_compiler.py::test_the_conjecturer_is_shown_the_program_contract_the_harness_enforces -v
    PASSED

Its docstring names `run-27b80f26bd398c718360e97e2a403593`. It asserts
disclosure and enforcement together rather than either alone:

  - the signature the disclosure names is built into a program and put
    through `validate_sandboxed_python_source`, which accepts it;
  - the field run's shape — that function with a script around it — still
    raises `exactly one simulate function`;
  - `declared observable missing`, the consequence the observables text
    names, is asserted to be the runner's own wording, against
    `CONTAINED_WORKER_SOURCE_V1`;
  - the declarative site enforces the same set rule
    (`compile_declarative_numeric` raises `observables differ`);
  - both the v5 and the v6 simulation-enabled schemas, rendered as
    `adapter.py:764` renders them, carry the signature, `sealed_inputs`,
    and the observables text.

So a future edit that changes the enforced signature without the
disclosed one — or the reverse — fails here rather than in the field.

## Criterion 2 — the full gate

    $ pytest tests/ -q -n 4
    3169 passed, 7 skipped in 638.72s (0:10:38)

0 failed. No assertion was weakened, nothing was skipped or xfailed, and
the only fixture touched is the one FIX.md predicted.

## Criterion 3 — the committed roots

`verify_root` over all 23 committed run roots under `experiments/`,
captured on the clean tree before the change and again after it:
**byte-identical**, full JSON reports, violation entries and all.

Remaining violations, listed by class rather than summarised away — all
pre-existing, none introduced, none masked:

    foreign-criticism   44
    run-input            1
    terminal-authority   1

    12 of 23 roots carry at least one; 11 are clean. The field run
    `run-27b80f26bd398c718360e97e2a403593` is among the clean ones,
    before and after.

The append-only record was never a party to this change: no run root's
bytes were read for anything but verification, and none were written.

## The predictions FIX.md made, checked

| Predicted before the change | Observed after |
|---|---|
| incident-wave `generated_root_sha256.A3` moves `d887b449… → 11b5aa70…` | moved, exactly that value |
| `generated_root_sha256.A1` / `.A2` do not move | unmoved |
| `descriptor_sha256` does not move | unmoved |
| semantic-freedom `tokens_per_admitted_useful_candidate` stays 784.5 | stayed; its test passes unchanged |
| no third baseline moves | none did — the gate's only failure before the fixture edit was the predicted one |
| `verify_root` unmoved across all committed roots | byte-identical |

One of the two baselines the operator pre-authorised was therefore not
spent. The authority to regenerate it stands unused rather than
consumed.

## Reproduction inverted, in the one part that should invert

    part 1a  conjecturer.turn.v5  occurrences {'simulate': 2, 'inputs': 3, 'rng': 2}   (was all 0)
    part 1b  conjecturer.turn.v6  occurrences {'simulate': 2, 'inputs': 3, 'rng': 2}   (was all 0)
    part 1c  the field run's three committed packs        still {'simulate': 0, ...}
    part 2   ValueError('sandboxed Python must define exactly one simulate function')  unchanged
    part 3   contained runner -> 'declared observable missing', missing=['stdout']     unchanged

Three of four parts had to stay still, and did. The schema the model
reads grew (v5 5232 → 6414 bytes, v6 9814 → 10996); what the harness
enforces did not move at all.

## Live attempt: none

GOAL.md did not demand live proof and explicitly declined to claim it:
capability-channel use is stochastic, so one live run that happens not to
propose a simulation would prove nothing, and one that did would confound
this change with the citation fix that landed just before it. The
credential file `experiments/live_research_2026-07-29/env` was recreated
this session as the operator's handover instructed, but the value handed
over is the literal placeholder `<my key>`, so no live run could have
authenticated in any case. Flagged rather than worked around.

## Verdict: PASS (offline)

All three of GOAL.md's criteria are met.

## Residue, stated honestly

**Nothing here shows a model writing a valid program.** What is proven is
narrower and worth stating exactly: the two rules the harness enforces
are now inside the bytes the conjecturer is shown, they are the same
rules the enforcing code applies (asserted by coupling, not by eye), and
nothing about what is enforced or already recorded moved. Whether glm-5.2
then authors a conforming `simulate` is UNPROVEN and is not offline-
decidable. The record's own warning applies: accepted does not mean true.

**The recorded denial stands.** `run-27b80f26bd398c718360e97e2a403593`
still carries its `invalid_model_program` transition and always will —
the log is append-only and was not touched. This tranche changes what
future packs say, not what past ones said.

**The declarative DSL is still undisclosed.** `model_source` now tells
the model that a `declarative_numeric_v1` source is a JSON document
rather than Python, but not what that document must contain
(`{"schema": "declarative-numeric.v1", "observables": {...}}` over a
fixed expression vocabulary). That is the same defect class as the one
just fixed, one mode over. Parked as D2c — it was not in the operator's
approval, which enumerated the `simulate` contract and the
`requested_observables` rule.

**The disclosure is unconditional.** `SimulationProposalWireV1` stays in
`$defs` even when `_omit_property` removes the `simulation_proposals`
property, so packs for runs that cannot propose a simulation now carry
~1.2 KB of contract text they cannot use. This predates the tranche —
the definition itself was already dangling — but the change makes the
dangling piece bigger. Parked as D2e.

**Two rules are now stated in two places each.** The description text and
the code that enforces it must agree, and only the new regression test
holds them together. That coupling is deliberate and it is also the
maintenance cost of this fix, stated so it is not discovered later.

**Not addressed, by design:** D2a (a capability transition still cannot
say why it denied a program); D1a (`EvidenceRefClaimV1`'s quote docstring
still describes the stricter, pre-fix rule); P4; Q1. All in PARKED.md.
