# Fix: give a criticism a place to declare what it rests on, and register that declaration on its validity node as EVIDENCE

Guarantee restored: **when a criticism declares an artifact essential and that
artifact is later refuted, the criticism's attack lifts onto its validity node
in the same fixpoint pass and its target reinstates** — the road
`CON-warrants-and-attacks.md` already documents ("a verdict may declare what it
rests on, and that declaration is the evidence closure's only entry point"),
now reachable from the wire instead of only from a hand-built graph.

## Frozen-surface verdict (run before any code was written)

```
$ python tools/blast_radius.py \
    --files src/deepreason/llm/contracts.py src/deepreason/llm/wire.py \
            src/deepreason/rules/crit.py src/deepreason/informal/trial.py \
    --symbols ArgumentativeCriticOutput CompactCritic CriticWireContract \
              crit_argumentative crit_argumentative_batch \
              run_argument_trial_from_case _argument_trial_steps

"frozen_surface_contacts": []
"frozen_adjacent_contacts": []
"frozen_surface_verdict": "CLEAR"
"disclosure_summary": "This change touches none of the five frozen surfaces.
 9 test file(s) and 11 map document(s) assert on the touched targets today. ..."
"qualification_digest": []
"wheel_smoke_pins": []
```

NO CONTACT, as GOAL.md forecast. No grant is needed and none is requested.
`src/deepreason/llm/roles.py` (two template sentences) was not in the
`--files` list above; it is a prompt string with no symbol any frozen surface
reads, and `test_role_prompt_registry.py` is its only consumer.

## Change sites (exhaustive)

- `src/deepreason/llm/contracts.py:112-145` — `ArgumentativeCriticOutput` gains
  `premises_essential: list[str]`, default empty. Resolved artifact ids: the
  artifacts this case ESSENTIALLY relies on, such that withdrawing one should
  make the case fall. Distinct from `premise` beside it, which is a
  presupposition of the PROBLEM and says so in its own comment.
- `src/deepreason/llm/contracts.py:148-161` — `BatchCase` gains the same field
  with the same semantics, exactly as `successor_question` and
  `premise_evidence` are carried on both criticism outputs
  (`CON-criticism-source.md`'s own check asserts that symmetry for
  `successor_question`; the new field joins it).
- `src/deepreason/llm/wire.py:2692-2704` — `CompactCritic` gains
  `essential_premise_aliases: list[str]`, default empty, shaped exactly like
  `cited_input_aliases` beside it (a plain array, so the schema binder can
  write its `items` enum; an optional `| None` field would nest the array
  under an `anyOf` where the binder does not reach).
- `src/deepreason/llm/wire.py:2709` — `CriticWireContract.ALIAS_ARRAY_FIELDS`
  gains `"essential_premise_aliases"`. **This is the whole of the
  hallucinated-id requirement on the compact road**: `_bind_alias_fields`
  writes the call-local alias set into the schema as an enum, so a premise
  naming something absent from the pack is an ordinary schema violation — a
  repair ladder and then a failed call that creates nothing, never a silent
  drop. `tests/test_schema_carries_every_prose_rule.py::
  test_alias_bearing_fields_name_their_legal_values_in_the_schema` already
  proves that mechanism for `cited_input_aliases`; the new field is added to
  its case list.
- `src/deepreason/llm/wire.py:2733-2755` — `CriticWireContract.compile`
  resolves the aliases to ids and carries them onto `premises_essential`.
  Unlike `cited_input_aliases` (which is flattened into the case TEXT and lost
  as structure — PARKED P1), the resolution survives as a list.
- `src/deepreason/llm/wire.py:2559-2568` — `BatchCriticCaseWireV2` gains the
  same wire field, and `BatchCriticWireContractV2` gains
  `ALIAS_ARRAY_FIELDS = ("essential_premise_aliases",)`; its `compile` carries
  the resolved ids onto each `BatchCase`.
- `src/deepreason/rules/crit.py:1633-1645` — `crit_argumentative` passes
  `output.premises_essential` into `run_argument_trial_from_case`.
- `src/deepreason/rules/crit.py:2256-2270` — `crit_argumentative_batch` passes
  `case.premises_essential` the same way.
- `src/deepreason/informal/trial.py:904-949` —
  `run_argument_trial_from_case` gains a keyword-only
  `premises_essential: Sequence[str] = ()` and forwards it.
- `src/deepreason/informal/trial.py:952-1076` — `_argument_trial_steps` gains
  the same keyword. Two effects, in this order:
  1. **Typed decline for an unknown id.** Any declared premise that is not a
     registered artifact returns `_decline(harness, target_id,
     "unknown-premise", diagnostics)` — the trial's existing typed
     non-outcome, which records a `["trial-declined", target, reason]` Measure
     and mints nothing. This is defence in depth behind the schema enum, and
     it is what covers the DIRECT-contract path (a profile with
     `direct_contracts` bypasses the alias table entirely, so the enum cannot
     protect it). Placed with the other preflight declines, above any provider
     spend.
  2. **The registration.** ν is built with
     `Interface(refs=[Ref(target=p, role=RefRole.EVIDENCE) for p in premises])`
     instead of no interface — the same construction `rules/vision.py:104`
     already uses for its screenshots, and the same role
     `register_fail_warrant`'s `manifest_ref` mounts for demonstrative
     verdicts. An empty declaration builds ν exactly as today (no interface
     argument at all), so the no-declaration path is byte-unchanged.
- `src/deepreason/llm/roles.py:36-51` — one sentence added to the
  `argumentative_critic` and `batch_critic` templates: name the artifacts your
  case essentially relies on, and it is complete to name none. Without this the
  field exists and is never filled.
- `docs/map/CON-warrants-and-attacks.md` — a new rule paragraph with a
  `check:` that would fail if the registration regressed, a `Where to change
  what` row, and a `Traps` entry naming this tranche. Same commit as the code,
  per `SCHEMA.md`.

## What is deliberately NOT registered

**Declared premises never reach a DEMONSTRATIVE verdict's ν.**
`rules/crit.py`'s five `register_fail_warrant` sites mint verdicts whose ground
is an EXECUTION — a counterexample that RAN, a program that FAILED. Mounting a
prose premise on those validity nodes would let a prose attack on a listed
premise disable a demonstrated refutation, inverting the execution-supremacy
line `CON-warrants-and-attacks.md` states in four separate rules. The
declaration therefore binds only where the criticism's ground IS its case: the
defended-trial mint site. This is a design decision, not an omission, and it is
recorded here so a later reader does not "complete" it.

Also not registered: `informal/trial.py:1405` (pairwise — rules on a rivalry,
not on a critic's case against one target), `rules/experiment.py:391` and
`rules/relatedness.py:153` (harness-composed rulings, no critic contract in
the loop), `rules/vision.py:104` (already declares its ground on ν; its
contract is not `ArgumentativeCriticOutput`).

## Regression artifact

Must invert / must newly hold:

1. `experiments/.../repro_nu_evidence.py` — must keep printing all three arms
   unchanged, exit 0. Arm A staying `('refuted', 'suspended_unsupported')` is
   REQUIRED: a criticism that declares nothing keeps today's behaviour.
2. NEW `experiments/.../s0_wire.py` — the §0 DEPENDENCE scenario driven
   through the wire, with the critic declaring the premise essential. Must
   print the EVIDENCE tuple `('accepted', 'refuted')`.
3. NEW `tests/test_criticism_premises.py`, on a stub root, reusing
   `tests/test_prose_refutation_boundaries.py`'s `_single_family_trial_adapter`
   scaffolding rather than inventing any:
   - a critic declares a premise; the trial mints; ν carries exactly one
     `RefRole.EVIDENCE` ref naming it;
   - the premise is then refuted, and the target returns to `ACCEPTED` in the
     same pass while the criticism goes `REFUTED`;
   - a critic that declares NOTHING produces a ν with no refs and a target
     that stays `REFUTED` after an unrelated refutation (the formalism-optional
     law, as a test rather than a promise);
   - an empty declaration is not a failed call and costs the criticism nothing;
   - a declared id absent from the graph declines typed, mints nothing, and
     leaves the target's status untouched;
   - the field is optional on BOTH criticism outputs (the symmetry
     `CON-criticism-source.md` already asserts for `successor_question`).
   Mutation proof: deleting the ν-interface construction in
   `_argument_trial_steps` must turn the reinstatement test red. Recorded in
   VERIFY.md with the pasted failure.

## Existing tests at risk (from the blast-radius consumer list, all read)

| Test | Verdict |
|---|---|
| `tests/test_wire_contracts.py` (critic schema/compile) | must keep passing; a new optional property with an empty default breaks no existing document |
| `tests/test_schema_carries_every_prose_rule.py::test_alias_bearing_fields_name_their_legal_values_in_the_schema` | must keep passing; the new field is ADDED to its critic case so the enum protection is asserted for it too |
| `tests/test_successor_law_line.py`, `tests/test_successor_wire_carry.py` | must keep passing untouched — they pin a different optional field and the law that nothing reads it |
| `tests/test_crit_batch.py`, `tests/test_compact_role_alias_integration.py` | must keep passing; batch cases without the field compile as before |
| `tests/test_prose_refutation_boundaries.py`, `tests/test_criticism_authority.py`, `tests/test_text_authority_policy.py`, `tests/test_judge_ensemble_boundary.py`, `tests/test_v6_defended_trial_transaction_wiring.py` | must keep passing; every one of them calls the trial with no declaration, which is the unchanged path |
| `tests/test_crit_pack_legacy_golden.py`, `tests/test_conj_pack_legacy_golden.py` and `tests/fixtures/*_pack_legacy_v0/*.txt` | **must keep passing with the fixture files UNEDITED** — this tranche's own constraint. No reference-menu declaration is registered for the new field (a menu renders into the pack and would move the goldens); PARKED P3 carries that as its own tranche |
| `tests/test_role_prompt_registry.py` | must keep passing; it compares `render_role_prompt` against `TEMPLATES[role]`, so a template edit moves both sides together |

No test's fixture depended on the defect, so no fixture is updated.

## Explicitly not changed

`src/deepreason/adjudication/` — the tempting neighbour. The evidence closure
and the pass-2 `SUSPENDED_UNSUPPORTED` rule are both correct and both proved
so by REPRO.md's arms B and C. GOAL.md makes an adjudication edit a STOP; none
is needed, and the reproduction is the evidence for that rather than a hope.

`cited_input_aliases` — the nearest existing field. It means "I looked at
this", not "withdraw this and my case falls", and its resolution is flattened
into the case string. Left exactly as it is; PARKED P1.

## Estimated diff

~65 lines of production code across 5 files (contracts.py ~16, wire.py ~22,
crit.py ~4, trial.py ~17, roles.py ~6), plus the new test file, the two
experiment scripts and the map document. Production diff is well under the
150-line budget.

## Approval gate

GOAL.md class is `defect`; the diff estimate is under 150 lines; the
blast-radius verdict is CLEAR with no frozen or frozen-adjacent contact.
Proceeding to `dr-implement-fix` without an operator stop, as the orchestrator's
gate provides.
