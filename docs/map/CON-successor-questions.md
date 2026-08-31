<!-- DR-CON-successor-questions -->
Verified-at: bc3175394
Verify: python -m pytest tests/test_successor_law_line.py tests/test_successor_registry.py tests/test_successor_questions.py tests/test_successor_minting.py tests/test_successor_rank_tie.py -q
Owns: src/deepreason/successor/__init__.py, src/deepreason/successor/registry.py, src/deepreason/successor/route.py, src/deepreason/successor/mint.py
Seams-undocumented: successor-questions x scratch, successor-questions x rules, successor-questions x scheduler

# Successor questions — the question a criticism proposes should be asked next

## What it is

A criticism may propose the question it thinks should be asked NEXT. The
proposal is one OPTIONAL string on the criticism output contracts, and this
package decides what happens to it: by default it becomes one advisory scratch
block linked to the problem it was proposed under, where a conjecturer seat
meets it through the ordinary attention pack. A second road — the proposal
becomes a PROBLEM, carrying `SpawnTrigger.SUCCESSOR` — is built and is OFF
unless a run switches it on.

The authority is the operator's law of 2026-08-29 (CLAUDE.md, "Successor
questions: optional to propose, routed by pluggable destination, minting gated
off-by-default"), captured verbatim in
`experiments/2026-08-30-change-successor-questions/REQUEST.md`.

THE CHANNEL IS LIVE. Rewritten 2026-08-30, and the paragraph it replaces said
the opposite: "NOTHING IN PRODUCTION CALLS THIS YET ... a live run today records
the field on the criticism output contract and routes nothing." That was true
as delivered and stopped being true when the operator answered Q3.

Q3 asked WHERE the one dispatch site may live — may the criticism side write to
the workshop? — and the answer is **ROAD B**: a reader OUTSIDE `rules/` walks
what criticism already recorded and routes what it finds
(`src/deepreason/successor/reader.py`). So `DR-SEAM-rules-x-scratch`'s
asymmetry survives as written rather than being overturned: `rules/crit.py`
takes a ZERO-LINE DIFF, and nothing under `rules/` names this package at all.

**How it reaches production without any decider naming it.** The two run paths
— `scheduler/scheduler.py::Scheduler._arg_crit` and `loop.py` — fire a HOOK
POINT after each criticism pass (`aftercycle.run_after_criticism`) and name no
channel at all. They have to: `tests/test_successor_law_line.py` forbids every
DECIDING package, the scheduler included, from naming this machinery, with an
EMPTY permitted-exception list, and that rule is about COUPLING rather than
spelling — so the answer is to have no coupling, not an exception. A build with
the hook unregistered runs cycles identically.

`aftercycle` DECLARES its hooks and resolves them lazily rather than letting
each package register itself on import, and that was measured rather than
preferred: with self-registration, importing `deepreason.scheduler.scheduler`
alone left the registry EMPTY, so the channel was armed only on import orders
that happened to touch `deepreason.config` first. A channel that works by
import accident is the defect this dispatch site exists to close.

So exactly TWO modules outside the package name it, and neither is a caller:
`aftercycle.py` holds the declared import path, and `config.py` imports the
registry's `DEFAULT_DESTINATION_ID` so a row id has one owner rather than two.
The check below pins that list and pins the absence under `rules/`.

`check: python -c "
import pathlib, re
root = pathlib.Path('src/deepreason')
pattern = re.compile(r'deepreason\.successor|from deepreason import successor')
found = sorted(
    str(p) for p in root.rglob('*.py')
    if 'successor/' not in str(p).replace(chr(92), '/')
    and pattern.search(p.read_text(encoding='utf-8'))
)
assert found == ['src/deepreason/aftercycle.py', 'src/deepreason/config.py'], found
assert not [f for f in found if '/rules/' in f], found
"`
`check: python -m pytest tests/test_successor_dispatch.py -q`

**What the reader can and cannot resolve, stated because it bounds one road.**
The question is a wire field, so the model's own JSON survives as the raw
completion blob; what does NOT survive is the call-local `AliasTable` that maps
`SRC_001` to a real target id. The PROBLEM is therefore always resolvable and
the TARGET is not: every artifact one criticism call attacks comes from one
problem's candidate set, so any target of that call yields the same problem
through `state.addr`. Routing needs only the problem and is fully live;
minting needs `from: [problem, target]`, so a call that criticised several
artifacts records a typed `ROUTED_TARGET_UNRESOLVED` and mints nothing. It
never guesses a target, and it never falls silent about not having one.

Three things it is deliberately NOT:

- **Not enforceable.** No pack parameter invites the field, no screen requires
  it, and nothing declines it. There is no invitation, so there is no decline
  to record.
