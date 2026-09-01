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

---

## F3 (2026-09-01) — qualification does not parallelize across endpoints, so a multi-model configuration pays each model's battery end to end

**Status: OPEN as a documentation and operations gap. Raised by the operator,
who observed that qualification is divided by seat allocation and asked why
four models were nonetheless taking so long.**

**The operator's premise is correct.** Pairs ARE seat-divided: each endpoint
qualifies only the contracts its own seats hold. Measured on this run's
compiled manifest, 23 pairs over four endpoints —

```
ollama-deepseek-v4-pro-0813   10 pairs      ollama-qwen3.5-397b   1 pair
ollama-glm-5.3                11 pairs      ollama-gpt-oss-120b   1 pair
```

No endpoint runs the whole battery. The division works.

**What the division does NOT buy is time.** `cli/doctor.py:1515-1520`:

```python
for pair in pairs:              # STRICTLY SEQUENTIAL over all 23
    cases = _case_block(pair)   # 20 cases, parallel at min(workers, 20)
```

Concurrency applies WITHIN a pair, never across pairs, so the four endpoints
never overlap. Total wall clock is the SUM over models, not the max — a
four-model configuration pays four batteries end to end even though each one
is correctly narrowed to its own contracts. Adding a model to a configuration
adds its whole battery to the critical path.

**CLAUDE.md's "~14 min, ~1160 calls" figure is silent on this**, and every
tranche that measured it was single-model with `reasoning: "none"`. A reader
budgeting a four-model run from that line will under-budget by roughly the
model count, and again by whatever thinking multiplies per call. This run is
the first to find out; the number is not wrong, its scope is unstated.

**A second, smaller contributor is this tranche's own ladder.**
`pa1_run.sh` exports `DEEPREASON_QUALIFY_CONCURRENCY=2`, from the Ollama Cloud
operations rule about owning the concurrency limit client-side. The SHIPPED
default is 4 (`doctor.DEFAULT_QUALIFICATION_CONCURRENCY`). Within-pair width is
`min(workers, PRODUCTION_CASES_PER_PAIR)`, so 2 halves the only parallelism the
battery has. That was this window's choice, not a harness defect, and it
roughly doubled the wall clock of the run in flight.

**Measurement discipline, and this window's own violation of it.** Two
per-case timings were taken to answer the operator's question — deepseek
4.2 s, glm-5.3 37.2 s per `conjecturer.turn.v6` case — and BOTH were taken
while the battery was running, competing for the same account concurrency.
`dr-drive-harness` §5b is explicit: "A surprising measurement taken under load
is not a measurement. Re-run idle before recording it, and say which run you
recorded." So the glm/deepseek ratio is SUGGESTIVE AND NOT ESTABLISHED, and it
is recorded here as such rather than quoted as a fact. A clean per-seat
latency measurement, taken on an idle box, is owed to whichever tranche next
budgets a multi-model battery.

**What would fix the operational half** (not attempted here, no authority):
qualification could run pair blocks across DISTINCT endpoints concurrently,
since distinct endpoints are distinct rate-limit subjects on this provider and
the circuit breaker is already per-endpoint. That is a design question for its
own tranche, touching `DR-SUB-manifest` (qualification is frozen surface 5) —
which is precisely why this window records it rather than touching it.

**Residue.** The sequential-pair loop is proven by reading the code and is not
in doubt. The projected duration built on it (~79 min for this configuration)
rests on the loaded timings above and is therefore soft; the run's actual
elapsed time, recorded in RESULTS.md, is the only figure worth trusting.

---

## F4 (2026-09-01) — one seat's contract exhaustion kills the whole run, and the failed terminal is not continuable

**Status: OPEN, two defects in one stop. The second one violates a standing
operator law.**

**How the run died, from the typed record and not from theory.**

```
run-status.json  state: failed
                 stop_reason: operational_failure
                 message: V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
                          /workflow/insufficient_capability_by_route_seat:
                          route seat has terminally exhausted its smallest
                          authorized contract
                 cycle: 5      tokens: 1 093 086 / 3 000 000
verify_root      violations: 0
```

`run/objects/workflow-route-seat-insufficient-capability-v1/` names the seat
exactly:

