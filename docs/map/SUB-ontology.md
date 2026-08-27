<!-- DR-SUB-ontology -->
Verified-at: 1662a3f96
Verify: python -m pytest tests/test_ontology.py -q
Owns: src/deepreason/ontology/
Seams: DR-SEAM-ontology-x-rules, DR-SEAM-evaluation-x-ontology, DR-SEAM-llm-x-verification
Seams-undocumented: adjudication x ontology, bridge x ontology, capabilities x ontology, harness x ontology, ontology x scratch, ontology x workflow

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

## Seams

| Side | Status | What the agreement is (one line) |
|---|---|---|
| `DR-SEAM-ontology-x-rules` | documented | the ontology lends the rules a vocabulary and keeps the right to define it — a rule may bring seven of the ontology's models into existence, never redefine them |
| `DR-SEAM-evaluation-x-ontology` | documented | the ontology hands evaluation an `Artifact` whose identity is `sha256(canonical(content_ref, codec, interface))` and one guarantee about it |
| adjudication x ontology | undocumented | real, already confirmed from the adjudication side: `DR-SUB-adjudication`'s entire import surface is `deepreason.ontology` plus itself |
| harness x ontology | undocumented | real, already confirmed from the harness side: `harness.py` imports `deepreason.ontology` at module level — `Event`/`Artifact`/`Status` are materialized here from ontology's types |
| bridge x ontology | undocumented, unusually directed | real: `ontology/event.py` imports the BRIDGE event envelope (not the reverse) — confirmed from `DR-SUB-bridge`'s own Seams table, which is why `bridge/`'s top-level `__init__.py` stays import-light to avoid closing the cycle |
| capabilities x ontology | undocumented, unusually directed | real, same shape as bridge: `ontology/event.py` loads the capability event envelope — confirmed from `DR-SUB-capabilities`'s own Seams table |
| ontology x scratch | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| ontology x workflow | undocumented | not evidenced here either way — candidate pair, not yet analyzed |

