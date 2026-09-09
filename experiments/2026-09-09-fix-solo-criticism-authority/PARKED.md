# Parked — found during this tranche, not fixed here

## P1 — a single-family, MULTI-model run can obtain no judge ensemble at all

**What.** `require_cross_family_judge_ensemble` accepts two judge seats of
different FAMILIES, or two seats of the exact same (provider, model_id). A run
whose judge seats carry two DIFFERENT models of ONE family satisfies neither
and raises `JudgeEnsemblePolicyError`, so its argumentative trial dies rather
than declines. `require_cross_school_judge_ensemble` and
`LLMAdapter.school_judge_bindings` were built for exactly this shape and cannot
be reached: `build_adapter` never populates the bindings, and both manifest
validators plus `resolve_school_route` refuse a `role="judge"` school binding.
This is the road the d8 tranche's SPEC.md M6 actually describes, and it is NOT
the road `ARGUMENTATIVE_AUTHORITY=single_family_trial` needed — that one asks
for a critic school, proved in this tranche's `REPRO.md`.

**Ready-to-send prompt.**

```
Route through dr-change-orchestrator (dr-capture-request first). One goal: a
single-FAMILY, MULTI-model run can obtain a judge ensemble, or the code built
for that case is retired.

Evidence, all read-only:
- experiments/2026-09-09-fix-solo-criticism-authority/REPRO.md, "What this
  reproduction does NOT show" -- why this is a different road from the one that
  tranche closed, measured rather than argued.
- src/deepreason/llm/firewall.py:354-393 -- require_cross_family_judge_ensemble
  raises when families<2 AND models!=1, which is exactly this shape.
- src/deepreason/informal/trial.py:989 -- the else-branch that reaches it.
- src/deepreason/llm/adapter.py:692-706 -- _select_judge_ensemble, the only
  consumer of school_judge_bindings.
- docs/map/SEAM-manifest-x-schools.md, "There is no manifest surface for a
  judge school" -- and its check, which PINS the isolation.

Frozen-surface reading FIRST and in full: this is
experiments/2026-09-09-fix-solo-criticism-authority/FIX.md's road (a), already
priced there with tools/blast_radius.py's computed rows pasted -- CONTACT, 2 of
5 surfaces, DIRECT on run_manifest.py, plus frozen-adjacent route_fingerprint,
a moved qualification subject digest (one battery, ~14 min, ~1160 calls per
home) and 180-260 lines across 6-8 files. It exceeds a tranche's 150-line
budget: scope it as a programme with its own rungs, or price the retirement
road instead. Start from that FIX.md rather than re-deriving the pricing.

Two roads: (a) wire it end to end -- validators admit a judge school binding,
resolve_school_role_lease routes it, build_adapter populates the bindings, and
the three re-checks the seam names as inseparable move together
(plan_foreign_criticism, _criticism_contract, verify_root); (b) retire
require_cross_school_judge_ensemble and LLMAdapter.school_judge_bindings and
record in ERRATA that a single-family multi-model run must either add a second
family or run two judge seats on one model. Road (b) removes a capability the
solo law's spirit covers; do not take it without the operator's words.
```

## P2 — `Config.ARGUMENTATIVE_AUTHORITY`'s three values have no single place that says which reach a run

**What.** The Literal offers `observe_only`, `trial_required` and
`single_family_trial`. `trial_required` reaches a trial only through the
legacy, school-free criticism circuit; `single_family_trial` reaches none;
`defended_trial` — the value that DOES work on a solo run — is not on this knob
at all but on `ENGAGED_CRITICISM_AUTHORITY`, and needs
`LEGACY_CRITICISM_ENABLED=False` besides. Four knobs decide one behaviour and
no document holds the table. `docs/map/CON-authority.md` describes the two
vocabularies correctly and still does not answer "which configuration actually
tries a case".

**Ready-to-send prompt.**

```
Route through dr-change-orchestrator. One goal: one table says which
configuration of ARGUMENTATIVE_AUTHORITY, ENGAGED_CRITICISM_AUTHORITY,
LEGACY_CRITICISM_ENABLED and ADJUDICATION_STATUS_AUTHORITY_ENABLED actually
reaches an argumentative trial, with a check that goes red when it stops being
true.

Evidence: experiments/2026-09-09-fix-solo-criticism-authority/REPRO.md measures
two of the rows already (the Config road declines; the school-routed
defended_trial road mints a warrant on the same one-model shape), and its
proof/ carries both runnable stubs. docs/map/CON-authority.md is the owning
document; its "two vocabularies" section is correct and incomplete.

Smallest change: a table in CON-authority.md, one row per reachable
combination, each row carrying a check that compiles the configuration and
asserts whether a trial is reachable. Do NOT add a knob. Wait for the
criticism-authority tranche above to settle first -- its chosen road changes at
least one row.
```

## Not parked here, because another tranche already owns them

- `tools/blast_radius.py` reporting comment and string-literal occurrences as
  frozen-surface contacts —
  `experiments/2026-09-09-change-d8-criticism-experiment/PARKED.md` P4. Hit
  again in this tranche: road (c)'s three SYMBOL_INDIRECT rows all had to be
  checked by hand, and all three turned out to be real references. Recorded as
  a fifth measured instance, not re-parked.
- CLAUDE.md's provider-model sentence — same file, P2.
