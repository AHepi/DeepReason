# Parked — P-CEPP-1 dual-mode wiring tranche

Nothing here is fixed in-tree this tranche. Each entry is a ready-to-send
prompt for a future tranche.

**P-CEPP-1-BATTERY-1 — should `cli/doctor.py` (frozen surface 5, the
qualification pair inventory) be widened so `conjecturer.turn.v7`
becomes reachable through the NORMAL `deepreason doctor`/qualification
battery, not just a hand-built bypass?**

Confirmed, not assumed (`REQUEST.md` Amendment 1): surface 5 is
byte-untouched by this tranche —
`ProductionContractPairV1.contract_id`'s `Literal`
(`src/deepreason/cli/doctor.py:62`) still does not admit
`"conjecturer.turn.v7"`. This tranche's own live run
(`experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/
live_run_v7/`) proved v7 dispatches correctly end-to-end against a
real provider, but only by BYPASSING the qualification battery
(`scripts/live_run_v7.py::_bind_classification_bypassing_doctor`,
mirroring the same technique the S2/S4 regression tests use) — a
v7-configured manifest still cannot pass through `deepreason doctor`
or the ordinary `deepreason setup`/`deepreason run` CLI lifecycle,
because `production_contract_pairs(manifest)` raises a
`pydantic.ValidationError` the first time it tries to project a
`conjecturer.turn.v7` grant into a `ProductionContractPairV1`
(`src/deepreason/cli/doctor.py:332`).

This was explicitly out of scope for Option C (the operator's own
choice among three priced options, `SPEC.md`) and remains untouched by
design, not oversight — widening it would trigger a qualification
cache miss (~14 min, ~1160 calls, `CLAUDE.md`'s own documented cost of
any manifest/pair-inventory change) and touches a THIRD frozen surface
this tranche never got explicit words for.

**Ready-to-send prompt**: "Widen `ProductionContractPairV1.contract_id`
(`src/deepreason/cli/doctor.py:62`, frozen surface 5) to admit
`\"conjecturer.turn.v7\"` alongside `\"conjecturer.turn.v6\"`, so a
v7-configured manifest can pass through the normal
`deepreason doctor`/qualification battery and the ordinary
`deepreason setup`/`deepreason run` CLI lifecycle without the
hand-built classification bypass
`experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/
scripts/live_run_v7.py` uses. Requires explicit operator words for
touching frozen surface 5 specifically (this tranche's own Amendment 1
established that a prior option-selection's preview text is not a
substitute for that). Budget for the qualification cache miss (~14
min, ~1160 calls) this will cost. The four files this earlier tranche
(`experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/`)
already wired (`run_manifest.py`, `rules/conj.py`,
`workflow/profiles.py`, `invariants.py`) do not need to be touched
again — they already treat v6 and v7 identically; only surface 5's own
pair-inventory Literal is the remaining gap."