## Entry points
- `Artifact` — the untyped content object; `Artifact.compute_id(content_ref, codec, interface)` is the content address.
- `Interface`, `Ref`, `RefRole` — the attack/support surface: `dependence` builds `dep`, `evidence` feeds validity-node closure, `mention` is inert for edges.
- `Provenance`, `ProvenanceRole` — generator role plus the school that conditioned it; never an input to status.
- `Commitment`, `Budget` — a decidable test `eval` (`program:` / `predicate:` / `rubric:`) with a finite declared budget.
- `Problem`, `ProblemProvenance`, `SpawnTrigger` — the frontier item and the nine typed reasons a problem exists. `SUCCESSOR` is inert: a failed verdict mints nothing (H1) and the decommissioned website pipeline's remnant producer is gone, so the name survives with nothing behind it.
- `Warrant`, `WarrantType` — a contentful attack; `validity_node` is the attackable claim that the test was sound and relevant.
- `EpistemicState` — the materialized view `(A, Pi, carries, att, dep, addr, status, hv, reach, conn)` the harness rebuilds by replay.
- `Status` — the four labels the two-pass adjudicator assigns.
- `Event`, `Rule` — one append-only log line and the fifteen rules that can produce one.
- `StateDiff` — the graph delta an event applies, under its on-record aliases (`att+`, `dep+`, `A+`, `Π+`, `addr+`, `carry+`).
- `LLMCall`, `LLMAttempt` — provider accounting and per-attempt repair trace; process-only, never graph state. `LLMAttempt.natural_stop` (did the provider end this completion on its own, or at the cap?) is WRITTEN AND NEVER READ: it is a correctness signal, and letting a guard, rank, status, label or warrant consume it would make it an evidence signal, which the seats/evidence law forbids. `split_legs` carries the two `LLMSplitLegV1` records of one split-budget seat call (`llm/split.py`), and `split_notice` the typed reason the protocol was not honored when it was not — on the ATTEMPT rather than on a leg, because the seats it describes are exactly the ones with no legs. **A LEG IS NOT AN ATTEMPT**, and this is the field that says so: `attempt_trace` is the repair ladder, whose index means "how many times this call was told its value was wrong", and the two legs of a split are one such value produced by two provider requests. Recording them as ladder entries is a real recorded defect — it made every thinking-ON run replay-invalid against four unrelated checks at once (`experiments/2026-08-27-defect-split-leg-recording/`). Each leg keeps its own wire cap rather than reusing `max_tokens`, because `invariants.py`'s `attempt-limits` check admits only route-authorized caps and a leg's share of the ceiling is not one: `LLMAttempt.max_tokens` is the authorized envelope, `LLMSplitLegV1.max_tokens` the wire value, and `DR-SEAM-llm-x-verification` checks the pair against the envelope.
- `SchoolRouteReceiptV1`, `ConjectureContextCallReceiptV1` — durable proof of the routing and the advisory scratch a conjecture call actually saw.
- `deepreason.ontology.frozen` — compatibility re-export of `FrozenRecord`/`FrozenList`/`FrozenDict` from `deepreason.frozen`, used by the two process-payload modules (`scratch/events.py`, `bridge/events.py`) that reach back through the ontology package; the other three import `deepreason.frozen` directly.

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
`check: python -c "from deepreason.storage.objects import SCHEMAS; from deepreason.ontology import Artifact, Commitment, Problem, Warrant, Rule, EpistemicState as S; assert [SCHEMAS[k] for k in ('artifact','commitment','warrant','problem')]==[Artifact,Commitment,Warrant,Problem]; assert set(S.model_fields)=={'artifacts','problems','carries','att','dep','addr','status','hv','reach','conn'}; assert len(Rule)==15"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| what bytes an artifact's identity covers | `Artifact.compute_id` in `ontology/artifact.py` | `tests/test_ontology.py::test_compute_id_deterministic_and_content_sensitive` |
| add a ref role, or what a role means for the graph | `RefRole` in `ontology/artifact.py`, then `build_dep` / `build_att` in `adjudication/edges.py` | `tests/test_adjudication.py` |
| add a generator role (a new rule that authors artifacts) | `ProvenanceRole` in `ontology/artifact.py` — and nothing in `adjudication/` may branch on it | `tests/test_adjudication_blindness.py` |
| add a spawn trigger | `SpawnTrigger` in `ontology/problem.py`, then a `_spawn` branch in `rules/spawn.py` | `tests/test_harness_fixes.py::test_remove_arbitrariness_carries_root_description_and_criteria` |
| pin new criteria into every problem at registration | `POPPER_BATTERY` in `ontology/problem.py` (consumed by `Harness.register_problem`) | `tests/test_reflexive_discipline.py::test_debt_problem_asks_the_genuine_question` |
| add a status label | `Status` in `ontology/state.py`, then `final_labels` in `adjudication/support.py` | `tests/test_adjudication.py::test_support_cascade_orphaned_not_false` |
| change what counts as a "survivor" on ANY surface | `counts_as_survivor` / `is_import_admission` in `ontology/state.py` — the ONE place the rule lives; `scheduler.run_report`, `Scheduler._select_problem` and `application.results._survivor_count` all call it and none re-spells it | `tests/test_import_role_survivors.py::test_one_authority_names_the_rule_and_every_survivor_surface_calls_it` |
| add a materialized relation to the view | `EpistemicState` in `ontology/state.py` + an aliased field on `StateDiff` in `ontology/event.py` + `Harness._apply_event` | `tests/test_adjudication.py::test_validity_attack_disables_every_carrier_of_a_warrant` |
| add a budget dimension a test program reads | `Budget.extra` in `ontology/commitment.py` | `tests/test_ontology.py::test_commitment_defaults` |
| add an event rule | `Rule` in `ontology/event.py` + the dispatch in `Harness._apply_event` | `tests/test_ontology.py::test_event_round_trip` |
| attach a new typed process payload to events | a new optional field on `Event` with `exclude_if`, plus a clause in `Event._process_payload_contract` | `tests/test_workflow_control_event_storage_c1.py::test_control_rule_and_payload_must_appear_together` |
| record new per-call provider accounting | `LLMAttempt` / `LLMCall` in `ontology/event.py` (defaults required for replay) | `tests/test_workflow_control_event_storage_c1.py::test_work_order_call_binding_is_conjecturer_only_and_legacy_shape_is_unchanged` |
| record a per-attempt provider signal that nothing may act on | a defaulted field on `LLMAttempt`, plus a no-consumer census pinning where its name may occur | `tests/test_seats_evidence_law.py::test_natural_stop_is_recorded_and_never_consumed` |
| persist a new record type under `objects/` | `SCHEMAS` in `storage/objects.py` | `tests/test_workflow_control_event_storage_c1.py::test_every_workflow_record_round_trips_through_shared_store` |

`check: python -c "
import inspect, pathlib
from deepreason.ontology.state import counts_as_survivor, is_import_admission
from deepreason.scheduler.scheduler import Scheduler, run_report
from deepreason.application import results
for site in (Scheduler._select_problem, run_report):
    assert 'counts_as_survivor' in inspect.getsource(site), site
