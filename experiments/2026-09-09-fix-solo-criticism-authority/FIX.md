# Fix: make `single_family_trial` name the road that already runs, or stop naming a road at all

**STATUS: STOPPED FOR THE OPERATOR.** Nothing is implemented. This tranche
found something the brief did not know, and it changes what each road costs.

## What the reproduction changed about the question

The brief asked whether the operator's 2026-08-09 solo law has a road. It has
one, and it runs. On a one-model configuration — the same model id in every
seat, two judge seats, a defender seat, two schools — with
`LEGACY_CRITICISM_ENABLED=False`, `ADJUDICATION_STATUS_AUTHORITY_ENABLED=True`
and `ENGAGED_CRITICISM_AUTHORITY=defended_trial`, a v6 manifest compiles clean
and the run mints an ARGUMENTATIVE warrant that becomes an attack edge and a
REFUTED status (`proof/REPRO_B_defended_trial.txt`; the root replays with zero
violations). No cross-family anything is required: the criticism validator's
same-model substitute — two judge seats carrying one model — already admits a
solo run, so `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED` never fires.

So the defect is narrower and more ordinary than "solo runs are locked out of
status-changing criticism". It is that `Config.ARGUMENTATIVE_AUTHORITY` offers
three values and one of them, `single_family_trial`, is reachable only from the
caller that structurally cannot satisfy the trial it asks for. An operator
reading that Literal cannot tell which value works.

**And one correction to the brief, stated plainly because it changes the
choice.** The brief's road (a) — populate `school_judge_bindings` from the
manifest, admit a `role="judge"` school binding at the validator, route it at
the resolver — would NOT make `single_family_trial` reach a run. Measured:
`informal/trial.py::_argument_trial_steps`'s single-model branch never calls
`_select_judge_ensemble` and never consults a judge binding; it asks for a
CRITIC SCHOOL. The judge-binding gates guard a different road (a single-FAMILY,
MULTI-model run, where the else-branch runs `require_cross_family_judges()` and
the cross-school ensemble is the only one obtainable). That road is real and
worth building one day, but wiring it would leave this tranche's goal exactly
where it started. I have priced it below as road (a) so the operator can see
what the brief's own recommendation buys, and added road (c), which the
evidence made available and which meets the goal at a fraction of the cost.

Guarantee restored (roads b and c alike): every value
`Config.ARGUMENTATIVE_AUTHORITY` accepts either reaches a trial on some
launchable configuration, or is not a value it accepts.

## The three roads, priced

### Road (a) — wire the cross-school JUDGE ensemble end to end

What it buys: a single-FAMILY, multi-MODEL run gains a judge ensemble it cannot
obtain today. It does NOT satisfy this tranche's goal.

Change sites: `run_manifest.py` (`_validate_v4_criticism_policy` and
`_validate_v4_control_plane_policy` admit `role="judge"`; the
`SchoolRoleBindingV1`/`CriticismPolicyV1` shape may need a judge-seat field),
`llm/firewall.py::resolve_school_role_lease` (admit the role),
`llm/adapter.py::build_adapter` (populate `school_judge_bindings` from the
manifest), plus the three re-checks the seam names as inseparable —
`plan_foreign_criticism`'s eligible set, `_criticism_contract`'s restart
authorization, and `verify_root`'s `school-route` derivation.

Frozen-surface verdict: **CONTACT** — 2 of the five surfaces plus
frozen-adjacent ground. `tools/blast_radius.py` rows, verbatim and computed
(full JSON at `proof/BLAST_RADIUS_road_a.txt`):

| kind | surface | tier | target | detail |
|---|---|---|---|---|
| frozen surface contacts | manifest schemas and validators (run_manifest.py) | DIRECT | src/deepreason/run_manifest.py | target file is surface path src/deepreason/run_manifest.py |
| frozen surface contacts | replay-validation record formats (invariants.py) | SYMBOL_INDIRECT | route_fingerprint | 'route_fingerprint' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact) |
| frozen surface contacts | manifest schemas and validators (run_manifest.py) | SYMBOL_INDIRECT | _validate_v4_criticism_policy | '_validate_v4_criticism_policy' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact) |
| frozen surface contacts | manifest schemas and validators (run_manifest.py) | SYMBOL_INDIRECT | resolve_school_route | 'resolve_school_route' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact) |
| frozen surface contacts | manifest schemas and validators (run_manifest.py) | SYMBOL_INDIRECT | route_fingerprint | 'route_fingerprint' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact) |
| frozen adjacent contacts | route_fingerprint serialization (llm/firewall.py) | DIRECT | src/deepreason/llm/firewall.py | target file is surface path src/deepreason/llm/firewall.py |
| frozen adjacent contacts | route_fingerprint serialization (llm/firewall.py) | SYMBOL_INDIRECT | require_cross_school_judge_ensemble | 'require_cross_school_judge_ensemble' referenced in src/deepreason/llm/firewall.py (grep-based; not proof of semantic contact) |
| frozen adjacent contacts | route_fingerprint serialization (llm/firewall.py) | SYMBOL_INDIRECT | route_fingerprint | 'route_fingerprint' referenced in src/deepreason/llm/firewall.py (grep-based; not proof of semantic contact) |

