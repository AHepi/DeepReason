# P-A1 findings

Dated segments. Each finding is what the record shows, and the residue is what
it does not show. A finding is not a fix: this is a RUN tranche and every entry
here becomes a parked prompt for another one.

---

## F1 (2026-09-01) — the offline soak instrument cannot exercise two modules the harness ships

**Status: OPEN. Blocks the documented launch gate for any configuration that
turns on the config referee or the grounded bridge's repair path.**

**What happened.** `python -u scripts/cycle_soak.py --case pa1` failed at its
qualification stage, before driving a single cycle:

```
[soak] QUALIFY FAILED
qualified: false   pair_count: 23   qualified_pair_count: 10
case_count: 460    first_pass_valid_count: 200
failure codes: ENDPOINT_HTTP_500 x40, CIRCUIT_OPEN_ENDPOINT_HTTP_500 x220
circuit breaker opened on BOTH generation endpoints after 20 block failures each
```

**What it is NOT.** It is not a defect in the harness, and it is not a
modularity-law violation. Every module this run turns on IS reachable by
configuration: the manifest compiles with the config referee armed
(`cadence_cycles: 6`), the grounded two-stage bridge, `grounding_review: true`,
and non-empty behavioural-contract grants on defender, judge and variator. The
49-check `preflight_pa1.py` passes against that compiled manifest. Nothing
about the LAUNCH shape is wrong.

**What it is.** The offline stub the soak drives —
`scripts/wheel_operational_smoke.py::response_for_schema`, reused by
`cycle_soak.py` rather than re-minted — has no fixture for two advertised wire
schemas, and its generic schema-synthesising fallback (`_schema_value`) cannot
satisfy either. It then raises, the loopback server answers HTTP 500, twenty
such failures trip the qualification circuit breaker per endpoint, and 220
further cases are skipped as cascade. The ten pairs that DID qualify are the
ten the stub already knew.

Reproduced directly, outside the soak:

```
config_referee_wire_contract(...)         title ConfigRefereeWireV1
  response_for_schema(...) -> AssertionError: provider fixture cannot satisfy
                              advertised schema
DirectWireContract(GroundingRepairWireV1) title GroundingRepairWireV1
  response_for_schema(...) -> AssertionError: provider fixture cannot satisfy
                              advertised schema
```

`GroundingVerdictWireV1` synthesises fine — its soak failures were cascade, not
origin. So the gap is exactly TWO schemas.

**Why the generic fallback cannot cover them.** `GroundingRepairWireV1`'s
schema is conditional: `allOf` / `if` / `then` branches make
`replacement_text`, `resolution` and `resolution_reason` required or forbidden
depending on the value of `action`. A synthesiser that walks properties
independently cannot produce a value that satisfies a cross-field implication.
`ConfigRefereeWireV1` fails for the analogous reason at its own constraints.

**Why no earlier tranche hit it.** No committed soak case turns either module
on. `pc1`, `pc2`, `pc2b` and `split-legs` leave `bridge.mode` at its shipped
`legacy_thesis`, so no grounding-repair contract is ever granted; `pr1` does the
same; and `DEEPREASON_CONFIG_REFEREE` is unset everywhere, so
`engaged_config_referee_policy` returns None and no referee contract exists.
P-A1 is the first configuration to grant either, which is what a
maximum-configuration run is FOR.