- **Not a weight.** No declaration in this package carries a number, so there
  is no rank, score or admission weight for any configuration to set.
- **Not a second workshop.** The default destination reuses the block shape
  `scratch/authoring.py` already writes for an unresolved question, rather than
  inventing a parallel record.

## The three layers (`DR-INV-signal-contract`'s own vocabulary)

| Layer | Holds | What it takes to change |
|---|---|---|
| **FROZEN** | the interface `deepreason.successor` exports, and the law that a proposed question never reaches a label, a warrant, a rank or an admission decision | an operator design law |
| **VERSIONED** | `DESTINATIONS` and `GATES` — declarations with a registry version, not wiring | a declaration plus a recorded decision |
| **FREE** | which destination a run selects and whether it opens the minting gate | ordinary configuration |

A NEW destination enters by REGISTRATION, and reaches the routing path without
`route.py` being edited — which is checkable, and is checked, because a
modularity claim without a failable check is decoration. The check was driven
RED by making `route` branch on the row id and green again on restore
(`experiments/2026-08-30-change-successor-questions/proof/registry_modularity_red.txt`).

`check: python -m pytest tests/test_successor_registry.py::test_adding_a_destination_requires_no_edit_to_any_consumer -q`

No consumer names a row id, in this package or anywhere else in the tree: a
consumer that must know WHICH row it got has stopped consuming the interface
and started knowing the subsystem.

`check: python -m pytest tests/test_successor_registry.py::test_a_row_id_literal_appears_in_the_registry_and_nowhere_else -q`

## THE LAW LINE

> The successor-question field is OPTIONAL on criticism output — never
> required, never penalized. No successor field, destination row, receipt or
> minted problem may feed a label, a warrant, a rank, an admission decision, or
> any adjudication pass.

This is the formalism-optional law (`DR-CON-conjecture-kinds`'s R-g) and the
operator's seats guardrail applied to this channel. It is pinned four ways in
`tests/test_successor_law_line.py`, and pin 1 is mutation-proved — the registry
wired into the scheduler's own rank key turns it red
(`experiments/2026-08-30-change-successor-questions/proof/law_line_pin1_red.txt`),
as does a numeric field added to the declaration model
(`.../proof/law_line_pin2_red.txt`).

`check: python -m pytest tests/test_successor_law_line.py -q`

The packages that DECIDE anything — `scheduler`, `adjudication`, `informal`,
`rules`, plus `workflow` and `workflows`, which hold two of the four production
callers of the admission gate — name no part of this machinery, and the
permitted-exception list is EMPTY. The package list is not a hand-maintained
reading: `test_every_caller_of_the_admission_gate_is_inside_a_deciding_package`
censuses every caller of `anti_relapse.check` under `src/deepreason` and reddens
if one appears in a package the absence check does not scan. That emptiness
SURVIVED the answer to Q3, which is the point of road B: the dispatch site is a
reader outside `rules/`, so nothing inside `rules/` dispatches this channel and
nothing that decides reads the field. Before 2026-08-30 the emptiness meant
"the question is unanswered"; now it means "the answer preserved the
asymmetry", and the assertion is the same either way.

`check: python -m pytest tests/test_successor_law_line.py::test_nothing_that_labels_ranks_or_admits_reads_a_successor_question tests/test_successor_law_line.py::test_every_caller_of_the_admission_gate_is_inside_a_deciding_package -q`

## Entry points (library surface)

- `deepreason.successor.resolve(config)` — the destination row a run selects;
  an unregistered id falls back to the shipped default and discloses.
- `deepreason.successor.route(harness, config, *, problem_id, question,
  llm_call=None)` — send one filled question to that destination. Records
  exactly one typed receipt per FILLED question and nothing at all for an
  empty one.
- `deepreason.successor.mint(harness, config, *, problem_id, target_id,
  question)` — register the problem the question proposes, once. Returns None
  unless the gate is on.
- `deepreason.successor.unknown_destination_notices(config)` and
  `minting_notices(config)` — typed `CompileNoticeV1` disclosures. Neither ever
  refuses.

**Where the minting gate's warning actually lands (Q2, answered ROAD B,
2026-08-30).** The operator's law names the TEXT, "may cause critics to fully
consume conjecturer role", not the idea, so it is carried verbatim in two
places and paraphrased in neither: DECLARED on the `minting.v1` registry row,
and WRITTEN TO THE RUN'S OWN APPEND-ONLY RECORD by
`mint.py::_record_gate_warning_once` the first time the gate is consulted while
on. The record is the durable half — `minting_notices` is the compile-time
reading of the same declaration and still has no caller inside `src/`.

