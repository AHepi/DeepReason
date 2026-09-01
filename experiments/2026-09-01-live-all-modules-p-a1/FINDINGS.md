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

**Why this window did not apply it.** `scripts/wheel_operational_smoke.py` is
outside this tranche, and the tranche instruction lists "any needed code edit"
as a STOP AND ASK condition to be bubbled to the operator and not resolved
here. Raised 2026-09-01; awaiting the operator's decision.

**Residue.** Even with the two fixtures added, a green soak would prove that
the two contracts can be DISPATCHED and their responses parsed. It would not
prove that a real model produces useful referee verdicts or grounding repairs
— that is what the live run is for, and no soak can stand in for it.