Tool's own summary, verbatim: "This change touches 2 of the five frozen
surfaces (locked-down files that a change can silently corrupt old,
already-recorded runs by touching): manifest schemas and validators
(run_manifest.py); replay-validation record formats (invariants.py). It also
touches frozen-adjacent ground: route_fingerprint serialization
(llm/firewall.py). 1 declared symbol(s) already have no live call path today,
independent of this change: _validate_v4_criticism_policy. 11 test file(s) and
14 map document(s) assert on the touched targets today."

Price: widening a criticism-binding role changes which topologies are
admissible, which changes `production_contract_pairs`, which moves the
qualification subject digest — the seam prices a moved digest at one full
battery, about 14 minutes and about 1160 provider calls per affected home. The
two `CON-schools.md` checks that pin the isolation (line 151 and the
`require_cross_school_judge_ensemble` Trap) must be rewritten to pin the new
behaviour. Estimated diff: 180-260 lines across 6-8 files — **over the 150-line
tranche budget**, so this road is a programme, not a tranche.

### Road (b) — retire the declaration

Change sites (exhaustive):
- `src/deepreason/config.py:538-540` — drop `"single_family_trial"` from the
  Literal; rewrite the comment block at 515-529 to name the road that works.
- `src/deepreason/authority.py:43,49` — drop it from `_ARGUMENTATIVE_VALUES`
  and `_TRIAL_AUTHORITIES`.
- `src/deepreason/rules/crit.py:79` — drop it from `_TRIAL_MODES`; rewrite the
  comment at 66-72.
- `src/deepreason/workflow/nonconjecture_recovery.py:691,698` — drop it from
  the recoverable-authority tuple and its comment.
- `docs/ERRATA.md` — a new entry recording that the 2026-08-09 law's solo road
  is `ENGAGED_CRITICISM_AUTHORITY=defended_trial` with
  `LEGACY_CRITICISM_ENABLED=False` on a one-model configuration with two judge
  seats, proven by the committed stub test, and that the value removed here
  never reached a run.
- Map: `CON-authority.md` (2 identical set-checks at :49 and :122, the
  refusal-message check at :154, and prose at :120 and :303),
  `SUB-rules.md:253` Traps entry and its check, `CON-schools.md:244` Traps
  entry, `SUB-workflow.md:351` prose.

Frozen-surface verdict: **CONTACT, frozen-ADJACENT only** — no frozen surface
is touched. Rows, computed (`proof/BLAST_RADIUS_road_b.txt`):

| kind | surface | tier | target | detail |
|---|---|---|---|---|
| frozen adjacent contacts | route_fingerprint serialization (llm/firewall.py) | DIRECT | src/deepreason/llm/firewall.py | target file is surface path src/deepreason/llm/firewall.py |
| frozen adjacent contacts | route_fingerprint serialization (llm/firewall.py) | SYMBOL_INDIRECT | require_cross_school_judge_ensemble | 'require_cross_school_judge_ensemble' referenced in src/deepreason/llm/firewall.py (grep-based; not proof of semantic contact) |

Tool's own summary, verbatim: "This change touches none of the five frozen
surfaces. It also touches frozen-adjacent ground: route_fingerprint
serialization (llm/firewall.py). 6 test file(s) and 11 map document(s) assert
on the touched targets today."

That frozen-adjacent row appears only because the road as the brief wrote it
also deletes `LLMAdapter.school_judge_bindings` and
`require_cross_school_judge_ensemble`. **I recommend against deleting those
even under road (b):** the reproduction shows they are not what
`single_family_trial` needed, and they are the only ensemble a single-family
multi-model run could ever obtain. Deleting them removes a capability from a
run shape the law also covers. Keep them and road (b) touches neither a frozen
nor a frozen-adjacent surface.

Price: measured, `Config.ARGUMENTATIVE_AUTHORITY` is already carried in the v6
engine-config echo, and the digest is over the VALUE, not the schema — so
removing an unused value from the Literal moves no committed digest and costs
no battery. Estimated diff: about 45 lines across 4 source files plus ERRATA
and 4 map documents; roughly 8 tests rewritten. **Cost: it deletes the value
the law's own words asked for, so a future reader of the law finds nothing in
`Config` answering to it, and the road is discoverable only by reading ERRATA.**