Three properties, each with a mutant behind it
(`experiments/2026-08-30-change-successor-questions/proof/q2_warning_mutants_red.txt`):
the receipt is written even when NO question was ever proposed, because the
warning is about the configuration rather than about any proposal; it is
written EXACTLY ONCE, idempotent by searching the record rather than by a
module flag, so a resumed run neither re-discloses nor falls silent; and an
ABSENT receipt is what says the gate was off.

Road A — appending the words to the manifest's stderr notice stream — was NOT
taken. It would have cost a second line inside `run_manifest.py`, i.e. a second
frozen-surface-4 contact, and the Q1 grant covers exactly two `data.pop` lines
and nothing else.

`check: python -m pytest tests/test_successor_minting.py -q`
`check: python -c "
from deepreason.signals import declaration
from deepreason.successor.mint import GATE_WARNING_RECEIPT
from deepreason.successor.registry import GATES, MINTING_GATE_ID
text = 'may cause critics to fully consume conjecturer role'
assert GATES[MINTING_GATE_ID].warning == text, GATES[MINTING_GATE_ID].warning
d = declaration(GATE_WARNING_RECEIPT)
assert d is not None and GATE_WARNING_RECEIPT.startswith(d.name)
assert d.unit != 'unspecified' and d.staleness != 'unspecified'
"`

`check: python -c "import deepreason.successor as s; assert set(s.__all__) == {'resolve','route','mint','dispatch_recorded_proposals','unknown_destination_notices','SUCCESSOR_DESTINATION_REGISTRY_VERSION','DESTINATIONS'}, s.__all__; assert callable(s.minting_notices) and callable(s.recorded_proposals)"`

## State it owns

None of its own. The default destination writes one ordinary
`scratch-block` object plus one `BLOCK_CREATED` scratch event through
`ScratchService.create_block`; the minting road registers one ordinary
`Problem`. Both are records the harness already owns, and this package adds no
schema and no store.

The LINK to the originating problem lives on `ScratchProvenanceV1.origin`,
which is a free string OUTSIDE the block's `body_hash` — so carrying it costs
no stored block id. `ScratchBlockBodyV1` is not widened: a field added there
moved every stored block's id, measured in-code as `ff609dcc` -> `248b3201`
for the same content.

`check: python -m pytest tests/test_successor_questions.py::test_a_filled_field_becomes_exactly_one_linked_block -q && ! grep -q "successor" src/deepreason/scratch/models.py`

Visibility is MEASURED rather than asserted: the routed block is selected by
`plan_conjecture_context` — the same call `Scheduler._plan_conjecture_context`
makes — and appears in the rendered pack's ordered block refs.

`check: python -m pytest tests/test_successor_questions.py::test_the_routed_block_reaches_a_conjecturer_context -q`

## Invariants

- `DR-INV-signal-contract` — the registry sits in its VERSIONED layer, and its
  receipts are declared signals with a real unit and a real staleness.

`check: python -m pytest tests/test_successor_registry.py::test_both_receipt_families_are_declared_signals -q`

- `DR-INV-frozen-surfaces` — nothing here touches one. The two per-run `Config`
  switches, and the two `data.pop` lines they owe `run_manifest.py`, are
  REQUESTED and not granted; until they are, `resolve` and `minting_enabled`
  read their selector by `getattr`, so the shipped defaults are correct with no
  `Config` field in existence.
- `DR-CON-scheduler-ranking` — a minted successor loses every rank TIE to the
  operator's seed question, in both selection modes, by construction.

`check: python -c "from deepreason.config import Config; from deepreason.successor import resolve, minting_enabled; assert resolve(Config()).id == 'scratchpad.v1'; assert minting_enabled(Config()) is False"`

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| Send questions somewhere other than the scratchpad | register a row + writer via `registry.register_destination`; select it by `SUCCESSOR_QUESTION_DESTINATION` — NOTE: no `Config` field carries this selector yet (Q1 pending); a real `Config` refuses it with `extra_forbidden`, so today only a non-`Config` configuration object can select a row | `tests/test_successor_registry.py::test_adding_a_destination_requires_no_edit_to_any_consumer` |
| Change what the scratchpad block looks like | `route.py::_write_scratch_block` — body shape only; never a new `ScratchBlockBodyV1` field | `tests/test_successor_questions.py` |
| Change what a run is TOLD when it opens the minting gate | the `warning` field on the `minting.v1` row in `registry.py` — never a paraphrase at an emit site | `tests/test_successor_minting.py::test_enabling_the_gate_discloses_the_operators_own_warning` |
| Add or re-declare a receipt this channel emits | declare it in `signals.py` under `DR-REC-add-signal`, never the emit site | its EXISTENCE, unit and staleness are pinned by `tests/test_successor_registry.py::test_both_receipt_families_are_declared_signals`, not by `tests/test_signal_contract.py`, which stays green when a declaration is deleted outright |
| Give the channel a per-run switch | `config.py` + the matching unconditional `data.pop` in `run_manifest.py::_versioned_source_config_data` — frozen surface 4, grant REQUIRED first | `tests/test_manifest_config_disclosure.py` |