assert 'is_import_admission' in inspect.getsource(results._survivor_count)
for module in (Scheduler, results):
    text = pathlib.Path(inspect.getfile(module)).read_text()
    assert 'ProvenanceRole.IMPORT' not in text, module
"`

`check: python -c "
from deepreason.ontology.event import LLMAttempt as A, LLMSplitLegV1 as L
assert {'natural_stop', 'split_notice', 'split_legs'} <= set(A.model_fields)
# The leg fields are GONE from the attempt: a leg name on a non-leg record is
# the borrowed costume the 2026-08-27 defect was made of.
assert not {'split_leg', 'split_max_tokens'} & set(A.model_fields)
a = A(prompt_ref='blob:p')
assert (a.natural_stop, a.split_notice, a.split_legs) == (None, '', ()), a
# A leg carries no attempt index and cannot be given one.
assert 'attempt' not in L.model_fields
" && test -z "$(grep -rl natural_stop src/deepreason --include=*.py | grep -vE '^src/deepreason/(ontology/event|llm/(adapter|split))\.py$')"`

**The survivor rule was spelled out at each surface, and one copy drifted.**
`selfstudy run-9175f0ec` installed "import-role admission records never count as
a survivor" in `Scheduler._select_problem` alone. `run-1b31f006` (poietics P-R1,
the first run here to bind a non-empty dossier at seed) then published **82
survivors, 24 of them IMPORT-role sections of the operator's own record**, all
registered at log seq 5-40 while the log's first LLM-bearing event is seq 85 —
so `deepreason results` reported as "positions still standing" 24 artifacts that
were accepted before any model was consulted. The map's own check could not see
it: it grepped for the literal in the file, and the file held one site that had
the clause and another that did not. FIXED 2026-08-25 by moving the rule to
`ontology/state.py` and leaving no consumer able to spell it
(`experiments/2026-08-25-fix-import-role-survivors/`).
`check: python -m pytest tests/test_import_role_survivors.py -q`

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
`check: python -c "from deepreason.canonical import canonical_json, sha256_hex; from deepreason.ontology import Artifact, Interface, Provenance; i=Interface(); mk=lambda w,p: Artifact(id=Artifact.compute_id('inline:x','utf8',i), content_ref='inline:x', codec='utf8', interface=i, warrants=w, provenance=p); a=mk(['w1'], Provenance(role='critic', school='school-3')); b=mk([], Provenance(role='conjecturer')); assert a.id==b.id and a!=b; assert a.id==sha256_hex(canonical_json({'content_ref':'inline:x','codec':'utf8','interface':i.model_dump(mode='json')}))"`

**These models declare less than they appear to.** Unlike `scratch/models.py`
records, which self-check `id == compute_id(...)` in a model validator, `Artifact`
accepts any id string — the harness only detects a *collision* (same id, different
content), so an artifact built without calling `compute_id` registers, replays,
and is wrong. Two module-level types in this package look load-bearing and bind
nothing: `Codec` is a `Literal[...] | str` union that admits any string *and is
referenced nowhere* — `Artifact.codec` is a bare `str` that accepts a junk codec —
and the `Verdict` enum in `ontology/commitment.py` is neither exported from
`deepreason.ontology` nor imported by any module, so `Warrant.verdict` is a plain
`str | None` that rules populate with the literal `"fail"`. Typing either field is
a change to on-record shapes, not a cleanup.
`check: python -c "import typing, pathlib, deepreason.ontology as o; from deepreason.ontology.artifact import Codec; from deepreason.ontology import Artifact, Interface, Provenance, Warrant; from deepreason.ontology.commitment import Verdict; a=Artifact(id='not-a-content-address', content_ref='inline:x', codec='not-a-declared-codec', interface=Interface(), provenance=Provenance(role='seed')); assert a.id != Artifact.compute_id(a.content_ref, a.codec, a.interface); assert Artifact.model_fields['codec'].annotation is str; assert typing.get_origin(Codec) is typing.Union and str in typing.get_args(Codec) and pathlib.Path('src/deepreason/ontology/artifact.py').read_text().count('Codec')==1; assert 'Verdict' not in o.__all__ and not hasattr(o,'Verdict') and Warrant.model_fields['verdict'].annotation==(str|None)" && ! grep -rEq "^[[:space:]]*(from|import).*\bVerdict\b" --include=*.py src tests`

