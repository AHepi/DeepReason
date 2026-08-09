# Parked defects — corpus-enrichment + consistency-patrol pilot

Nothing here is fixed in-tree this tranche. `src/`, `tests/`, `tools/`
stay byte-untouched by tranche scope; each entry below is a ready-to-send
prompt for a future tranche.

**P-CEPP-1** — `conjecturer.turn.v7` (the D2 dual-mode/candidate-checker
contract) cannot be used by any live run today. `ContractVersionPolicyV3`
(`src/deepreason/run_manifest.py:658-660`) accepts the Literal value, but
`_compile_contract_schema_repair_policy` (`run_manifest.py:2473-2545`)
hardcodes schema-repair grants for `"conjecturer.turn.v6"` only
(line 2491) — no config field or CLI flag adds a v7 grant. A manifest
built with `conjecturer_turn_contract="conjecturer.turn.v7"` therefore
always fails `_compile_route_seat_behavioral_capability_plan`
(`run_manifest.py:1994-2002`) with a typed
`RunManifestError("V6_BEHAVIORAL_REPAIR_GRANT_REQUIRED", ...,
"/contract_schema_repair_policy/grants")` before the run can even start
— confirmed by direct construction, not inferred. D2's own CHECKLIST.md
(lines 693-702) already named wiring v7 to a real repair-authority grant
as out-of-scope "future-tranche work"; this entry is that future
tranche's ready-to-send prompt. Ready-to-send prompt: "Wire
`conjecturer.turn.v7` to a real `ContractSchemaRepairGrantV1` in
`_compile_contract_schema_repair_policy` (`run_manifest.py:2473`) so a
live run configured for v7 can actually validate and dispatch a
`program:candidate_checker` eval-kind commitment through the `encoder`
seat; D2's own tests (`tests/test_oracle.py`'s dual-mode section) prove
the eval-kind mechanics work once a manifest can be compiled at all."

**P-CEPP-2** — the Phase 2 patrol pilot's topical-neighborhood rule uses
problem-address locality (`state.addr`) only; refs-based locality
(shared `Interface.refs` edges, `RefRole.MENTION`/`EVIDENCE`/
`DEPENDENCE`) was considered in the prereg and deliberately not
implemented for this pilot — it needs a graph-distance computation
beyond a single dict lookup, and the task's own falsifiable question
(candidate-contradiction rate, historical vs enriched) does not need it
to produce a first decision number. Ready-to-send prompt: "Extend
`experiments/2026-08-08-corpus-enrichment-patrol-pilot`'s patrol sampler
with a refs-based neighborhood rule (claims connected within N hops via
`Interface.refs`/`state.dep` in addition to shared `state.addr`), and
report whether it finds contradiction candidates the problem-address
rule misses."
