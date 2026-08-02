<!-- DR-SUB-ontology -->
Verified-at: 08dcdf3c
Verify: python -m pytest tests/test_ontology.py -q
Owns: src/deepreason/ontology/
Seams: 
Seams-undocumented: adjudication x ontology, bridge x ontology, capabilities x ontology, harness x ontology, ontology x rules, ontology x scratch, ontology x workflow

# Ontology — the one schema every other subsystem speaks

## What it is
The ontology package is the closed vocabulary of the record: artifacts,
commitments, warrants, problems, epistemic status, and the event that appends any
of them to the log. It exists so that meaning is never carried by a type tag.
Artifacts are untyped by construction — there is no `kind` field — so dispatch is
forced onto interface *structure*: a carried warrant is an attack edge, a
`dependence` ref is a support edge, and everything else is inert. Provenance
(who generated a thing, under which school) is recorded but epistemically inert
by design, which is what keeps adjudication blind to authorship. Every record is
a frozen pydantic model with immutable sequences and mappings, because the log is
append-only and a mutable in-memory record would let a later reader disagree with
the bytes on disk.

## Entry points
- `Artifact` — the untyped content object; `Artifact.compute_id(content_ref, codec, interface)` is the content address.
- `Interface`, `Ref`, `RefRole` — the attack/support surface: `dependence` builds `dep`, `evidence` feeds validity-node closure, `mention` is inert for edges.
- `Provenance`, `ProvenanceRole` — generator role plus the school that conditioned it; never an input to status.
- `Commitment`, `Budget` — a decidable test `eval` (`program:` / `predicate:` / `rubric:`) with a finite declared budget.
- `Problem`, `ProblemProvenance`, `SpawnTrigger` — the frontier item and the nine typed reasons a successor problem exists.
- `Warrant`, `WarrantType` — a contentful attack; `validity_node` is the attackable claim that the test was sound and relevant.
- `EpistemicState` — the materialized view `(A, Pi, carries, att, dep, addr, status, hv, reach, conn)` the harness rebuilds by replay.
- `Status` — the four labels the two-pass adjudicator assigns.
- `Event`, `Rule` — one append-only log line and the fifteen rules that can produce one.
- `StateDiff` — the graph delta an event applies, under its on-record aliases (`att+`, `dep+`, `A+`, `Π+`, `addr+`, `carry+`).
- `LLMCall`, `LLMAttempt` — provider accounting and per-attempt repair trace; process-only, never graph state.
- `SchoolRouteReceiptV1`, `ConjectureContextCallReceiptV1` — durable proof of the routing and the advisory scratch a conjecture call actually saw.
- `deepreason.ontology.frozen` — compatibility re-export of `FrozenRecord`/`FrozenList`/`FrozenDict`, imported by the process-payload modules that `Event` in turn imports.

## State it owns
Nothing at runtime — the package is pure schema and holds no module-level mutable
state. It does define the shapes of everything that persists: each line of
`log.jsonl` is one `Event`; `objects/artifact/`, `objects/commitment/`,
`objects/warrant/` and `objects/problem/` hold the four ontology records under the
names registered in `storage/objects.py::SCHEMAS`; an artifact id *is* the sha256
over canonical JSON of `(content_ref, codec, interface)`. `EpistemicState` is
in-memory only and is never ground truth — `status`, `hv`, `reach` and `conn` are
recomputed from the log at any `seq`.