**Only `RefRole.DEPENDENCE` builds a `dep` edge.** `EVIDENCE` refs are read by
`build_att` for validity-node closure and `MENTION` refs are edge-inert — but all
three are ordinary refs on the same `Interface`, so a role added without touching
`adjudication/edges.py` is silently a `mention`.
`check: python -c "from deepreason.adjudication.edges import build_dep; from deepreason.ontology import Artifact, Interface, Ref, Provenance; p=Provenance(role='seed'); mk=lambda n,r: Artifact(id=n, content_ref='inline:'+n, interface=Interface(refs=[Ref(target='t', role=r)]), provenance=p); arts={a.id: a for a in (Artifact(id='t', content_ref='inline:t', provenance=p), mk('d','dependence'), mk('e','evidence'), mk('m','mention'))}; assert build_dep(arts)=={('d','t')}, build_dep(arts)"`

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
`check: python -c "from deepreason.ontology.problem import POPPER_BATTERY, SpawnTrigger; assert POPPER_BATTERY == () and len(SpawnTrigger) == 10 and SpawnTrigger.PROMOTION"`

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
`check: python -c "import pytest; from pydantic import ValidationError; from deepreason.ontology.event import ConjectureContextCallReceiptV1 as R; h='0'*64; s='sha256:'+h; b1='sha256:'+'1'*64; b2='sha256:'+'2'*64; base=dict(manifest_digest=h, problem_id='p', formal_fence_seq=4, scratch_fence_seq=4, selection_receipt_ref=s, advisory_context_ref=s, render_receipt_ref=h, rendered_context_ref=h); assert R(**base).expansion_decision_ref is None; pytest.raises(ValidationError, R, **{**base,'scratch_fence_seq':5}); pytest.raises(ValidationError, R, **{**base,'expansion_decision_ref':s}); pytest.raises(ValidationError, R, **{**base,'expansion_decision_ref':s,'expansion_request_hash':s,'expansion_index':1,'added_block_refs':[b1],'root_block_refs':[b1]}); assert R(**base, expansion_decision_ref=s, expansion_request_hash=s, expansion_index=1, added_block_refs=[b1], root_block_refs=[b2]).expansion_index==1"`

**Immutability and aliasing are two separate failure modes.** `FrozenList` and
`FrozenDict` are `list`/`dict` subclasses with mutators disabled, so an in-place
mutation raises `TypeError`, not `ValidationError` (field *reassignment* on a
`FrozenRecord` raises `ValidationError`); their `__copy__`/`__deepcopy__` return
`self`. And `ProblemProvenance.from_` serializes as `from` — both spellings
construct under `populate_by_name=True`, but `log.jsonl` and `objects/problem/`
contain `from`, so a `by_alias=False` dump writes a key no existing root has.
`check: python -c "import copy, json, pytest; from pydantic import ValidationError; from deepreason.frozen import FrozenDict; from deepreason.ontology import Interface, Ref, ProblemProvenance, SpawnTrigger; i=Interface(refs=[Ref(target='x',role='mention')]); pytest.raises(TypeError, i.refs.append, Ref(target='y',role='mention')); pytest.raises(ValidationError, setattr, i.refs[0], 'target', 'y'); assert copy.copy(i.refs) is i.refs and copy.deepcopy(i.refs) is i.refs; d=FrozenDict({'a':1}); pytest.raises(TypeError, d.__setitem__, 'b', 2); assert copy.deepcopy(d) is d; p=ProblemProvenance(trigger=SpawnTrigger.SEED, from_=['a']); assert json.loads(p.model_dump_json(by_alias=True))['from']==['a'] and 'from_' not in json.loads(p.model_dump_json(by_alias=True))"`

**The ontology is not a leaf.** `ontology/event.py` imports the typed process
payloads from `scratch`, `bridge`, `capabilities`, `control_events` and
`conjecture_events`. Those modules stay importable only because none of them names
`deepreason.ontology` itself at top level: three (`capabilities/events.py`,
`control_events.py`, `conjecture_events.py`) import the leaf `deepreason.frozen`
directly, and two (`scratch/events.py`, `bridge/events.py`) go through the
`deepreason.ontology.frozen` re-export — which works only because importing a
*submodule* of a half-initialised package is legal while `from deepreason.ontology
import ...` is not. A top-level `from deepreason.ontology import ...` in any of the
five closes the cycle.
`check: grep -q "^from deepreason.ontology.frozen import" src/deepreason/scratch/events.py && grep -q "^from deepreason.ontology.frozen import" src/deepreason/bridge/events.py && grep -q "^from deepreason.frozen import" src/deepreason/capabilities/events.py && grep -q "^from deepreason.frozen import" src/deepreason/control_events.py && grep -q "^from deepreason.frozen import" src/deepreason/conjecture_events.py && ! grep -rq "^from deepreason.ontology import" src/deepreason/scratch/events.py src/deepreason/bridge/events.py src/deepreason/capabilities/events.py src/deepreason/control_events.py src/deepreason/conjecture_events.py`