```
route_lease   role=conjecturer  seat=1  endpoint_id=ollama-glm-5.3
reason        smallest_authorized_contract_schema_exhausted
contract_id   conjecturer.atomic-candidate.v1
attempted     conjecturer.turn.v6 x5  ->  conjecturer.atomic-candidate.v1 x2
              (one compact-recovery transition, one decomposition transition)
maximum_provider_calls 5   observed_provider_calls 2   maximum_schema_repairs 4
```

So the harness did everything it was designed to do: glm-5.3 seat 1 kept
producing output its contract could not accept, the recovery ladder walked it
down — compact recovery, then decomposition to atomic candidates — and when
the SMALLEST authorized contract also failed, the seat had no capability left.

**Defect 1: one seat's exhaustion terminates the whole run.** The other
conjecturer seat was healthy: deepseek seat 0 made 30 successful
`conjecturer.turn.v6` calls and never failed once. The run held 25 accepted
artifacts, a working defended-trial circuit and 0 `verify_root` violations. A
two-seat ensemble has no seat-level degradation path — no "retire this seat and
continue on the other", no typed disclosure that the ensemble is now one seat
wide. The whole run dies with the weakest seat. That is worth questioning
precisely because the operator's ungated-seats law (2026-08-28) invites putting
ANY model in ANY seat: a configuration surface that welcomes heterogeneous
seats but terminates on the first seat that cannot hold its contract makes
heterogeneity structurally risky in a way no notice warns about.

**Defect 2, and this one is a law violation.** The operator's law of
2026-08-29, verbatim: *"clean stop. with an assurance that continuing is
possible. Too often an operational failure overlooks securing enough
checkpoints to allow relaunches or forgets to ensure continuing is possible
that trigger corrupted stops."* Its operational reading, ledgered in CLAUDE.md:
**EVERY terminal — clean or failed — must leave checkpoints sufficient for
relaunch, and a stop that cannot assure continuability is itself a defect.**

`deepreason results` on this root:

```
stop reason is resumable: no
carries the lifecycle decision `continue` resumes from: no
the run recorded this reason for refusing that receipt:
    TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL
ready for `deepreason amend` / `deepreason continue`: no
```

Five cycles of work, 1.09 M tokens, 25 accepted artifacts, a clean replay
verdict — and no operation can touch it. This is exactly the corrupted stop the
law was written against, and it is not a jailbroken record being correctly
refused: `verify_root` reports **0 violations**, so the integrity gate the same
law demands has nothing to complain about. The record is intact AND unusable.

**What it cost downstream, measured rather than asserted.** The grounded bridge
was configured correctly (`grounded_two_stage`) and the ladder DID call the
composition step — the two halves of P-S1's `bridge_events: 0` are both closed.
It still produced nothing, for a third reason neither P-S1 nor this tranche
anticipated:

```
BRIDGE_REASONING_NOT_COMPLETED: canonical run state is failed
```

So the bridge row in MODULE_COVERAGE.md reads `did-not-fire`, and the typed
reason is downstream of F4 rather than of any configuration this window chose.
Had the run terminated cleanly at its cycle budget, the composition step would
have had a completed run to compose from.

**Not fixed here.** RUN tranche, no authority over `src/`. Both defects belong
to `DR-SUB-workflow` × `DR-SUB-scheduler`, and defect 2 additionally touches
terminalization, which the operations-parity law routes through one shared
path.

**Residue.** Defect 1 is proven for THIS shape — a two-seat conjecturer
ensemble where one seat exhausts. It is NOT established that every role behaves
this way, nor that a seat-level degradation path would be safe: continuing on
one seat silently changes the topology the manifest froze, and the honest fix
may be a typed disclosure plus a clean stop rather than silent continuation.
Defect 2 is proven outright by the run's own refusal string.

---

## F5 (2026-09-01) — glm-5.3 at a 49 152-token cap takes ~20 minutes per conjecture, and the cap raise is the likely cause

**Status: OPEN as a calibration finding. Measured on the live record, idle of
any competing instrument.**

Per-call latency for `conjecturer.turn.v6`, same contract, same question, same
run, read from consecutive `log.jsonl` timestamps:

| seat | latency |
|---|---|
| deepseek-v4-pro:0813 seat 0 | 28 s, 5 s, 4 s |
| **glm-5.3 seat 1** | **1 216 s (20.3 min)** |

The call SUCCEEDED — no timeout, no typed failure, no transport fault. This is
generation speed, not breakage.