`Artifact.warrants` is the legacy on-record shorthand for carriage; the
authoritative relation is `EpistemicState.carries`, appended through
`StateDiff.carry_add`. Warrants and commitments themselves are *not* in the view —
the harness keeps them in its own `self.warrants` / `self.commitments` maps,
persisted through the object store under the four registered schema names.
`check: python -c "from deepreason.storage.objects import SCHEMAS; from deepreason.ontology import Artifact, Commitment, Problem, Warrant, EpistemicState as S; assert [SCHEMAS[k] for k in ('artifact','commitment','warrant','problem')]==[Artifact,Commitment,Warrant,Problem]; assert set(S.model_fields)=={'artifacts','problems','carries','att','dep','addr','status','hv','reach','conn'}"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| what bytes an artifact's identity covers | `Artifact.compute_id` in `ontology/artifact.py` | `tests/test_ontology.py::test_compute_id_deterministic_and_content_sensitive` |
| add a ref role, or what a role means for the graph | `RefRole` in `ontology/artifact.py`, then `build_dep` / `build_att` in `adjudication/edges.py` | `tests/test_adjudication.py` |
| add a generator role (a new rule that authors artifacts) | `ProvenanceRole` in `ontology/artifact.py` — and nothing in `adjudication/` may branch on it | `tests/test_adjudication_blindness.py` |
| add a spawn trigger | `SpawnTrigger` in `ontology/problem.py`, then a `_spawn` branch in `rules/spawn.py` | `tests/test_harness_fixes.py::test_remove_arbitrariness_carries_root_description_and_criteria` |
| pin new criteria into every problem at registration | `POPPER_BATTERY` in `ontology/problem.py` (consumed by `Harness.register_problem`) | `tests/test_ontology.py::test_problem_provenance_alias` |
| add a status label | `Status` in `ontology/state.py`, then `final_labels` in `adjudication/support.py` | `tests/test_adjudication.py::test_support_cascade_orphaned_not_false` |
| add a materialized relation to the view | `EpistemicState` in `ontology/state.py` + an aliased field on `StateDiff` in `ontology/event.py` + `Harness._apply_event` | `tests/test_adjudication.py::test_validity_attack_disables_every_carrier_of_a_warrant` |
| add a budget dimension a test program reads | `Budget.extra` in `ontology/commitment.py` | `tests/test_ontology.py::test_commitment_defaults` |
| add an event rule | `Rule` in `ontology/event.py` + the dispatch in `Harness._apply_event` | `tests/test_ontology.py::test_event_round_trip` |
| attach a new typed process payload to events | a new optional field on `Event` with `exclude_if`, plus a clause in `Event._process_payload_contract` | `tests/test_workflow_control_event_storage_c1.py::test_control_rule_and_payload_must_appear_together` |
| record new per-call provider accounting | `LLMAttempt` / `LLMCall` in `ontology/event.py` (defaults required for replay) | `tests/test_workflow_control_event_storage_c1.py::test_work_order_call_binding_is_conjecturer_only_and_legacy_shape_is_unchanged` |
| persist a new record type under `objects/` | `SCHEMAS` in `storage/objects.py` | `tests/test_workflow_control_event_storage_c1.py::test_every_workflow_record_round_trips_through_shared_store` |

## Traps

**There is no `kind` field, and adding one is not a schema change but a theory
change.** Untypedness (Def 3.2) is what forces dispatch onto interface structure;
a discriminator would let a generator declare its own epistemic weight.
`check: python -m pytest tests/test_ontology.py::test_artifact_has_no_kind_field -q`

**An artifact's identity does not cover its warrants or its provenance.** Two
critics emitting byte-identical prose against different targets produce the *same*
artifact id. That is why carriage had to move out of `Artifact.warrants` and into
`EpistemicState.carries` / `StateDiff.carry_add` — content dedupe would otherwise
silently erase the second attack edge.
`check: python -c "from deepreason.ontology import Artifact, Interface, Provenance; i=Interface(); b=Artifact.compute_id('inline:x','utf8',i); a=Artifact(id=b, content_ref='inline:x', codec='utf8', interface=i, warrants=['w1'], provenance=Provenance(role='critic', school='school-3')); assert Artifact.compute_id(a.content_ref,a.codec,a.interface)==b"`

**These models declare less than they appear to.** Unlike `scratch/models.py`
records, which self-check `id == compute_id(...)` in a model validator, `Artifact`
accepts any id string — the harness only detects a *collision* (same id, different
content), so an artifact built without calling `compute_id` registers, replays,
and is wrong. Likewise `Codec` is a `Literal[...] | str` union that admits any
string, and the `Verdict` enum is neither exported from `deepreason.ontology` nor
imported anywhere: `Warrant.verdict` is a plain `str | None` that rules populate
with the literal `"fail"`. Typing either field is a change to on-record shapes,
not a cleanup.
`check: python -c "import deepreason.ontology as o; from deepreason.ontology.commitment import Verdict; from deepreason.ontology import Artifact, Interface, Provenance, Warrant; a=Artifact(id='not-a-content-address', content_ref='inline:x', interface=Interface(), provenance=Provenance(role='seed')); assert a.id != Artifact.compute_id(a.content_ref, a.codec, a.interface); assert Artifact.model_fields['codec'].annotation is str; assert 'Verdict' not in o.__all__ and Warrant.model_fields['verdict'].annotation != Verdict"`

**Only `RefRole.DEPENDENCE` builds a `dep` edge.** `EVIDENCE` refs are read by
`build_att` for validity-node closure and `MENTION` refs are edge-inert — but all
three are ordinary refs on the same `Interface`, so a role added without touching
`adjudication/edges.py` is silently a `mention`.
`check: grep -q "ref.role == RefRole.DEPENDENCE" src/deepreason/adjudication/edges.py`

**Provenance is never a warrant (D2).** `role` and `school` may steer packs and
scheduling; no adjudication code reads them, and that blindness is the property,
not an accident of the current implementation.
`check: python -c "from deepreason.ontology.artifact import ProvenanceRole; assert {'seed','conjecturer','critic','variator','synthesizer','import','user','controller','experimenter'}=={r.value for r in ProvenanceRole}" && ! grep -rq provenance src/deepreason/adjudication/*.py`

**`SUSPENDED_UNSUPPORTED` is not `REFUTED`.** Pass 2 assigns it when an artifact
survives attack semantics but a dependence did not — orphaned, not false. Code
that treats "not accepted" as refuted misreads three of the four labels.
`check: python -c "from deepreason.ontology import Status; assert [s.value for s in Status]==['accepted','refuted','suspended','suspended_unsupported']"`

**`POPPER_BATTERY` is empty.** The auto-pinning mechanism in
`Harness.register_problem` is structural and live, but it currently pins nothing;
a test asserting battery contents would be asserting aspiration, not behaviour.
`check: python -c "from deepreason.ontology.problem import POPPER_BATTERY, SpawnTrigger; assert POPPER_BATTERY == () and len(SpawnTrigger) == 9"`

**Every optional `Event` / `LLMCall` field carries `exclude_if=lambda value: value
is None` so that a formal event still serializes to its historical key set.**
Dropping `exclude_if` — or giving a new field a non-`None` default — changes the
bytes of already-committed logs and invalidates existing replay-valid roots. See
`DR-INV-frozen-surfaces`.
`check: python -c "import json; from deepreason.ontology import Event, Rule; d=json.loads(Event(seq=0, ts='2026-01-01T00:00:00Z', rule=Rule.REGISTER).model_dump_json(by_alias=True)); assert set(d)=={'seq','ts','rule','inputs','outputs','llm','state_diff'}, sorted(d)"`

**Rule and typed payload are mutually implying, a process event may not touch
formal state, and preconstructed payloads are re-parsed on the way in.**
`Event._process_payload_contract` requires `Rule.SCRATCH` iff `scratch`,
`Rule.BRIDGE` iff `bridge`, and so on; it mirrors `inputs`/`outputs` between the
event and its payload and rejects any nonempty `StateDiff` on a process event.
Separately, pydantic trusts an already-built instance, so `model_copy(update=...)`
could bypass `LLMCall` and control/capability validators on the live append path
and then fail on reopen — a torn tail; `Event`'s `mode="before"` validators
re-validate those payloads from their dumps.
`check: python -m pytest tests/test_workflow_control_event_storage_c1.py::test_control_rule_and_payload_must_appear_together tests/test_workflow_control_event_storage_c1.py::test_control_event_deeply_revalidates_preconstructed_payloads -q`

**A work order on an `LLMCall` is conjecturer-only unless a transactional
authorization bundle accompanies it.** Copying a well-formed content address is
not authority; `dispatch_authorization_ref` and `work_order_id` must appear
together, and exact `prompt_tokens`/`completion_tokens` must sum to `tokens`.
`check: python -m pytest tests/test_workflow_control_event_storage_c1.py::test_work_order_call_binding_is_conjecturer_only_and_legacy_shape_is_unchanged -q`

**`ConjectureContextCallReceiptV1` requires one state prefix and all-or-nothing
expansion lineage.** `formal_fence_seq` must equal `scratch_fence_seq`; an
`expansion_decision_ref` demands the complete lineage evidence (request hash,
index, added blocks) and root/added block sets must be disjoint.
`check: python -c "import pytest; from pydantic import ValidationError; from deepreason.ontology.event import ConjectureContextCallReceiptV1 as R; h='0'*64; s='sha256:'+h; pytest.raises(ValidationError, R, manifest_digest=h, problem_id='p', formal_fence_seq=4, scratch_fence_seq=5, selection_receipt_ref=s, advisory_context_ref=s, render_receipt_ref=h, rendered_context_ref=h)"`

**Immutability and aliasing are two separate failure modes.** `FrozenList` and
`FrozenDict` are `list`/`dict` subclasses with mutators disabled, so an in-place
mutation raises `TypeError`, not `ValidationError` (field *reassignment* on a
`FrozenRecord` raises `ValidationError`); their `__copy__`/`__deepcopy__` return
`self`. And `ProblemProvenance.from_` serializes as `from` — both spellings
construct under `populate_by_name=True`, but `log.jsonl` and `objects/problem/`
contain `from`, so a `by_alias=False` dump writes a key no existing root has.
`check: python -c "import json, pytest; from pydantic import ValidationError; from deepreason.ontology import Interface, Ref, ProblemProvenance, SpawnTrigger; i=Interface(refs=[Ref(target='x',role='mention')]); pytest.raises(TypeError, i.refs.append, Ref(target='y',role='mention')); pytest.raises(ValidationError, setattr, i.refs[0], 'target', 'y'); p=ProblemProvenance(trigger=SpawnTrigger.SEED, from_=['a']); assert json.loads(p.model_dump_json(by_alias=True))['from']==['a']"`

**The ontology is not a leaf.** `ontology/event.py` imports the typed process
payloads from `scratch`, `bridge`, `capabilities`, `control_events` and
`conjecture_events`. Those modules stay importable only because they reach for
`deepreason.ontology.frozen` (a re-export of `deepreason.frozen`) rather than
`deepreason.ontology`; a top-level `from deepreason.ontology import ...` in any of
them closes the cycle.
`check: ! grep -rq "^from deepreason.ontology import" src/deepreason/scratch/events.py src/deepreason/bridge/events.py src/deepreason/capabilities/events.py src/deepreason/control_events.py src/deepreason/conjecture_events.py`