## Traps

- **The producer's LOCATION is the invariant, not its existence.**
  `successor/mint.py` is the ONE producer of the SUCCESSOR trigger, and it
  lives outside `src/deepreason/rules/` on purpose: a mint site inside `rules/`
  would break `DR-SEAM-ontology-x-rules`'s two-site
  `ProblemProvenance.model_validate` count, and a branch inside `scan_spawns`
  would break `DR-SEAM-rules-x-scratch`'s six-name trigger set AND revive H1's
  deleted loop. `src/deepreason/rules/spawn.py` takes a zero-line diff.
`check: test "$(grep -rn "ProblemProvenance.model_validate" --include=*.py src/deepreason/rules/ | wc -l)" -eq 2 && python -m pytest tests/test_successor_minting.py::test_the_producer_is_outside_scan_spawns -q`

- **The field must default to `None`, never `""`.** `_canonical_value` dumps
  with `exclude_none`, so `None` drops out and an empty string does not: a
  default of `""` would add a key to every critic output ever recorded. This is
  the same trap `ScratchBlockBodyV1`'s advisory refs already paid for once.
`check: python -c "from deepreason.llm.contracts import ArgumentativeCriticOutput as O; assert O.model_fields['successor_question'].default is None; assert 'successor_question' not in O(attack=False).model_dump(exclude_none=True)"`

- **A wire field named with the substring `scratch` turns a map check RED.**
  `DR-SEAM-rules-x-scratch` enumerates Critic-named wire models DYNAMICALLY and
  forbids any field whose name contains it, so the mirror field is
  `successor_question` on both `CompactCritic` and `BatchCriticCaseWireV2`
  rather than anything naming its destination — which is also correct on the
  merits, because the destination is configuration and the field is not.
`check: python -c "import inspect;from pydantic import BaseModel;from deepreason.llm import wire;K=[getattr(wire,n) for n in dir(wire) if 'Critic' in n and inspect.isclass(getattr(wire,n))];M=[c for c in K if issubclass(c,BaseModel)];assert M;F=[(c.__name__,f) for c in M for f in c.model_fields if 'scratch' in f];assert not F,F;assert {'CompactCritic','BatchCriticCaseWireV2'} <= {c.__name__ for c in M if 'successor_question' in c.model_fields}"`

- **Routing into a run whose workshop is OFF must DISCLOSE, not discard.**
  A question written into a disabled scratch policy would otherwise vanish with
  no trace, and the record is the only admissible evidence about what a run
  did. Reproduced as a mutant in
  `experiments/2026-08-30-change-successor-questions/proof/route_mutants_red.txt`.
`check: python -m pytest tests/test_successor_questions.py::test_a_scratch_disabled_run_discloses_instead_of_discarding -q`

- **Two map checks count FILES BY THE WORDS IN THEM, so a new module can move
  them without importing anything.** `DR-SEAM-harness-x-workflow` pins the
  number of files under `src/deepreason` containing both `harness` and
  `workflow` at 59, and `DR-SEAM-scratch-x-workflow` pins `scratch` × `workflow`
  at 48. `route.py` originally read the run's scratch policy from
  `harness._workflow_manifest` and moved BOTH counts to 60 and 49 — two map
  documents red, from one attribute name, with no import and no behavioural
  coupling at all. It reads the policy from the CONFIGURATION instead, which is
  where a manifest-launched run has it reconstructed anyway, so there is one
  answer rather than two that can disagree. Found and fixed 2026-08-30 in this
  tranche's own `docs_verify` run, before the branch was handed on.
`check: test "$(for f in $(grep -rl harness --include=*.py src/deepreason); do grep -ql workflow "$f" && echo x; done | wc -l)" -eq 59 && test "$(for f in $(grep -rl scratch src/deepreason --include=*.py); do grep -ql workflow "$f" && echo x; done | wc -l)" -eq 48 && ! grep -q "_workflow_manifest" src/deepreason/successor/route.py && grep -q "getattr(config, \"scratchpad\", None)" src/deepreason/successor/route.py`

- **`ScratchAuthoringService.author_block` is the wrong door.** Its
  `block_role` is a closed `Literal["conjecturer","synthesizer"]` that enters
  the qualification subject's pair inventory, so widening it to admit a critic
  role is a frozen surface 4 AND 5 contact costing a full battery per home.
  `ScratchService.create_block` takes no role parameter and is the door this
  package uses.
`check: grep -q 'block_role: Literal\["conjecturer", "synthesizer"\]' src/deepreason/run_manifest.py && ! grep -q "author_block" src/deepreason/successor/route.py`
