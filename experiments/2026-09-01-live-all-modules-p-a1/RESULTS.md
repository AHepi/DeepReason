# P-A1 — results

Dated honest-ledger segments. Each says what the RECORD shows and then the
RESIDUE: what remains unproven. Accepted does not mean true. A negative or
inconclusive result is recorded as one.

Model prose is never evidence here — including this window's. The admissible
evidence is `log.jsonl`, `objects/`, `progress.jsonl`, `run-status.json`,
`run-stop.json`, `REPLAY_VALIDATION.json`, `verify_root`, the compiled
manifest, and the committed instrument outputs.

---

## 2026-09-01 · Segment 1 — the configuration, and what it cost to establish

**What the record shows.** The maximum-configuration shape compiles, and every
module the tranche instruction names is reachable by CONFIGURATION rather than
by a code edit. `preflight_pa1.py` passes 50 of 50 typed gates against the
compiled `run-manifest.json` and the runtime `Config` reconstructed from it by
`config_from_run_manifest` — 49 offline plus one live catalogue check that
every seat names a model the provider actually lists.

Load-bearing values, read off the compiled manifest and not asserted:

```
criticism_policy.authority          defended_trial, 4 school bindings
behavioural contract grants         defender.direct.v1 / judgeruling.direct.v1
                                    (both judge seats) / variator.direct.v1
bridge_policy.mode                  grounded_two_stage, reviewer grounding_reviewer
inquiry.simulation                  enabled, simulation.container.v1,
                                    12 requests / 12 executions
inquiry.research                    enabled, web.contained.v1,
                                    arxiv.org + en.wikipedia.org
inquiry.attached_evidence           enabled, 16 sources / 8 MiB, 0 bound
inquiry.config_referee              enabled, cadence 6
control_plane.school_execution      route_bound, 4 bindings round-robin
scratch_policy.enabled              true
NEAR_DUP_EPS / RESEED_DIST_MIN      0.2608 / 0.0401 (calibrated)
open_loop_notices(bound_roles)      ()  -- zero of seven policy signals open-loop
```

**Two things this segment establishes that were not known before it.**

The near-duplicate threshold is now a MEASURED value rather than an unarmed
default. `deepreason calibrate` was run on the configured neural embedder
(fingerprint `d6e3599ce0377000`) over three independent committed live roots,
and all three agree: planted-duplicate ceiling 0.2608, within-problem sibling
p10 between 0.032 and 0.040. The recommendation is re-derivable by that
command, which is why it was preferred to any hand-picked number.

And a near-miss was caught before it could produce a green-looking dead run.
The first probe compile passed the compiler's OWN derived capability policy and
reported `simulation_enabled: false`, `research_enabled: false` with every
switch in `run-config.yaml` already set — the exact shape P-S1 ran in.
Compiling without an explicit `inquiry_capability_policy` derives an
ALL-DISABLED policy. The explicit engaged preset is the fix, and the preflight
now asserts both flags so it cannot regress silently.

**Residue.** `separable` is FALSE in the calibration: planted-duplicate
distances overlap the sibling tail, so 0.2608 is the duplicate CEILING and not
a midpoint between separated classes. The consequence is bounded — stage 2 only
narrows which refuted priors face the stage-3 battery check, and a block still
requires verdict-vector equivalence — but the gate is wider than a separable
corpus would have allowed, and nothing here measures what that costs in
practice.

---

## 2026-09-01 · Segment 2 — the launch gate, and an instrument that could not reach two shipped modules

**What the record shows.** `python -u scripts/cycle_soak.py --case pa1` exits
0 (clean) on the launch configuration's own shape:

```
manifest 0f817fbca920f246...      qualification rc=0 in 13.5s
drive 1242.3s, 27 progress events, 24 of 24 cycles reached

[PASS] A1-typed-terminal          state='completed' stop_reason='budget_exhausted'
[PASS] A2-no-operational-failure  stop_reason='budget_exhausted'
[PASS] A3-verify-root-clean       0 violations
[PASS] A4-cycles-reached          24 of 24; deepest recorded death was cycle 2
[PART] D1-seat-contract           zero repair tasks -- the documented shape for
                                  an un-induced stub
[PASS] D2/D3/D4                   194 lease-checked attempts, dispatch
                                  authorizations, token reservations
```