**The consequence, stated plainly.** CLAUDE.md makes a green soak a hard
precondition for any live launch, and CLAUDE.md also forbids soaking a
different shape from the one that will launch ("an instrument that soaks the
wrong shape is worse than no instrument, because it reports green"). Those two
rules together mean this configuration cannot currently reach a live launch,
and NEITHER rule should be relaxed.

**The fix, measured rather than proposed.** Two additive `title ==` branches in
`response_for_schema`, before the generic fallback. Both fixture values were
constructed and validated against the real contracts:

```
ConfigRefereeWireV1 ->
  {"verdict": "config_effective",
   "assessment": "The bounded loopback fixture observes no mistuning.",
   "cited_seqs": [0], "recommendation": "no_change"}          CONTRACT-VALID

GroundingRepairWireV1 ->
  {"action": "correct_wording",
   "replacement_text": "A conservative restatement.",
   "resolution": null, "resolution_reason": null}             CONTRACT-VALID
```

The branches are additive: no title they match is matched by any existing
branch, so every current soak case and the wheel smoke keep their exact
behaviour.

**Disposition, 2026-09-01 — APPLIED under the operator's instruction.**
`scripts/wheel_operational_smoke.py` is outside this tranche, and the tranche
instruction lists "any needed code edit" as a STOP AND ASK condition. The
window prepared the question; before it was put, the operator re-sent the
credential and instructed "Just run it". That is a decision to proceed, and
the repo's own rule is that a reaffirmed instruction is the operator's call.
The contact is therefore LEDGERED HERE rather than left silent.

What was changed: two additive `if title == ...` branches in
`response_for_schema`, placed before the generic fallback. Bounded as tightly
as the gap allows:

- neither title is matched by any existing branch, so every committed soak
  case and the wheel smoke keep their exact behaviour;
- no existing branch, no fallback, and no other function was edited;
- both fixtures are INERT by construction. The referee fixture never reports
  mistuning and never recommends a change, so a soak exercises the dispatch
  path without the referee steering the run it is soaking; the repair fixture
  takes `remove_span`, which carries no substantive field at all.

**The repair fixture took two attempts, and the first one is worth recording
because it is a trap the schema itself sets.** The first fixture used
`correct_wording`. It VALIDATED against the advertised contract and the soak
still failed on exactly that pair — 20 origin `ENDPOINT_HTTP_500`s on the
glm-5.3 endpoint, `repair_count: 1` and `scope_violations: 1` per case, and
100 cascade skips behind the reopened circuit breaker. (The referee fixture
worked first time: qualified pairs went 10 → 17 of 23.)

The cause is a gap between two different notions of "legal". The caller
NARROWS the contract to one finding status's permitted actions
(`GroundingRepairWireContractV1(_ALLOWED_BY_STATUS[status])`), but the
advertised JSON Schema still `$ref`s the FULL `CorrectionMode` enum. So a
fixture chosen from the schema alone can be structurally valid and still out
of scope — and `correct_wording` is forbidden under `MISCLASSIFIED`, the
status the production-contract doctor's own probe uses. It parsed, then
`_admit_production_probe_output` raised `BRIDGE_REPAIR_ACTION_FORBIDDEN`, the
case burned a repair turn, and the pair failed.

`remove_span` is the correct fixture for two independent reasons, both
checked rather than assumed: it is the only action present in EVERY entry of
`_ALLOWED_BY_STATUS`, so no probe the doctor can construct puts it out of
scope; and it accepts no substantive field, so it satisfies every conditional
branch of the schema by carrying nothing. Verified across all five finding
statuses: valid and in scope for each.

**The reusable half.** A stub fixture derived from an advertised schema is
not thereby in scope, wherever a caller narrows a contract below what it
advertises. Schema-validity is a necessary condition, never a sufficient one.

This is instrument maintenance, not a harness change: no `src/` file, no test
and no frozen surface is touched, and the two branches exist only so that an
OFFLINE stub can answer contracts the harness already ships.

**Residue.** Even with the two fixtures added, a green soak would prove that
the two contracts can be DISPATCHED and their responses parsed. It would not
prove that a real model produces useful referee verdicts or grounding repairs
— that is what the live run is for, and no soak can stand in for it.

---

## F2 (2026-09-01) — `hv` is structurally unreachable on ANY v6 run, under any configuration

**Status: OPEN, and this is a MODULARITY-LAW FINDING.** The tranche instruction
forecast this exact disposition for requirement R4: *"Find the configuration
that grants that contract ... If no configuration grants it, STOP and report
the same way."* No configuration grants it. Reported, not fixed.

**The correction this makes to R4, stated plainly.** P-A1 was designed on the
inference that P-S1's 171 `transaction-contract-unavailable` deferrals were
caused by its null criticism policy — because that policy is what gates the
defender/judge/**variator** behavioural-contract grants
(`run_manifest.py:2059-2077`). That inference was **half right and its
conclusion was wrong**. The missing grant was a real defect and P-A1 closes it:
`variator[0]` now holds `variator.direct.v1`. But the grant is not what the
scheduler consults, so closing it does not make `hv` measure.

**What the record shows.** `Scheduler._defer_untransactional_v6_phase`
(`scheduler/scheduler.py:696-752`) is the gate in front of every legacy model
phase. Its entire decision is:

```python
manifest = self.run_manifest
if manifest is None or manifest.schema_version != 6:
    return False
...
return True
```

It returns True for **every** v6 manifest. It never reads
`route_seat_behavioral_capability_plan`, never reads a contract grant, never
reads a route, never reads a Config field. There is no value any configuration
can carry that changes its answer. The only branch that reaches the phase is
`schema_version != 6` — and the operations-parity law (2026-08-13, ONE run
path) makes v6 the only path a current run takes.

**The two producers of `hv_set` are both behind it**, so `hv` cannot be
measured on a v6 run at all:

| producer | call site | gate |
|---|---|---|
| `run_hv_floor` | `scheduler.py:1358` (`_criticize`) | `hv-floor` / variator |
| `hv_spot_check` | `scheduler.py:2947` (`_lazy_hv`) | `hv-spot-check` / variator |

**`reach` is NOT affected, and that distinction matters.** `reach_sweep`
(`measures/reach.py:110`, called at `scheduler.py:2229` and `2479`) is
deterministic, makes no provider call, and sits in front of no gate. It runs
every cycle. P-S1's and P-R1's zero `reach_set` counts are therefore an
ordinary empirical outcome — no artifact passed a foreign problem's qualifying
criteria — and not a structural block. Correcting this half of the diagnosis is
the difference between "measure it again on a richer run" and "no run can
measure it".

**Eleven phases die on this line, not one.** Every model phase the gate
covers is dead on v6, whatever the configuration says:

```
hv-floor                      variator        rubric-trial              judge
hv-spot-check                 variator        property-design           property_designer
premise-demarcation-variation variator        property-relevance-trial  judge
premise-rent                  variator        paraphrase-audit-judgment judge
paraphrase-audit-variation    variator        pairwise-discrimination   (judge)
experiment-generator-authoring conjecturer    vision-criticism          vision_critic
```

So the run-config fields `HV_K`, `HV_MIN`, `AUDIT_PERIOD`, `GEN_PROPOSE_PERIOD`,
`GEN_MAX`, `PROP_PROPOSE_PERIOD`, `PROP_MAX`, `VISION_CRIT_PER_CYCLE` and
`ADVISORY_TRIALS_PER_CYCLE` are all live-looking knobs over phases that cannot
fire. The operator's modularity law (2026-08-26) says every behaviour a run can
vary must be reachable as configuration and that "enforced" means a check that
can fail. Here there is no such check, and a whole family of behaviours is
unreachable while its knobs still parse, compile and appear in the manifest.

**Evidence, three independent roots.**

| root | variator deferrals | `hv_set` events | `reach_set` events |
|---|---|---|---|
| P-S1 (reported in the tranche instruction) | 171 | 0 | 0 |
| P-R1 `experiments/2026-08-25-poietics-program/run` | 117 (`hv-floor` 42, `hv-spot-check` 74, `premise-demarcation-variation` 1) | 0 | 0 |
| P-C2b `experiments/2026-08-27-pc2b-symmetric-reasoning/run` | — | 0 | 0 |
| P-A1 offline soak (this tranche, contract grant PRESENT) | `premise-demarcation-variation` 1 and counting | 0 | 0 |

The last row is the load-bearing one: it carries the behavioural-contract grant
P-S1 lacked, and `hv` is still zero. The grant was necessary and is not
sufficient.

**Consequence for the Pareto frontier.** `PARETO_AXES` is
`["hv", "reach", "coverage"]` and the manifest carries it unchanged, but on any
v6 run `hv` is always absent (`state.hv.get(artifact_id, 0.0)` →
`scheduler.py:232`), so the frontier sorts on `reach` and `coverage` alone —
and on a run where no artifact reaches a foreign problem, on `coverage` alone.
This is the actual mechanism behind the "frontier inversion" the tranche
instruction lists as known-open defect D1. It is not diluted by having the
contract grant; it is unchanged by it.

**Not fixed here, and deliberately.** This is a RUN tranche with no authority
to edit `src/`. The fix is also not obvious enough to be safe: the deferral
exists because "RunManifest v6 makes the adapter fail closed on every unbound
provider dispatch", so simply removing it would trip that global guard and fail
whole roots. The real repair is to make the gate consult the behavioural
contract grant it was written to stand in for — which is a design question for
its own tranche, touching `DR-SUB-scheduler` × `DR-SUB-workflow`.

**Residue.** This finding is proven for `hv` and for the eleven phase names
above by code reading plus four roots. It is NOT proven that every one of those
eleven phases is otherwise sound — only that none of them can run. And the
consequence for judge participation is stated but not yet measured live: the
`rubric-trial` phase is deferred, so `ADVISORY_TRIALS_PER_CYCLE` cannot fire,
but the DEFENDED-TRIAL circuit reached through the criticism policy is a
different path and this finding says nothing about it. The live run is what
settles that.