### Road (c) — make the declared value name the road that runs (RECOMMENDED)

`single_family_trial` stops being a Config-only trial mode and becomes what it
always meant: "compile the criticism policy for a solo run". When
`ADJUDICATION_STATUS_AUTHORITY_ENABLED` is on and
`ARGUMENTATIVE_AUTHORITY=single_family_trial`,
`v6_policy::configured_criticism_policy` compiles `authority="defended_trial"`,
which is the value the manifest, the resolver, the scheduler and the trial
already agree on. Nothing new is admitted anywhere; one Config word is
translated into the manifest's own word at the one site that already performs
that kind of translation.

Change sites (exhaustive):
- `src/deepreason/v6_policy.py:302-317` (`configured_criticism_policy`) — the
  translation, with the deterministic resolution rule when
  `ENGAGED_CRITICISM_AUTHORITY` also speaks (the stronger of the two wins, and
  the choice is recorded).
- `src/deepreason/config.py:515-529` — rewrite the comment block to say what
  the value now does and what it still requires
  (`LEGACY_CRITICISM_ENABLED=False`).
- `src/deepreason/scheduler/scheduler.py` (one call site in
  `_foreign_arg_crit`) — the typed disclosure on the run's own record, a
  `criticism.authority-translated.v1` measure recorded once at first foreign
  criticism dispatch, derived by comparing the manifest's echoed
  `ARGUMENTATIVE_AUTHORITY` with the compiled policy authority. This satisfies
  the 2026-08-28 law's "switching a gate produces a typed WARNING, never
  silence" and the goal's "the typed disclosure for the switched gate is on the
  record".
- A second typed disclosure for the case the operator will actually hit: when
  `ARGUMENTATIVE_AUTHORITY=single_family_trial` but
  `LEGACY_CRITICISM_ENABLED` is still `True` (the default), the value cannot
  reach a trial — say so on the record rather than compile silently. No silent
  override of a named setting: that is the P10 shape the 2026-08-28 law
  condemns.
- Map: `CON-schools.md:244` Traps entry rewritten (it currently says the mode
  "cannot complete a trial"), plus a Traps entry naming this run id; a new
  `check:` in `CON-authority.md` that goes red if the road stops reaching a
  run.

Frozen-surface verdict: **CONTACT, three SYMBOL_INDIRECT rows only** — no
target file is a frozen surface. Rows, computed
(`proof/BLAST_RADIUS_road_c.txt`):

| kind | surface | tier | target | detail |
|---|---|---|---|---|
| frozen surface contacts | manifest schemas and validators (run_manifest.py) | SYMBOL_INDIRECT | configured_criticism_policy | 'configured_criticism_policy' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact) |
| frozen surface contacts | manifest schemas and validators (run_manifest.py) | SYMBOL_INDIRECT | ENGAGED_CRITICISM_AUTHORITY | 'ENGAGED_CRITICISM_AUTHORITY' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact) |
| frozen surface contacts | manifest schemas and validators (run_manifest.py) | SYMBOL_INDIRECT | LEGACY_CRITICISM_ENABLED | 'LEGACY_CRITICISM_ENABLED' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact) |

Tool's own summary, verbatim: "This change touches 1 of the five frozen
surfaces (locked-down files that a change can silently corrupt old,
already-recorded runs by touching): manifest schemas and validators
(run_manifest.py). 6 test file(s) and 8 map document(s) assert on the touched
targets today."