It did not pass on the first attempt, and FINDINGS.md F1 records why: the
offline stub had no fixture for `ConfigRefereeWireV1` or
`GroundingRepairWireV1`, and its generic schema synthesiser cannot satisfy
either. No committed soak case had ever turned those two modules on, so P-A1 is
the first configuration to grant their contracts — which is what a
maximum-configuration run is for.

**The correction inside that repair is the reusable part.** The first repair
fixture used `correct_wording`. It VALIDATED against the advertised contract
and the soak still failed on exactly that pair. The caller narrows the contract
to one finding status's permitted actions while the advertised JSON Schema
still `$ref`s the full enum, so a fixture chosen from the schema alone can be
structurally valid and out of scope. `remove_span` is correct because it is the
only action present in every entry of `_ALLOWED_BY_STATUS` and it carries no
substantive field — checked across all five statuses, not assumed.

**Residue.** A green soak proves these contracts can be DISPATCHED and their
responses parsed against a deterministic stub. It proves nothing about whether
a real model produces useful referee verdicts or grounding repairs. Only the
live run speaks to that, and no soak can stand in for it.

---

## 2026-09-01 · Segment 3 — R4 falsified: `hv` is unreachable on any v6 run

**What the record shows.** This tranche was designed on the inference that
P-S1's 171 `transaction-contract-unavailable` deferrals were caused by its null
criticism policy, since that policy gates the defender/judge/variator
behavioural-contract grants. **The inference was half right and its conclusion
was wrong.**

The missing grant was a real defect and P-A1 closes it: `variator[0]` holds
`variator.direct.v1` where P-S1's held nothing. But
`Scheduler._defer_untransactional_v6_phase` (`scheduler.py:696-752`) returns
True for EVERY v6 manifest unconditionally. It never reads
`route_seat_behavioral_capability_plan`, a contract grant, a route, or any
Config field; its only other branch is `schema_version != 6`, which the
operations-parity law forecloses. Both producers of `hv_set` sit behind it.

The soak corroborates it empirically rather than by code reading alone: 24
cycles, the grant PRESENT, and **zero `hv_set` events**.

| root | variator deferrals | `hv_set` | `reach_set` |
|---|---|---|---|
| P-S1 | 171 | 0 | 0 |
| P-R1 `2026-08-25-poietics-program/run` | 117 | 0 | 0 |
| P-C2b | — | 0 | 0 |
| P-A1 soak (grant present) | ≥1 | 0 | 0 |

Eleven model phases die on that one line, not one, and their run-config knobs
(`HV_K`, `AUDIT_PERIOD`, `PROP_MAX`, `VISION_CRIT_PER_CYCLE`,
`ADVISORY_TRIALS_PER_CYCLE`) still parse, compile and appear live. The
operator's modularity law requires that "enforced" mean a check that can fail;
there is no such check here. That is what makes it a MODULARITY-LAW FINDING
(F2) rather than an ordinary defect.

`reach` is NOT affected, and correcting that half matters: `reach_sweep` is
deterministic, makes no provider call and sits behind no gate. The zero counts
on P-S1 and P-R1 are an empirical outcome, not a structural block.

PREREG Amendment 1 withdraws R4's conclusion without editing the frozen text,
and §8 gate 2 is withdrawn in writing with its reason — a gate no correct
configuration can pass is a broken gate, not a standard. Its replacement
obligation is MEASUREMENT, discharged in MODULE_COVERAGE.md.

**Residue.** Proven for `hv` and for the eleven named phases by code reading
plus four roots. NOT proven that any of those phases is otherwise sound — only
that none can run. The consequence for the defended-trial circuit is a
different path and is untouched by this finding; the live run is what settles
it.

---

## 2026-09-01 · Segment 4 — the live run

**What the record shows.** Run
`4565139800f5ca020e2b74acff45355c1277a9d510068a8e8b4ed65813f1a49c`, launched
08:59:30, terminated 15:12:45.