**The likely cause is this tranche's own cap raise.** The tranche instruction
asked for a completion cap high enough that hidden reasoning could not consume
it, and `run-config.yaml` accordingly set `max_tokens: 49152` against P-C2b's
evidenced 32768. P-C2b measured glm-5.2 at 32768 taking 737 s / 420 s / 460 s.
Scaling roughly with the cap lands near 20 minutes, which is what was observed.
PREREG §3 recorded this as residue before the launch — *"1800 is an
EXTRAPOLATION from the 32768 measurement, not a measurement at 49152"* — and
the extrapolation held for the TIMEOUT (nothing timed out) while
under-predicting the WALL CLOCK.

**Consequence, and it is the reason this run reached only 5 of 24 cycles in
five hours.** glm-5.3 held six seats. At ~20 minutes per generation call, a
24-cycle run is a 16–24 hour proposition at best. The operator was given the
measurement and the priced roads and chose to let it run and report at a
checkpoint; the run then died at cycle 5 on F4 before the pacing mattered.

**Residue.** ONE glm-5.3 sample at 49152, and three deepseek samples. The
cap-scaling hypothesis is CONSISTENT with P-C2b's numbers and is NOT
established — no controlled A/B at 32768 versus 49152 on this question was
run, and glm-5.3 may simply be slower than the glm-5.2 those numbers came
from. Two confounds, one sample: this is a lead for a calibration tranche, not
a finding anyone should tune a config on.

---

## F6 (2026-09-01) — the transport-failure monitor watched the wrong surface, and missed a 27% failure rate in the criticism path

**Status: OPEN. An instrument defect in THIS tranche's own monitoring, found
after the run, by reading the record rather than by the monitor.**

**What the record shows.** `run/objects/criticism-attempt-v1/`:

```
completed          11
transport_failure   4        (4 of 15 = 27%)
```

Two of the four are the same target
(`4c65c1e95b4d…`) attempted twice, so at least one artifact went
uncriticised because the transport failed on both attempts at it.

**Why the monitor did not say so.** The tranche instruction was explicit about
this exact hazard — *"15 of P-S1's 24 cycles ran against a dead provider and no
summary said so — your monitor must alert on transport-failure signatures, not
just success."* `monitor.sh` and the live watcher were built for it and both
missed it, because they classify **`llm.attempt_trace` entries on log events**:
a call counts as failed only when a trace carries an error AND the event has no
`output_ref`. A criticism attempt that fails in transport never produces such
an event at all. It produces a `criticism-attempt-v1` OBJECT with
`outcome: transport_failure`, on a surface the monitor never opened.

So the monitor reported `calls_FAILED=0` for the whole run, truthfully by its
own definition and misleadingly in fact. It watched the provider-dispatch
surface and not the work-outcome surface, and the two disagree precisely where
a failure is absorbed by a retry that also fails.

**This is the P-S1 shape reproduced inside the instrument built to catch it.**
P-S1's lesson was "a run can advance while its calls die and no summary says
so". P-A1's monitor said `0 failed` while 27% of criticism attempts died. The
generalisation worth keeping: **a failure-rate monitor must read the surface
that records OUTCOMES, not the surface that records DISPATCHES** — and for this
harness that means the `*-attempt-v1` object families, not `attempt_trace`
alone.

**What it cost this run.** Nothing that changes a verdict: the run's terminal
was `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` on a conjecturer seat (F4), not a
criticism transport failure, and `verify_root` reports 0 violations. But it
means the criticism coverage the run achieved was lower than the module census
implies — 11 completed attempts across 5 `Crit` events, not 15 — and
MODULE_COVERAGE.md's criticism row should be read with that number beside it.

**The fix, not applied here.** `module_census.py` and `monitor.sh` both belong
to this tranche, so a fix would be in scope for a follow-up — but this window
is closing on a delivered tranche and changing the census after its numbers are
committed would rewrite the evidence rather than extend it. The correct shape
is an additional census row and monitor clause reading every
`objects/*-attempt-v1/` family's `outcome` field, so a transport failure is
counted wherever the harness records one.

**Residue.** The 27% is this run's criticism path only. Whether other
`*-attempt-v1` families carried unnoticed transport failures in this or any
earlier root is UNMEASURED — the census never looked, and neither did any
predecessor's.