I checked every one of those three rows by hand rather than trusting the grep,
because this gate is known to match comment prose (the d8 tranche's parked P4).
All three are REAL references and none is an edit target:
`run_manifest.py:3964-3967` CALLS `configured_criticism_policy`;
`run_manifest.py:2412,2428,2563-2564,2621-2623` name the other two as
engine-config carriage rows. **`run_manifest.py` is not edited under road (c)**,
so the DIRECT contact road (a) carries does not arise. Whether that still
requires a frozen-surface grant is the operator's call, and is question Q2
below.

Price: no manifest schema, validator, Pydantic model or record format moves.
The qualification subject digest moves only for a configuration that sets
`single_family_trial` — a value no committed run ever used, because no
committed run could — so no existing home requalifies. Estimated diff: about
70 lines across 3 source files plus 2 map documents and one new test file.

## Regression artifact

`proof/stub_solo_config_path.py` must invert: under roads (a) and (c) it
reports `argumentative: >= 1` and no `trial-declined:no-critic-school`; under
road (b) the script no longer constructs, because `Config` rejects the value.
`proof/stub_solo_defended_trial.py` must be unchanged under every road — it is
the control, and a road that moves it has changed the road that already works.

New conditions the chosen road must also be tested against, mutation-proven in
both directions:
1. A one-model configuration with the switches on mints an ARGUMENTATIVE
   warrant that becomes an attack edge (`docs/map/CON-warrants-and-attacks.md`:
   no warrant, no edge).
2. The typed disclosure for the switched gate is on the record.
3. `route_fingerprint` does not move — asserted directly over a fixture route,
   as the grant text requires.
4. The qualification subject digest over the committed fixture does not move —
   asserted the way the seat-retirement grant asserted it.
5. Under road (c), the `LEGACY_CRITICISM_ENABLED=True` case records its typed
   "cannot reach a trial" disclosure rather than compiling silently.

## Existing tests at risk

| test | road (a) | road (b) | road (c) |
|---|---|---|---|
| `test_prose_refutation_boundaries.py::test_the_config_only_path_cannot_satisfy_the_cross_school_guarantee` (:1165) | keeps passing | DELETED — the value is gone | REWRITTEN — it asserts the old decline; under (c) the direct-helper path is still school-free, so it keeps passing with a comment change only if the translation is confined to the compiled policy |
| `::test_the_single_family_authority_value_exists` (:135) | keeps passing | DELETED | keeps passing |
| `::test_the_new_mode_is_config_only_and_refused_by_the_manifest_path` (:148) | keeps passing | DELETED | keeps passing — the value still may not be frozen INTO the manifest; it is translated before the manifest sees it |
| `::test_the_new_mode_routes_to_the_same_defended_trial` (:182) | keeps passing | DELETED | keeps passing |
| `::test_single_family_trial_reachable_under_master_gate` (:1063) | keeps passing | DELETED — and its docstring is the one that cites the solo law, so ERRATA must carry what it asserted | keeps passing |
| `::test_the_cross_school_ensemble_*` (:347-:419), `::test_configuring_school_bindings_does_not_reach_the_gate_with_two_families` (:892), `::test_nothing_the_operator_configures_can_turn_the_substitute_on` (:1261) | REWRITTEN — they pin the isolation this road removes | keeps passing if the pair is kept (recommended); DELETED if it is not | keeps passing |
| `test_config.py:35`, `test_criticism_authority.py:113,227`, `test_manifest_integration.py:122-271` | keeps passing | fixture updates where they name the value | keeps passing |
| `test_v6_policy_preset.py::test_engaged_criticism_authority_config_default_preserves_prior_behavior` | keeps passing | keeps passing | MUST keep passing — it pins that `ENGAGED_CRITICISM_AUTHORITY` reaches the manifest with no vocabulary translation, so road (c)'s translation must live on `ARGUMENTATIVE_AUTHORITY` and leave that knob's path byte-identical |

## Explicitly not changed, under every road

`informal/trial.py`'s trial mechanics; `capabilities/state.py`; `harness.py`;
`invariants.py`; `verification/`; `qualification.py`;
`CriticismPolicyV1.authority`'s Literal (widening it is the thing
`SUB-rules.md:253` and `CON-authority.md`'s "may never be widened" rule forbid,
and roads (b) and (c) both avoid it). The single-family MULTI-model judge gap
is PARKED, not fixed here.

## STOP — what I need from the operator

Q1. **Which road?** My recommendation is **(c)**, on three grounds: it is the
only road that satisfies the goal as written; it costs no battery and touches
no frozen surface as an edit target; and it keeps the operator's own word
`single_family_trial` meaning something, which road (b) gives up. The brief's
own recommendation was road (a); the reproduction shows road (a) does not reach
this goal, and I would rather say that than build it.

Q2. **Do you grant frozen-surface contact?** Under road (c) I do not intend to
edit `run_manifest.py` at all — the three contact rows are references from that
file into mine, not edits to it. If you want the belt-and-braces version (a
compile NOTICE emitted by `compile_run_manifest` instead of a measure on the
run's record), that IS an edit to frozen surface 4 and needs an explicit grant.
Say which you want. Under road (a) the grant is unavoidable and the tranche
also exceeds its line budget, so road (a) needs a programme, not this tranche.

Q3. **Keep or delete `school_judge_bindings` and
`require_cross_school_judge_ensemble`?** The brief's road (b) deletes them. I
recommend KEEPING them under any road: the reproduction shows they were never
what `single_family_trial` needed, and they are the only judge ensemble a
single-family multi-model run could obtain. Deleting them is the only part of
this tranche that would remove a capability.

Estimated diff, road (c): about 70 lines across 3 source files, 2 map
documents, 1 new test file. Within budget. One commit.