```
state              failed
stop_reason        operational_failure
message            V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY -- route seat has
                   terminally exhausted its smallest authorized contract
cycles completed   5 of 24
tokens             1 093 086 / 3 000 000
artifacts          25 accepted / 4 refuted / 0 suspended
verify_root        0 violations
qualification      23/23 pairs, 460 cases, 454 first-pass valid, 460 eventual,
                   6 repairs, 0 scope violations, no circuit openings
```

**The tranche's own question is answered, and answered positively.** P-S1 ran
this configuration's ancestor and filed 140 criticisms as `scrutiny`
observations without ever summoning a judge. This run filed **zero** scrutiny.
It ran the defended-trial circuit six times and summoned both cross-family
judges. Thirteen of twenty-four modules fired with typed evidence, and every
one of the eleven that did not carries a typed reason rather than a silence.
The explicit criticism policy is what did it — the same one line of manifest
data that also granted the defender, judge and variator seats their
behavioural contracts.

**And the live adjudication result is more interesting than success.** All six
trials DECLINED — two on ensemble split (the two judges disagreed), four on
execution-backed grounds. Zero verdicts. That is the frozen cross-family
unanimous configuration behaving as the amended judge law (2026-08-28)
describes it: under-convicting rather than prosecuting indiscriminately. Six
trials is far too small a sample to confirm anything and is recorded as an
observation, not a measurement.

**Why it stopped at cycle 5.** glm-5.3 conjecturer seat 1 exhausted its
smallest authorized contract: five `conjecturer.turn.v6` attempts, a compact
recovery, a decomposition to `conjecturer.atomic-candidate.v1`, two more
attempts, and nothing smaller to fall back to. The recovery ladder worked
exactly as designed and then ran out of rungs. **The other conjecturer seat was
healthy throughout** — deepseek seat 0 made 30 successful calls and never
failed once — but one seat's exhaustion terminates the whole run (F4).

**Three measured defects, all recorded as they came out:**

| # | measured |
|---|---|
| D1 frontier inversion | 14 members: **1 seed (7%), 13 harness-minted (93%)** — 8 research, 3 connection, 2 discrimination. NOT diluted: `hv` absent (F2), `reach` zero, so it sorted on coverage alone |
| D2 criticism → new problem | **0** of 5 `Crit` events. All 14 spawns harness-minted. Expected — minting is OFF by the operator's default — so this neither confirms nor refutes |
| D3 premise citation | **0 CITED, 7 DECLINED.** Same direction as P-S1's 1-vs-122, smaller sample |

**Five findings, none of them fixed here.** F1 the soak stub could not exercise
two shipped modules; F2 `hv` is unreachable on any v6 run under any
configuration; F3 qualification does not parallelize across endpoints; F4 one
seat's exhaustion kills the run AND the failed terminal is not continuable,
violating the 2026-08-29 continuation law; F5 glm-5.3 at the raised cap takes
~20 minutes per conjecture.

**Residue, and it is substantial.**

The run did not answer the operator's seed question, and nothing here claims it
did. Five cycles on a genuinely open problem in random-graph dynamics produced
25 accepted artifacts whose CONTENT this tranche has not assessed and whose
acceptance means only that they survived the criticism actually mounted at
them. Accepted does not mean true.

Six modules that were correctly configured never got the chance to fire:
simulation proposed nothing in five cycles, the scratchpad recorded nothing,
the config referee was one cycle short of its first firing at cadence 6, and
the bridge refused downstream of the failure. Whether any of them would have
fired in a run that reached cycle 24 is UNKNOWN, and a run that dies at cycle 5
cannot settle it. Capability-channel use is stochastic across identical runs
(CLAUDE.md), so one live miss is inconclusive for that path.

The cap-scaling hypothesis in F5 rests on one glm-5.3 sample against three
deepseek samples, with two confounds — the cap raise and the glm-5.2/5.3
version change — and no controlled comparison. It is a lead, not a result.

And the run is not continuable, so none of the above can be settled by
resuming this root. A future attempt starts over.
