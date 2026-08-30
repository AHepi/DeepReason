# Spec for: successor questions — optional to propose, routed by pluggable destination, minting gated off-by-default

Traces: every item cites R/C numbers from `REQUEST.md`. Untraceable items are bugs.

Tranche: `experiments/2026-08-30-change-successor-questions/`
Branch: `claude/b2-lane-B` (worktree `/home/user/dr-lanes/lane-B`)
Family: `dr-change-orchestrator`. Phase: `dr-spec-change`. NO implementation code
exists at the time this document is committed, and none may be written before
the STOPs below are answered — S14, S15, S19 and S24 are grant-gated outright,
and S9/S13 are provisional on Q3.

## Map preflight

The `DR-` ids this work resolves to are recorded in `REQUEST.md` under "Map
preflight", together with the FINDING that the map has no id for the module
this change must create and the proposal to add `DR-CON-successor-questions`
owning `src/deepreason/successor/`. Read in INDEX.md's prescribed order: the
seams (`DR-SEAM-rules-x-scratch`, `DR-SEAM-ontology-x-rules`,
`DR-SEAM-llm-x-rules`) before the subsystems, and `DR-INV-frozen-surfaces`
before designing anything.

## Items

Grouped into the five ordered sub-tranches the Budget section splits this work
into. Every `accept:` is a command, never a judgement.

### B-i — the optional field, and the law line that keeps it optional

S1 (R1, C1): `src/deepreason/llm/contracts.py` | before: `ArgumentativeCriticOutput`
and `BatchCase` carry `attack`, `case`, `counterexample`, `premise`,
`premise_evidence` | after: both carry one further OPTIONAL field
`successor_question: str | None = None`, defaulting to `None` (never `""` and
never `[]`, so an unfilled field canonicalises to the bytes it always did under
`exclude_none`), commented in the shape `premise_evidence`'s own comment uses:
optional, absent-legal, never required, never penalized. No new role, no new
`contract_id`.
    accept: `python -c "from deepreason.llm.contracts import ArgumentativeCriticOutput as O, BatchCase as B;
assert 'successor_question' in O.model_fields and 'successor_question' in B.model_fields;
assert O(attack=False).successor_question is None;
assert 'successor_question' not in O(attack=False).model_dump(exclude_none=True)"` -> exit 0

S2 (R1): `src/deepreason/llm/wire.py` | before: `CompactCritic` and
`BatchCriticCaseWireV2` mirror the contract fields and their `compile()` methods
map them across | after: both mirror `successor_question` and both `compile()`
methods carry it onto the contract. The field name contains no substring
`scratch` (a `docs/map/SEAM-rules-x-scratch.md` check enumerates Critic-named
wire models dynamically and forbids it).
    accept: `python -m pytest tests/test_wire_contracts.py tests/test_crit_batch.py tests/test_v6_patch_repair_and_wire.py tests/test_reference_menu.py::test_wire_schema_sha_does_not_move -q` -> `0 failed`
    accept: `python -c "import inspect;from pydantic import BaseModel;from deepreason.llm import wire;K=[getattr(wire,n) for n in dir(wire) if 'Critic' in n and inspect.isclass(getattr(wire,n))];M=[c for c in K if issubclass(c,BaseModel)];F=[(c.__name__,f) for c in M for f in c.model_fields if 'scratch' in f];assert not F,F"` -> exit 0
    accept: `python -m pytest tests/test_discharge_wire.py::test_the_qualification_subject_digest_does_not_move tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move -q` -> `2 passed`, with no literal in either test edited

S3 (R1, C1, C3): `tests/test_successor_law_line.py` (new) | before: nothing
proves the field is unread by deciding code | after: four pins on
`tests/test_discharge_law_line.py`'s model — (1) an ABSENCE of every successor
name over the four deciding packages (`scheduler`, `adjudication`, `informal`,
`rules`) with positive anchors so a rename cannot make it vacuous; (2) the
destination declaration model has NO field annotated `int` or `float`, checked
over the MODEL rather than today's rows, so there is no weight for any
configuration to set; (3) admission is byte-identical with and without a filled
successor question on one graph; (4) no status label differs between a
field-filled and a field-absent run on one graph. Pin 1 is MUTATION-PROVED RED
before it is written down (wire the field into a rank or label computation in a
scratch copy) and the red capture is committed under the tranche's `proof/`.
    accept: `python -m pytest tests/test_successor_law_line.py -q` -> `0 failed`
    accept: `test -s experiments/2026-08-30-change-successor-questions/proof/law_line_pin1_red.txt` -> exit 0

S4 (R1, C9): `docs/map/CON-criticism-source.md` | before: no row or trap for a
successor question | after: one "Where to change what" row naming the field and
its destination registry, and one Traps entry recording that the field is
optional-and-unread-by-anything-that-decides, each carrying a `check:` at column
0 that fails if the property regresses. `Verified-at:` advanced only if this
document's checks were actually re-run.
    accept: `python tools/docs_verify.py 2>&1 | grep -c "FAIL CON-criticism-source"` -> `0`

### B-ii — the destination registry (VERSIONED, REGISTERED, plugin-shaped)

S5 (R3, R6, C3, C4, C5): `src/deepreason/successor/registry.py` (new) | before:
no such module | after: a frozen declaration dataclass on `channels.py`'s and
`discharge/policy.py`'s shape — `id`, `routes` (producer-agnostic semantics of
where a filled question goes), `default` (bool), `enforcement` (where the
routing decision is actually read), `authority` (the operator words the row
answers to), and `warning` (the text a gate row discloses when switched on);
NO field annotated `int` or `float`; a `SUCCESSOR_DESTINATION_REGISTRY_VERSION`
string; a rows mapping whose default row is the scratchpad; a `resolve(config)`
returning the declaration a configuration selects; and
`unknown_destination_notices(config)` returning typed `CompileNoticeV1` values
with `CompileNoticeV1` imported AT CALL TIME (the `channels.py` pattern), so an
unknown id FALLS BACK to the shipped default and DISCLOSES rather than refusing
(C5). `resolve` reads the selector by `getattr(config, FIELD, <default id>)`, so
this item lands and is provable BEFORE the grant-gated `Config` field of S14.
    accept: `python -c "
from types import SimpleNamespace as N
import deepreason.successor as s
assert isinstance(s.SUCCESSOR_DESTINATION_REGISTRY_VERSION, str)
assert s.resolve(N()).id == 'scratchpad.v1'
assert s.resolve(N(SUCCESSOR_QUESTION_DESTINATION='nope')).id == 'scratchpad.v1'
assert len(s.unknown_destination_notices(N(SUCCESSOR_QUESTION_DESTINATION='nope'))) == 1
assert not s.unknown_destination_notices(N())
"` -> exit 0

S6 (R3, R6): `src/deepreason/successor/__init__.py` (new) | before: no such
package | after: the module's declared INTERFACE and nothing else —
`resolve`, `route`, `mint`, `unknown_destination_notices`,
`SUCCESSOR_DESTINATION_REGISTRY_VERSION`. Consumers import the interface; a
consumer reaching past it into a row's internals is what S8's architecture test
goes red on.
    accept: `python -c "import deepreason.successor as s; assert set(s.__all__) == {'resolve','route','mint','unknown_destination_notices','SUCCESSOR_DESTINATION_REGISTRY_VERSION','DESTINATIONS'}, s.__all__"` -> exit 0

S7 (R3, R6, C9): `docs/map/CON-successor-questions.md` (new) + one routing row in
`docs/map/INDEX.md` | before: no map document owns `src/deepreason/successor/`
| after: a concept document on `CON-discharge-channel.md`'s model — what the
channel is, the socket contract (promises / what it is handed / what it must
never do), where it lives, where to change what, and Traps — with an `Owns:`
header naming the new package, and every load-bearing claim carrying a `check:`
at column 0 that can fail.
    accept: `python tools/docs_verify.py --links` -> `0 dangling`
    accept: `python tools/docs_verify.py --audit 2>&1 | grep -c "CON-successor-questions"` -> `0`

S8 (R3, R6, C3): `tests/test_successor_registry.py` (new) | before: nothing
proves the registry is a contract rather than a wiring | after: the
architecture test the modularity law requires — (a) no declaration field is
annotated `int` or `float`, checked over the MODEL; (b) an unknown selector id
falls back and discloses exactly one notice, and never raises; (c) ADDING a
destination row requires no edit to any consumer, proved by registering a
throw-away row in-test and routing to it through the public interface alone;
(d) no consumer branches on a row's `id` — the producer-agnostic rule
(`DR-INV-signal-contract`'s "a consumer that needs to know the producer has left
the contract"), asserted as an absence over `src/deepreason/` with a positive
anchor.
    accept: `python -m pytest tests/test_successor_registry.py -q` -> `0 failed`

### B-iii — the DEFAULT destination: the scratchpad, linked and visible

S9 (R2, C11 — PROVISIONAL ON Q3): `src/deepreason/successor/route.py` (new) |
before: nothing routes a filled question anywhere | after: `route(harness,
config, *, problem_id, question, llm_call)` resolves the destination through
S5's interface and, for the shipped default row, creates ONE scratch block via
`ScratchService.create_block` with body `{content: <question>, unfinished:
"Successor question"}` — the shape `scratch/authoring.py` already uses for an
unresolved question — and `ScratchProvenanceV1(actor="llm", origin=<problem
id>)`, which is where the LINK to the originating problem lives. It records
exactly one typed receipt (S10) per routed question and NOTHING at all when the
field is absent, mirroring the uninvited-dispatch rule
(`DR-CON-criticism-source`). Explicitly NOT done: no field is added to
`ScratchBlockBodyV1` (a body field moved every stored block id — measured
`ff609dcc` -> `248b3201` in-code), and nothing routes through
`ScratchAuthoringService.author_block` (its `block_role` is a closed Literal
that enters the qualification subject's pair inventory — frozen surfaces 4
and 5).
    accept: `python -m pytest tests/test_successor_questions.py -q` -> `0 failed`
    accept: `git diff --stat -- src/deepreason/scratch/models.py src/deepreason/scratch/authoring.py src/deepreason/scratch/events.py` -> empty

S10 (R2, C4): `src/deepreason/signals.py` | before: no successor receipt tag is
declared | after: one declaration per receipt this change emits, each with a
REAL `unit` and a REAL `staleness` from the closed vocabularies —
`unspecified` is unavailable to a new signal (`DR-REC-add-signal`) — and
producer-agnostic `semantics` saying what one occurrence means and what it is
NOT evidence of. `MIGRATION_DEBT` is untouched: this adds signals, it does not
pay debt down.
    accept: `python -m pytest tests/test_signal_contract.py tests/test_signals.py -q` -> `0 failed`

S11 (R2): `tests/test_successor_questions.py` (new) | before: nothing proves the
route | after: an absent field records nothing at all; a filled field creates
exactly one `scratch-block` object whose `provenance.origin` names the
originating problem id and whose `provenance.actor` is `llm`; the resulting
block is SELECTED by `AttentionPlanner.plan` for a conjecturer context under a
permissive policy and appears in the rendered pack's ordered refs — the
VISIBILITY half of R2, measured rather than asserted; and a run whose scratch
policy is DISABLED gets a typed disclosure rather than a silent discard.
    accept: `python -m pytest tests/test_successor_questions.py -q` -> `0 failed`

S12 (C9, C11 — PROVISIONAL ON Q3): `docs/map/SEAM-rules-x-scratch.md` | before:
"An unresolved question is not a problem ... No edge joins the two, and none
should" and rule 6 "Never widen the criticism side to close the asymmetry ...
Overturning it is an operator's call, not an implementer's" | after: both
sentences amended to record that the operator MADE that call on 2026-08-29,
what exactly it permits, and — precisely — what of the asymmetry SURVIVES it
(whatever Q3 answers). The existing `check:` lines that pin `grep -c scratch
src/deepreason/rules/crit.py -eq 2`, `grep -c fence -eq 6`, the `conj.py`-only
scratch import and the exact `render_crit_pack` / `render_batch_crit_pack`
parameter lists STAY GREEN UNCHANGED — this change adds no pack parameter and
no scratch name to `crit.py`. A Traps entry is added; none is deleted.
    accept: `python tools/docs_verify.py 2>&1 | grep -c "FAIL SEAM-rules-x-scratch"` -> `0`
    accept: `test "$(grep -c scratch src/deepreason/rules/crit.py)" -eq 2 && test "$(grep -c fence src/deepreason/rules/crit.py)" -eq 6` -> exit 0
    accept: `python -m pytest tests/test_prose_refutation_boundaries.py -q` -> `0 failed`

### B-iv — the minting road, built and gated

S13 (R4, C13 — PROVISIONAL ON Q3): `src/deepreason/successor/mint.py` (new) |
before: `SpawnTrigger.SUCCESSOR` has zero producers | after: exactly ONE
producer, modelled line for line on `calculus/operations.py::ensure_promotion_problem`
— a deterministic id under the historical `succ:` prefix, an idempotent early
return on `pid in harness.state.problems` (the re-registration trap in
`DR-SEAM-ontology-x-rules`), provenance `{"trigger": SpawnTrigger.SUCCESSOR,
"from": [<problem id>, <criticised target id>]}` built through the on-record
`from` alias, and criteria pinned AT REGISTRATION because `Problem` is
immutable. It lives OUTSIDE `src/deepreason/rules/` and is never called from
`scan_spawns`, which keeps `DR-SEAM-ontology-x-rules`'s two-site
`ProblemProvenance.model_validate` count, `DR-SEAM-rules-x-scratch`'s six-name
`scan_spawns` trigger set, and `tests/test_h1_no_spawn_from_refutation.py`'s
`inspect.getsource(scan_spawns)` assertion all green. `src/deepreason/rules/spawn.py`
takes a ZERO-LINE DIFF.
    accept: `python -c "import inspect; from deepreason.rules.spawn import scan_spawns; assert 'SpawnTrigger.SUCCESSOR' not in inspect.getsource(scan_spawns)"` -> exit 0
    accept: `git diff --stat -- src/deepreason/rules/spawn.py` -> empty
    accept: `python -m pytest tests/test_successor_minting.py -q` -> `0 failed`

S16 (R4, C9): `src/deepreason/ontology/problem.py` | before: the `INERT
VOCABULARY: producers = 0` comment states "its presence asserts no producer and
licenses no new one" | after: that comment is rewritten to state what is now
true — one producer, outside `rules/`, gated by a per-run flag defaulting off,
under the operator's P9 law of 2026-08-29 — and to state what did NOT change
(the website pipeline stays decommissioned; `scan_spawns` still mints nothing
from a refutation). The enum member NAME and VALUE are unchanged: a map check
pins the exact member list.
    accept: `python -c "from deepreason.ontology.problem import SpawnTrigger;n=sorted(t.name for t in SpawnTrigger);assert n==['AUDIT_CRITIC','CONNECTION','DISCRIMINATION','EXPLANATION_DEBT','INTEGRATION','PROMOTION','REMOVE_ARBITRARINESS','RESEARCH','SEED','SUCCESSOR'],n; assert SpawnTrigger.SUCCESSOR.value=='successor'"` -> exit 0
    accept: `git diff -- src/deepreason/ontology/problem.py | grep -c '^-[^-]' ` -> only comment lines removed, zero code lines

S17 (R4, C2, C13): `tests/test_successor_minting.py` (new) | before: nothing
proves the gate | after: with the flag OFF (the default) a filled successor
question mints NOTHING and the problem set is unchanged; with it ON exactly one
problem is minted and minting twice mints once (idempotence); the minted
problem carries `SpawnTrigger.SUCCESSOR` and names both its parents in `from`;
and turning the flag ON produces a TYPED disclosure carrying the operator's own
words "may cause critics to fully consume conjecturer role" — never a refusal
and never silence (C2).
    accept: `python -m pytest tests/test_successor_minting.py -q` -> `0 failed`
    accept: `python -c "
from types import SimpleNamespace as N
import deepreason.successor as s
msgs = [n.message for n in s.minting_notices(N(SUCCESSOR_MINTING_ENABLED=True))]
assert any('may cause critics to fully consume conjecturer role' in m for m in msgs), msgs
assert s.minting_notices(N(SUCCESSOR_MINTING_ENABLED=False)) == ()
"` -> exit 0

S18 (R5, C8): `tests/test_successor_rank_tie.py` (new) | before:
`tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero`
proves the seed wins rank ties against the spawn triggers that existed then |
after: the same proof with a `SpawnTrigger.SUCCESSOR` rival, looping
`for liveness in (True, False)` so BOTH selection modes are covered, asserting
the seed problem is selected first. Mirrored rather than edited, so the existing
regression stays byte-unchanged. The docstring states plainly what this proves
and what it does NOT: the guarantee is over the TIE-BREAK term, and Q4 records
the residue.
    accept: `python -m pytest tests/test_successor_rank_tie.py tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero -q` -> `0 failed`
    accept: `git diff --stat -- src/deepreason/scheduler/scheduler.py` -> empty

S21 (C9, C12): `docs/map/CON-problem-layer-lifecycle.md` | before: invariant H1
reads "Nothing here mints a problem from a conjecture's failure. `translate` is
the only path that mints a problem", and a Traps sentence asserts "`scan_spawns`
mints a SUCCESSOR problem for every REFUTED artifact that addresses a problem" |
after: H1 is amended to say exactly what survives — nothing mints a problem
AUTOMATICALLY FROM A REFUTATION, and `translate` is still the only path that
mints a problem FROM AN ADJUDICATED RESOLUTION — and the new road is named:
a critic's OPTIONAL PROPOSAL, under a per-run flag defaulting off, is a
different road with a different authority. The stale Traps sentence is
CORRECTED (it describes a loop deleted at Rung 3a) rather than deleted, per the
never-delete-a-Traps-entry rule.
    accept: `python tools/docs_verify.py 2>&1 | grep -c "FAIL CON-problem-layer-lifecycle"` -> `0`

S22 (C9): `docs/map/SEAM-ontology-x-rules.md` | before: no Traps entry for the
SUCCESSOR revival; rule 5 says a `SpawnTrigger` needs its consumer in the same
commit | after: a Traps entry naming this tranche, recording that SUCCESSOR
acquired its consumer OUTSIDE `rules/` on purpose and that the two-site
`ProblemProvenance.model_validate` check inside `rules/` is exactly what forces
that. The check itself stays green and unedited.
    accept: `python tools/docs_verify.py 2>&1 | grep -c "FAIL SEAM-ontology-x-rules"` -> `0`

### B-v — the grant-gated switches and the superseded fixtures

S14 (R4, R6, C6 — GRANT-GATED ON Q1): `src/deepreason/config.py` | before: no
successor fields | after: two per-run fields —
`SUCCESSOR_QUESTION_DESTINATION: str = "scratchpad.v1"` (the registry selector)
and `SUCCESSOR_MINTING_ENABLED: bool = False` (the gate), modelled on
`DISCHARGE_POLICY` and `JUDGE_SEATS_ENABLED`. Neither name contains `stance`,
`lineage`, `crossover` or `reseed` (a map check forbids those words in
`run_manifest.py`, which echoes every `Config` field by name).
    accept: `python -c "from deepreason.config import Config; c=Config(); assert c.SUCCESSOR_MINTING_ENABLED is False and c.SUCCESSOR_QUESTION_DESTINATION=='scratchpad.v1'"` -> exit 0
    accept: `sh -c '! grep -qiE "\bstance\b|lineage|crossover|reseed" src/deepreason/run_manifest.py'` -> exit 0

S15 (C6 — GRANT-GATED ON Q1, FROZEN SURFACE 4): `src/deepreason/run_manifest.py`
| before: 25 unconditional four-space `data.pop(...)` lines in
`_versioned_source_config_data` | after: 27. Two INSERTIONS ONLY, at EXACTLY
four-space indent, unconditional. No schema, validator, Pydantic model, check
name or record format is touched. The pop must be unconditional and at that
exact indent because an eight-space guard-scoped pop CONTAINS the four-space
string as a substring and passed a naive check while v6's hash had already
moved (recorded 2026-08-26).
    accept: `python -c "
from deepreason.config import Config
from deepreason.run_manifest import source_config_hash
h=[source_config_hash(Config(), schema_version=v) for v in (1,2,3,4,5,6)]
assert h[0]==h[1]=='6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81', h
assert h[2]==h[3]==h[4]==h[5]=='2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5', h
"` -> exit 0
    accept: `test "$(grep -c '^    data\.pop(' src/deepreason/run_manifest.py)" -eq 27` -> exit 0
    accept: `git diff --numstat -- src/deepreason/run_manifest.py` -> `2	0`
    accept: `python -m pytest tests/test_manifest_config_disclosure.py tests/test_reusable_qualification.py tests/test_allocation_signal_consumption.py -q` -> `0 failed`

S19 (C7, C10 — BUBBLED ON Q5): `tests/test_decommissioned_pipeline_stays_out.py`
| before: `test_no_source_file_produces_a_successor_problem` asserts ZERO
SUCCESSOR producers anywhere under `src/deepreason` outside the enum
declaration | after: the same scan, asserting EXACTLY ONE producer, at the one
path this tranche creates, outside `rules/` and outside `scan_spawns` — a
tighter assertion than "zero" would be if the location were unpinned, and a
strictly stronger one than a deleted test. The docstring states the
supersession in full: the operator's P9 law of 2026-08-29 supersedes the
2026-08-15 decommissioning ruling FOR THE SUCCESSOR TRIGGER ALONE; the website
development pipeline itself stays decommissioned, and the four protected-channel
tests below are byte-unchanged.
    accept: `python -m pytest tests/test_decommissioned_pipeline_stays_out.py -q` -> `5 passed`
    accept: `git diff -- tests/test_decommissioned_pipeline_stays_out.py | grep -c "^[-+].*test_protected"` -> `0`

S20 (C7): `tests/test_h1_no_spawn_from_refutation.py` | before: three
assertions that H1's deleted loop stays deleted, with docstrings that predate
P9 | after: the ASSERTIONS ARE UNCHANGED — every one of them stays green,
because minting is outside `scan_spawns` and the flag defaults off — and the
docstrings record that H1's deletion (automatic minting from every refutation,
inside `scan_spawns`) stands untouched, while P9's road mints from an OPTIONAL
FIELD under a per-run flag, which is a different road with a different
authority.
    accept: `python -m pytest tests/test_h1_no_spawn_from_refutation.py -q` -> `5 passed`
    accept: `git diff -U0 -- tests/test_h1_no_spawn_from_refutation.py | grep -c "^[-+] *assert"` -> `0`

S23 (R5, C8, C9): `docs/map/CON-scheduler-ranking.md` | before: the seed rank-tie
promise and its two-occurrence check | after: one added sentence naming
SUCCESSOR as a trigger that can now be minted mid-run and losing the tie by
construction, with a `check:` pinning it, and one HONEST sentence recording the
residue Q4 parks: the seed term decides TIES, and the age*weight term precedes
it. Existing checks unedited.
    accept: `python tools/docs_verify.py 2>&1 | grep -c "FAIL CON-scheduler-ranking"` -> `0`

S24 (C6, C9 — GRANT-GATED ON Q1): `docs/map/INV-frozen-surfaces.md` | before:
five recorded granted contacts under surface 4 | after: a sixth, in the same
shape — the operator's own words, what moved (two insertions, zero deletions),
what CANNOT move (the two `source_config_hash` literals, the shipped
qualification subject digest), and a re-runnable `check:` PROVEN RED under at
least one mutation (an eight-space guard-scoped pop), with the red capture
committed under the tranche's `proof/`.
    accept: `python tools/docs_verify.py 2>&1 | grep -c "FAIL INV-frozen-surfaces"` -> a count NO GREATER than the count at this tranche's base commit (2 today: the `:181` `transport_failure` census and the `:734` stale digest pin, both pre-existing and both listed in `docs/AUDIT_BASELINES.md`), AND the new grant block's own check is not among the FAIL lines
    accept: `test -s experiments/2026-08-30-change-successor-questions/proof/frozen_grant_check_red.txt` -> exit 0 (the new check, captured RED under an eight-space guard-scoped `data.pop` mutation)

## Assumptions (operator may override)

A1 (R2): "goes to scratchpad" means ONE ordinary scratch BLOCK, created through
`ScratchService.create_block`, carrying the question as its content and
`unfinished: "Successor question"` — the shape `scratch/authoring.py` already
uses for an `unresolved_questions` draft. Smallest available: it reuses a
shipped record shape rather than inventing a parallel one, and it touches no
model whose bytes are addressed.

A2 (R2): "linked to the problem it was proposed under" means
`ScratchProvenanceV1.origin` carries the originating problem id.
`origin` is a free 1..512-character string, is documented as "Intellectual
origin only; never a warrant or routing instruction", and is NOT part of
`body_hash` — so the link costs no stored block id. The alternative,
`ScratchQuestionDraftV1.related_refs`, CANNOT carry it: a validator restricts it
to `SCR_`/`NEW_` scratch aliases.

A3 (R2): "the problem it was proposed under" is `_target_problem`'s answer — the
FIRST problem the criticised target is addressed to, in `addr` order, which is
the same one the criticism pack leads with. Any other choice would show the
critic one frame and file the question under another.

A4 (R3): the destination selector's shipped default row id is `scratchpad.v1`.
A version suffix, because `DR-INV-signal-contract` puts the registry in the
VERSIONED layer.

A5 (R4): "a per-run flag" is a `Config` field, not a manifest field. This is the
codebase's own recorded rule — `DR-INV-frozen-surfaces`, "Where authority is
allowed to live instead": put a new per-run mode on `Config`, never on the
manifest.

A6 (R4): the mint's problem id keeps the historical `succ:` prefix. A committed
root (`run-f4fa6663`) already carries `succ:` problem ids and a map check
asserts that prefix set, so reusing it keeps one spelling for one idea. A
trigger's `.value` is never a problem id, so this moves nothing.

A7 (R5): "never outrank" is read, for what this tranche BUILDS, as the rank-TIE
guarantee that `Scheduler._select_problem` already holds. Q4 asks whether the
operator meant strict domination; nothing here forecloses that answer.

A8 (R1): the criticism pack is NOT told the field exists by a new pack
parameter. `docs/map/SEAM-rules-x-scratch.md` pins the exact parameter lists of
`render_crit_pack` and `render_batch_crit_pack`, and widening either would
re-open the whole "criticism is given no scratch content" guarantee. The field
is always available on the contract with a schema description instead — which
is also what "not enforceable" asks for: no invitation to decline.

## Questions for operator (STOP if non-empty)

Five, and this section being non-empty is itself the STOP: `dr-plan-steps` does
not run until they are answered. Q1 blocks S14/S15/S24. Q3 makes S9/S13
provisional. Q5 blocks S19. Q2 and Q4 change what is built, not whether.

### Q1 — Frozen surface 4: two `data.pop` lines. REQUESTED, not assumed.

S14 adds two `Config` fields. `docs/map/INV-frozen-surfaces.md` states that a
`Config` field is not done without an unconditional `data.pop` line in
`run_manifest.py::_versioned_source_config_data`, because `Config` is serialized
into every manifest's `engine_config_json` and hashed into `source_config_hash`,
both of which the qualification subject embeds. `run_manifest.py` is frozen
surface 4.

`tools/blast_radius.py`'s own verdict and contact rows are pasted verbatim in
the next section and disposed there, one row at a time. Standing precedent — the
operator's 2026-08-26 words, "This is not an exception to the frozen surface —
it is the documented recipe (a Config field is not done WITHOUT that line)" — is
why this contact is FORECAST rather than surprising. It is not the grant. Every
one of the prior contacts was still requested in a SPEC.md before code, and the
operator has refused verbal grants ("Don't grant it verbally in chat").

**What is requested:** two insertions, zero deletions, at exactly four-space
indent, in `_versioned_source_config_data` only. Nothing else in the file.

**What it buys:** the two literal `source_config_hash` values stay byte-identical
at every schema version, every frozen manifest golden stays put, and no
qualification battery is owed (~14 minutes per home).

**What happens without it:** measured 2026-08-22 — the committed fixture's
subject digest moves from `b9038b84efdea313…` to `a5d81e5d34f51635…` and the
full gate goes red in ~40 places. So the alternative is not "skip the line", it
is "do not add the `Config` fields", which costs R4's per-run switch and R6's
configurable surface entirely.

### Q2 — Where the enablement warning is EMITTED. Two roads, both priced.

R4 requires that turning the minting flag on emit the operator's own words, "may
cause critics to fully consume conjecturer role", as a typed disclosure.

**Road A — the compile-notice stream (a SECOND frozen-surface-4 edit).** The
shipped emitter `_emit_uncarried_config_notices` already produces one typed
`ENGINE_CONFIG_FIELD_NOT_CARRIED` notice per dropped field whose configured
value differs from its default — so with Q1 granted, turning the flag on ALREADY
emits a typed notice, automatically, with no extra work. Appending the
operator's warning words to that notice's message requires a row in
`_CARRIAGE_REQUALIFIES`, a `dict[str, str]` literal that lives INSIDE
`run_manifest.py`. Cost: one more line inside frozen surface 4, i.e. a second
granted contact. Benefit: the words appear on the stream `deepreason config
compile` and preflight already print to stderr, so an operator sees them without
looking anywhere new. Reusing the existing notice CODE is mandatory on this
road — it is the exact key `qualification.py` strips before digesting, so any
NEW code would move the manifest sha and the subject digest.

**Road B — the registry declares it, and the record carries it (ZERO extra
frozen contact).** The warning text becomes a field on the gate's registry
declaration (S5), `successor.minting_notices(config)` returns it as a typed
`CompileNoticeV1` when the flag is on, and the mint path records it on the
RECORD as a typed receipt the first time the gate is consulted. Cost: the
notice function has no production caller inside `src/` — measured, and it is
exactly the shipped situation for `channels.unknown_channel_notices`, which
also has none — so the compile-time words are reachable and tested but not
printed by today's CLI. Benefit: no second frozen contact, and the words land
on the append-only record, which is the only admissible evidence about what a
run did.

**Recommendation: Road B, plus Road A if and only if Q1's grant is widened to
cover the one extra line.** Road B satisfies "never silence" on the record,
which is the durable half. Road A adds operator-visible stderr text for one more
line inside a frozen file, and that is the operator's call to price, not mine.

### Q3 — REAL DESIGN FORK: may the criticism dispatch WRITE to the workshop?

Two standing written positions, neither a defect, both older than the P9 law:

- `docs/map/CON-problem-layer-lifecycle.md`, invariant H1: "Nothing here mints a
  problem from a conjecture's failure. `translate` is the only path that mints a
  problem, and it fires from an adjudicated resolution, not from a refutation."
- `docs/map/SEAM-rules-x-scratch.md`: "An unresolved question is not a problem
  ... No edge joins the two, and none should." and, in How to change it, rule 6:
  "Never widen the criticism side to close the asymmetry. The asymmetry is the
  design. Overturning it is an operator's call, not an implementer's."

The P9 law IS that operator call and IS later than both documents. What it does
NOT settle is which guarantee survives it.

**Road A — criticism dispatches the route directly.** A `_file_successor_question`
helper beside `_file_attribution` in `rules/crit.py`, called from
`crit_argumentative` and from the batch path, importing `deepreason.successor`
LATE (inside the function body, exactly as `_file_attribution` imports
`premises`). This passes every mechanical check on the tree: the AST-walk tests
scan `crit.py`'s own imports for `deepreason.scratch` and find none; the
`grep -c scratch` count stays 2; the pinned pack signatures are untouched. It is
also the shipped precedent's exact shape. **But it is a workaround of the
letter of rule 6 while the SEAM's own prose says the SPIRIT is the operator's
call** — the criticism side would be writing into the workshop through a
module with a neutral name.

**Road B — a non-criticism intermediary READS what the criticism recorded.**
`rules/crit.py` takes a ZERO-LINE DIFF. The successor question reaches the
record anyway, because it is a wire field and the raw completion is already
persisted as a blob (`LLMCall.raw_ref`); a reader outside `rules/` walks critic
calls and routes what it finds — the exact shape `DR-CON-discharge-channel`
uses ("the channel is a READER of what `_observe_case` already records").
Cost: the reader must re-resolve the batch path's `target_alias` values and
recompute the originating problem from `addr`, which the criticism call already
had in hand; it is more code and more ways to be wrong. Benefit: the asymmetry
survives intact — criticism writes only its own record, and something that is
not criticism does the routing.

**Note on this lane's granted cone:** it grants `rules/crit.py` OUTPUT SCHEMA
ONLY, which reads as Road B. Road A needs that cone widened by two call sites.

**Recommendation: Road B if the asymmetry is to survive as written; Road A only
with an explicit sentence saying rule 6 is overturned for this channel.** Either
way the SEAM document must be amended in the same commit (S12) — what it says
today will be false under both roads.

Anything built before this is answered is PROVISIONAL on it, and S9/S13 are
marked so in the Items list.

### Q4 — How strong is "never outrank the seed"?

`Scheduler._select_problem` ranks under two keys. In both, the seed term is
`p.provenance.trigger != SpawnTrigger.SEED`, which is `False` for the seed and
`True` for a successor, and `False` sorts before `True` — so a minted successor
can NEVER win a TIE against the seed, by construction, with no new code. That
half is provable today and S18 proves it.

The residue: in the `LIVENESS_QUEUE` key the FIRST term is `-(age * weight)`,
and the seed term is second. A freshly minted successor has never been worked,
so its age is maximal; it can therefore outrank a seed that HAS been worked.
The only mitigation on the tree is the wander cap, which is a CANDIDACY gate
under `SEED_PROBLEM_BUDGET_FLOOR`, not a rank term.

**Reading 1 (tie guarantee): free, already true, proved by S18.** **Reading 2
(strict domination): a change to the rank key**, a socket whose promise is
pinned by two map checks and by
`tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero`
— a separate tranche, not this one. Recommendation: take reading 1 here and
park reading 2 as its own tranche if the operator wants it; changing a
scheduler socket to close a risk that no run has yet exhibited would be
speculative work against a pinned promise.

### Q5 — Confirm the scope of the superseded 2026-08-15 ruling.

`tests/test_decommissioned_pipeline_stays_out.py::test_no_source_file_produces_a_successor_problem`
is a deliberate tripwire. Its docstring: "THE load-bearing invariant: producers
= 0. The pipeline stays decommissioned because nothing mints a successor
problem, not because the vocabulary lost a word. If a producer comes back, this
fails -- which is the alarm that matters." Its module docstring quotes the
operator's 2026-08-15 ruling verbatim: "There was a website development pipeline
that I decommissioned a while ago. That needs to stay decommissioned."

S13 trips it ON PURPOSE. Gate discipline permits the update only because this
document PREDICTS it before the code exists (see Predicted fixture changes
below).

**The supersession statement, for confirmation:** the operator's P9 law of
2026-08-29 supersedes the 2026-08-15 decommissioning ruling FOR THE SUCCESSOR
TRIGGER ALONE — one producer, outside `rules/`, gated by a per-run flag that
defaults OFF — while the WEBSITE DEVELOPMENT PIPELINE ITSELF STAYS
DECOMMISSIONED and the four protected-channel tests in the same file stay
byte-unchanged. An implementer may not decide the scope of a superseded
operator ruling, so this sentence is bubbled rather than acted on.

## Out of scope (explicit)

- **Changing `Scheduler._select_problem`'s rank key.** Not requested; Q4 parks
  it. `src/deepreason/scheduler/scheduler.py` takes a zero-line diff.
- **Any change to `rules/spawn.py` or to `scan_spawns`.** Not requested. H1's
  deletion stays deleted; the file takes a zero-line diff.
- **Restoring `easy.py::seed_component`'s staged-pipeline repair branch.** Not
  requested, and Q5's supersession is explicitly narrower than it.
- **Adding a pack parameter so the critic is INVITED to fill the field.** Not
  requested, and "not enforceable" reads against it. The premise channel's
  invitation is the tempting neighbour; it is declined here because the pinned
  pack signatures make it a seam change and because an invitation implies a
  decline receipt the operator did not ask for.
- **A new `SpawnTrigger` member.** Not requested; SUCCESSOR already exists, so
  this is a revival, and a map check pins the exact member list.
- **Widening `ScratchPolicy.block_role` to admit a critic role.** Not requested.
  It is a closed Literal that enters the qualification subject's pair inventory
  — frozen surfaces 4 and 5, and a ~14-minute battery per home.
- **Adding any field to `ScratchBlockBodyV1`.** Not requested, and measured
  in-code to move every stored block id.
- **Judges, criticism authority, or anything that decides a STATUS.** Not
  requested; a successor question decides nothing.
- **A live run.** Not requested at this phase, and nothing here needs one: every
  acceptance check above is offline and deterministic.

## Declared write cone, path by path

Exactly these paths, and nothing else. Checked against
`docs/map/INV-frozen-surfaces.md`'s five surfaces / seven paths.

| path | new? | why | frozen? |
|---|---|---|---|
| `src/deepreason/llm/contracts.py` | no | S1 — the two optional contract fields | no |
| `src/deepreason/llm/wire.py` | no | S2 — the two wire mirrors and both `compile()` maps | no |
| `src/deepreason/successor/__init__.py` | YES | S6 — the declared interface | no |
| `src/deepreason/successor/registry.py` | YES | S5 — the versioned destination registry | no |
| `src/deepreason/successor/route.py` | YES | S9 — the default scratchpad destination | no |
| `src/deepreason/successor/mint.py` | YES | S13 — the one SUCCESSOR producer | no |
| `src/deepreason/signals.py` | no | S10 — the receipt declarations | no |
| `src/deepreason/ontology/problem.py` | no | S16 — the INERT VOCABULARY comment only; enum member and value unchanged | no |
| `src/deepreason/config.py` | no | S14 — two per-run fields | no (owned by `DR-CON-authority`) |
| `src/deepreason/run_manifest.py` | no | S15 — two `data.pop` lines, insertions only | **YES — surface 4, grant REQUESTED in Q1** |
| `tests/test_successor_law_line.py` | YES | S3 | n/a |
| `tests/test_successor_registry.py` | YES | S8 | n/a |
| `tests/test_successor_questions.py` | YES | S11 | n/a |
| `tests/test_successor_minting.py` | YES | S17 | n/a |
| `tests/test_successor_rank_tie.py` | YES | S18 | n/a |
| `tests/test_decommissioned_pipeline_stays_out.py` | no | S19 — one test + docstrings | n/a |
| `tests/test_h1_no_spawn_from_refutation.py` | no | S20 — docstrings only, zero assertion changes | n/a |
| `docs/map/CON-successor-questions.md` | YES | S7 | n/a |
| `docs/map/INDEX.md` | no | S7 — one routing row | n/a |
| `docs/map/CON-criticism-source.md` | no | S4 | n/a |
| `docs/map/SEAM-rules-x-scratch.md` | no | S12 | n/a |
| `docs/map/CON-problem-layer-lifecycle.md` | no | S21 | n/a |
| `docs/map/SEAM-ontology-x-rules.md` | no | S22 | n/a |
| `docs/map/CON-scheduler-ranking.md` | no | S23 | n/a |
| `docs/map/INV-frozen-surfaces.md` | no | S24 — the grant record | n/a (the document, not the surface) |
| `experiments/2026-08-30-change-successor-questions/**` | YES | the tranche's own artifacts and `proof/` captures | n/a |

**Explicitly NOT in the cone, and each is a path a careless implementation would
reach for:** `src/deepreason/rules/crit.py` (Q3 Road A would need two call sites
here; the granted cone says OUTPUT SCHEMA ONLY, so nothing is written there
until Q3 is answered), `src/deepreason/rules/spawn.py`,
`src/deepreason/scheduler/scheduler.py`, `src/deepreason/scratch/models.py`,
`src/deepreason/scratch/authoring.py`, `src/deepreason/scratch/events.py`,
`src/deepreason/llm/packs.py`, `src/deepreason/qualification.py`,
`src/deepreason/harness.py`, `src/deepreason/invariants.py`,
`src/deepreason/verification/`, `src/deepreason/capabilities/state.py`,
`src/deepreason/llm/firewall.py`, `src/deepreason/easy.py`,
`tests/test_controller.py`.

## Predicted fixture changes (recorded BEFORE the edit)

Gate discipline (C7) permits a fixture update only when the design document
predicted it. These are the predictions, made here, before any code exists.

**P-FIX-1 — `tests/test_decommissioned_pipeline_stays_out.py::test_no_source_file_produces_a_successor_problem`
WILL go red, and is rewritten (S19).** It scans every `.py` under
`src/deepreason` for four literal spellings of a SUCCESSOR producer and asserts
zero hits outside `ontology/problem.py`. S13 creates exactly one. *Why the
update is legitimate:* the assertion encoded an operator ruling of 2026-08-15;
the operator issued a later law on 2026-08-29 that requires exactly one gated
producer. The rewrite does not WEAKEN the assertion — it changes it from
"exactly zero producers" to "exactly one producer, at this path, outside
`rules/`, outside `scan_spawns`", which is a strictly more specific claim and
still fails the moment a second producer appears anywhere. *Bubbled:* the scope
of the supersession is Q5, and this edit does not land until Q5 is answered.

**P-FIX-2 — `tests/test_h1_no_spawn_from_refutation.py`: docstrings only, and
this is a PREDICTION that its assertions will NOT move (S20).** Three of its
assertions are load-bearing against H1's deleted loop:
`'SpawnTrigger.SUCCESSOR' not in inspect.getsource(scan_spawns)`, SUCCESSOR
absent from the triggers `scan_spawns(harness, Config())` produces, and a
refutation followed by `scan_spawns` leaving the problem set unchanged. All
three stay GREEN if and only if the mint site is outside `scan_spawns` AND the
flag defaults off. If any of them goes red, the design is wrong and the item is
a STOP, not a fixture update. The accept command for S20 asserts zero changed
assertion lines.

**P-FIX-3 — `tests/test_decommissioned_pipeline_stays_out.py::test_the_successor_trigger_is_inert_vocabulary`:
PREDICTED to stay green with no edit.** It asserts only
`hasattr(SpawnTrigger, "SUCCESSOR")`. Its name will be misleading after this
tranche; renaming it is deferred to S19's docstring rather than done, because a
renamed test loses its own history.

**P-FIX-4 — no other fixture is predicted to change.** In particular
`tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero`
is MIRRORED by S18, never edited; the two `source_config_hash` literals and the
shipped qualification subject digest are pinned to stay byte-identical (S15);
and `tests/test_reference_menu.py::test_wire_schema_sha_does_not_move` compares
bare-vs-informed schemas of the same code rather than a literal sha, so an
optional wire field does not move it. Any OTHER fixture that goes red is
undeclared drift and a STOP.

## Frozen-surface contact forecast

**VERDICT: CONTACT.** One of the five frozen surfaces — surface 4, manifest
schemas and their validators (`run_manifest.py`). This section is the written
REQUEST for that contact, made before a line of code exists, per the discipline
`docs/map/INV-frozen-surfaces.md` records for every prior grant. It is NOT a
grant. Standing precedent is not a grant either.

Command run, verbatim:

    python tools/blast_radius.py \
      --files src/deepreason/run_manifest.py src/deepreason/config.py \
              src/deepreason/llm/contracts.py src/deepreason/llm/wire.py \
              src/deepreason/rules/crit.py src/deepreason/ontology/problem.py \
              src/deepreason/signals.py \
      --symbols _versioned_source_config_data ArgumentativeCriticOutput \
                BatchCase CompactCritic BatchCriticCaseWireV2 SpawnTrigger

Full output committed verbatim at
`experiments/2026-08-30-change-successor-questions/blast_radius.json`. The
load-bearing sections, pasted rather than summarised:

    frozen_surface_verdict: CONTACT

    frozen_surface_contacts:
    [
      {
        "surface": "manifest schemas and validators (run_manifest.py)",
        "tier": "DIRECT",
        "target": "src/deepreason/run_manifest.py",
        "detail": "target file is surface path src/deepreason/run_manifest.py"
      },
      {
        "surface": "manifest schemas and validators (run_manifest.py)",
        "tier": "SYMBOL_INDIRECT",
        "target": "_versioned_source_config_data",
        "detail": "'_versioned_source_config_data' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"
      }
    ]

    frozen_adjacent_contacts:
    []

    consumers.qualification_digest:
    [
      {
        "target": "src/deepreason/run_manifest.py",
        "tier": "CONFIRMED",
        "detail": "target file is part of the manifest/qualification surface itself"
      },
      {
        "target": "_versioned_source_config_data",
        "tier": "PLAUSIBLE",
        "detail": "referenced in src/deepreason/run_manifest.py"
      }
    ]

    consumers.wheel_smoke_pins:
    [
      {
        "target": "BatchCriticCaseWireV2",
        "tier": "PLAUSIBLE",
        "pin": "scripts/wheel_operational_smoke.py"
      }
    ]

    reachability:
    [
      {
        "symbol": "_versioned_source_config_data",
        "status_current": "REACHABLE",
        "status_base": null,
        "direction": null
      },
      {
        "symbol": "ArgumentativeCriticOutput",
        "status_current": "UNKNOWN",
        "status_base": null,
        "direction": null
      },
      {
        "symbol": "BatchCase",
        "status_current": "UNKNOWN",
        "status_base": null,
        "direction": null
      },
      {
        "symbol": "CompactCritic",
        "status_current": "UNKNOWN",
        "status_base": null,
        "direction": null
      },
      {
        "symbol": "BatchCriticCaseWireV2",
        "status_current": "UNKNOWN",
        "status_base": null,
        "direction": null
      },
      {
        "symbol": "SpawnTrigger",
        "status_current": "UNKNOWN",
        "status_base": null,
        "direction": null
      }
    ]

    disclosure_summary:
    This change touches 1 of the five frozen surfaces (locked-down files that a change can silently corrupt old, already-recorded runs by touching): manifest schemas and validators (run_manifest.py). 9 test file(s) and 11 map document(s) assert on the touched targets today. Reachability here means a syntactic call path exists from a known entry point; it does not prove the path is ever actually exercised at runtime -- a symbol can be syntactically reachable and still never fire because of a runtime precondition this gate does not evaluate.

### Disposition, one contact row at a time

**Row 1 — `frozen_surface_contacts[0]`: surface "manifest schemas and validators
(run_manifest.py)", tier DIRECT, target `src/deepreason/run_manifest.py`.**
REAL. This is S15 and nothing else. The planned edit is two UNCONDITIONAL
`data.pop("<FIELD>", None)` lines at exactly four-space indent inside
`_versioned_source_config_data`, joining the 25 already there (measured today:
`grep -c '^    data\.pop(' src/deepreason/run_manifest.py` -> `25`). No schema,
no validator, no Pydantic model, no check name, no record format is touched;
`git diff --numstat` must read `2	0`. **REQUESTED under Q1. Blocked until
answered.** If the answer is no, S14/S15/S24 are dropped and R4's per-run switch
and R6's configurable surface are delivered as parked, not as done.

**Row 2 — `frozen_surface_contacts[1]`: surface "manifest schemas and validators
(run_manifest.py)", tier SYMBOL_INDIRECT, target `_versioned_source_config_data`,
detail "grep-based; not proof of semantic contact".** REAL, and it is the same
contact as row 1 seen from the symbol side — the function whose body receives the
two lines. Disposed together with row 1; no separate grant is requested and none
is implied.

**`frozen_adjacent_contacts`: EMPTY.** Confirmed by reading, not only by the
tool: `route_fingerprint` in `src/deepreason/llm/firewall.py` is the
frozen-adjacent symbol, and no item in this spec names that file. It is listed
in the declared cone's NOT-in-cone list.

**`consumers.qualification_digest[0]`: `src/deepreason/run_manifest.py`, tier
CONFIRMED.** Expected, and it is precisely what the two `data.pop` lines exist
to neutralise: with them, `source_config_hash` is byte-identical at every schema
version (S15's first accept command pins both literals) and the qualification
subject cannot move. WITHOUT them the digest moves and ~40 tests go red —
measured 2026-08-22. MUST NOT MOVE.

**`consumers.qualification_digest[1]`: `_versioned_source_config_data`, tier
PLAUSIBLE.** Same contact, symbol side. MUST NOT MOVE.

**`consumers.wheel_smoke_pins[0]`: `BatchCriticCaseWireV2`, tier PLAUSIBLE, pin
`scripts/wheel_operational_smoke.py`.** Disposed: the wheel smokes pin console
entry points, the MCP tool set and its schema sha, and the wheel layout. S2 adds
one OPTIONAL field to a criticism wire model, which is not a console entry
point, not an MCP tool, and not a layout change. Nonetheless, because no gate
runs the smokes, `python scripts/wheel_smoke.py` and `python -u
scripts/wheel_operational_smoke.py` WILL be run once at this tranche's
validation phase and their output pasted into VALIDATION.md — either as "surface
untouched" or, if a pin does move, as a pin updated in the same commit. Recorded
here so it cannot be forgotten.

**`reachability`: `_versioned_source_config_data` REACHABLE; the five wire and
enum symbols UNKNOWN.** The five UNKNOWNs are the tool declining to resolve
Pydantic model classes through the dynamic contract registry, not a claim that
they are dead — every one of them has committed test consumers listed in the
census below. No `newly_dead`/`newly_live` direction is predicted for any
symbol by this change: nothing is deleted and nothing previously unreachable
becomes reachable except `SpawnTrigger.SUCCESSOR`'s producer, which is the
change. **PREDICTED: `SpawnTrigger` may report a reachability direction change
at S13's commit. That is declared here so it is not read as drift.**

## Blast-radius census

`tools/blast_radius.py` reported 9 test files and 11 map documents asserting on
the touched targets. Every hit it computed is listed below, none omitted, after
the per-target verdict table. "no hits" would have been a valid census; this is
not that case.

### Per-target verdict

| target | verdict | why |
|---|---|---|
| `src/deepreason/run_manifest.py` | **MUST NOT MOVE** (behaviour); 2 inserted lines (text) | S15 adds two drop lines and nothing else; both `source_config_hash` literals and the qualification subject digest stay byte-identical |
| `_versioned_source_config_data` | **MUST NOT MOVE** (behaviour) | same contact, symbol side |
| `src/deepreason/config.py` | EXPECTED TO MOVE | S14 adds two fields; no existing field changes |
| `src/deepreason/llm/contracts.py` | EXPECTED TO MOVE | S1 adds one optional field to two models |
| `ArgumentativeCriticOutput`, `BatchCase` | EXPECTED TO MOVE | S1. Existing fields, defaults and `exclude_none` bytes unchanged |
| `src/deepreason/llm/wire.py` | EXPECTED TO MOVE | S2 adds one optional field to two wire models and threads both `compile()` maps |
| `CompactCritic`, `BatchCriticCaseWireV2` | EXPECTED TO MOVE | S2 |
| `src/deepreason/rules/crit.py` | **MUST NOT MOVE** under the granted cone | Q3 Road A would touch it; until Q3 is answered it takes a zero-line diff. Its two pinned counts (`scratch` = 2, `fence` = 6) are accept commands on S12 |
| `src/deepreason/ontology/problem.py` | EXPECTED TO MOVE (comment only) | S16. The enum member list and `SUCCESSOR`'s value are pinned by a map check and do not move |
| `SpawnTrigger` | **MUST NOT MOVE** (members/values); reachability direction MAY change | S13 gives SUCCESSOR its first producer; the member list check stays green |
| `src/deepreason/signals.py` | EXPECTED TO MOVE | S10 adds declarations; `MIGRATION_DEBT` untouched |

### Test consumers — every hit, none omitted

`src/deepreason/run_manifest.py` — 2 hit(s):

- `tests/test_decommissioned_pipeline_stays_out.py:116`
- `tests/test_manifest_config_disclosure.py:196`

`src/deepreason/llm/contracts.py` — 1 hit(s):

- `tests/test_discharge_contract.py:144`

`src/deepreason/rules/crit.py` — 1 hit(s):

- `tests/test_frame_render.py:583`

`src/deepreason/signals.py` — 1 hit(s):

- `tests/test_signals.py:52`

`_versioned_source_config_data` — 4 hit(s):

- `tests/test_manifest_config_disclosure.py:29`
- `tests/test_manifest_config_disclosure.py:197`
- `tests/test_manifest_config_disclosure.py:209`
- `tests/test_reusable_qualification.py:271`

`ArgumentativeCriticOutput` — 10 hit(s):

- `tests/test_compact_profiles.py:10`
- `tests/test_compact_profiles.py:121`
- `tests/test_crit_batch.py:128`
- `tests/test_p4_citable_evidence.py:506`
- `tests/test_p4_citable_evidence.py:514`
- `tests/test_reference_menu.py:948`
- `tests/test_wire_contracts.py:8`
- `tests/test_wire_contracts.py:77`
- `tests/test_wire_contracts.py:122`
- `tests/test_wire_contracts.py:146`

`BatchCase` — 2 hit(s):

- `tests/test_p4_citable_evidence.py:507`
- `tests/test_p4_citable_evidence.py:517`

`BatchCriticCaseWireV2` — 1 hit(s):

- `tests/test_v6_patch_repair_and_wire.py:526`

`SpawnTrigger` — 54 hit(s):

- `tests/test_amendment_epochs.py:56`
- `tests/test_amendment_epochs.py:259`
- `tests/test_calculus_axioms_rung7.py:182`
- `tests/test_calculus_axioms_rung7.py:183`
- `tests/test_calculus_axioms_rung7.py:185`
- `tests/test_calculus_frame_assertions.py:271`
- `tests/test_calculus_frame_assertions.py:277`
- `tests/test_calculus_nomination.py:28`
- `tests/test_calculus_nomination.py:33`
- `tests/test_calculus_nomination.py:82`
- `tests/test_calculus_nomination.py:100`
- `tests/test_calculus_nomination.py:123`
- `tests/test_calculus_nomination.py:128`
- `tests/test_calculus_nomination.py:138`
- `tests/test_calculus_nomination.py:140`
- `tests/test_calculus_nomination.py:197`
- `tests/test_calculus_scope_predicate.py:19`
- `tests/test_calculus_scope_predicate.py:23`
- `tests/test_calculus_standing.py:31`
- `tests/test_calculus_standing.py:257`
- `tests/test_calculus_standing.py:262`
- `tests/test_calculus_standing.py:621`
- `tests/test_calculus_standing.py:662`
- `tests/test_calculus_succession.py:39`
- `tests/test_calculus_succession.py:102`
- `tests/test_calculus_succession.py:151`
- `tests/test_calculus_succession.py:171`
- `tests/test_calculus_succession_trial.py:41`
- `tests/test_calculus_succession_trial.py:85`
- `tests/test_decommissioned_pipeline_stays_out.py:17`
- `tests/test_decommissioned_pipeline_stays_out.py:31`
- `tests/test_decommissioned_pipeline_stays_out.py:50`
- `tests/test_h1_no_spawn_from_refutation.py:22`
- `tests/test_h1_no_spawn_from_refutation.py:88`
- `tests/test_h1_no_spawn_from_refutation.py:121`
- `tests/test_h1_no_spawn_from_refutation.py:125`
- `tests/test_h1_no_spawn_from_refutation.py:142`
- `tests/test_h1_no_spawn_from_refutation.py:144`
- `tests/test_h1_no_spawn_from_refutation.py:148`
- `tests/test_ontology.py:13`
- `tests/test_ontology.py:54`
- `tests/test_ontology.py:57`
- `tests/test_promotion_closure.py:36`
- `tests/test_promotion_closure.py:43`
- `tests/test_promotion_criteria.py:29`
- `tests/test_promotion_criteria.py:38`
- `tests/test_promotion_rent.py:36`
- `tests/test_promotion_rent.py:44`
- `tests/test_promotion_solo.py:34`
- `tests/test_promotion_solo.py:88`
- `tests/test_promotion_solo.py:94`
- `tests/test_promotion_solo.py:106`
- `tests/test_scheduler_promotion_rank.py:29`
- `tests/test_scheduler_promotion_rank.py:157`

### Map-check consumers — every hit, none omitted

`src/deepreason/run_manifest.py` — 63 hit(s):

- `docs/map/CON-authority.md:4`
- `docs/map/CON-authority.md:56`
- `docs/map/CON-authority.md:94`
- `docs/map/CON-authority.md:95`
- `docs/map/CON-authority.md:98`
- `docs/map/CON-authority.md:144`
- `docs/map/CON-conjecture-kinds.md:154`
- `docs/map/CON-conjecture-kinds.md:260`
- `docs/map/CON-packs-and-token-economy.md:57`
- `docs/map/CON-packs-and-token-economy.md:262`
- `docs/map/CON-run-identity.md:125`
- `docs/map/CON-schools.md:4`
- `docs/map/CON-schools.md:49`
- `docs/map/CON-schools.md:146`
- `docs/map/CON-schools.md:156`
- `docs/map/CON-seats.md:207`
- `docs/map/INV-frozen-surfaces.md:4`
- `docs/map/INV-frozen-surfaces.md:153`
- `docs/map/INV-frozen-surfaces.md:309`
- `docs/map/INV-frozen-surfaces.md:347`
- `docs/map/INV-frozen-surfaces.md:384`
- `docs/map/INV-frozen-surfaces.md:397`
- `docs/map/INV-frozen-surfaces.md:419`
- `docs/map/INV-frozen-surfaces.md:641`
- `docs/map/INV-frozen-surfaces.md:659`
- `docs/map/INV-frozen-surfaces.md:673`
- `docs/map/INV-frozen-surfaces.md:880`
- `docs/map/SEAM-bridge-x-llm.md:240`
- `docs/map/SEAM-bridge-x-llm.md:252`
- `docs/map/SEAM-bridge-x-manifest.md:4`
- `docs/map/SEAM-bridge-x-manifest.md:41`
- `docs/map/SEAM-bridge-x-manifest.md:75`
- `docs/map/SEAM-bridge-x-manifest.md:85`
- `docs/map/SEAM-bridge-x-manifest.md:89`
- `docs/map/SEAM-bridge-x-manifest.md:131`
- `docs/map/SEAM-bridge-x-manifest.md:144`
- `docs/map/SEAM-bridge-x-manifest.md:152`
- `docs/map/SEAM-llm-x-manifest.md:4`
- `docs/map/SEAM-llm-x-manifest.md:44`
- `docs/map/SEAM-llm-x-manifest.md:141`
- `docs/map/SEAM-llm-x-manifest.md:174`
- `docs/map/SEAM-llm-x-manifest.md:327`
- `docs/map/SEAM-llm-x-workflow.md:71`
- `docs/map/SEAM-manifest-x-schools.md:4`
- `docs/map/SEAM-manifest-x-schools.md:93`
- `docs/map/SEAM-manifest-x-schools.md:187`
- `docs/map/SEAM-manifest-x-schools.md:206`
- `docs/map/SEAM-manifest-x-schools.md:215`
- `docs/map/SEAM-manifest-x-schools.md:226`
- `docs/map/SEAM-manifest-x-schools.md:236`
- `docs/map/SEAM-manifest-x-schools.md:254`
- `docs/map/SEAM-rules-x-workflow.md:363`
- `docs/map/SUB-manifest.md:4`
- `docs/map/SUB-manifest.md:25`
- `docs/map/SUB-manifest.md:83`
- `docs/map/SUB-manifest.md:155`
- `docs/map/SUB-manifest.md:175`
- `docs/map/SUB-manifest.md:202`
- `docs/map/SUB-manifest.md:300`
- `docs/map/SUB-manifest.md:316`
- `docs/map/SUB-manifest.md:321`
- `docs/map/SUB-scheduler.md:168`
- `docs/map/SUB-scratch.md:68`

`src/deepreason/config.py` — 13 hit(s):

- `docs/map/CON-authority.md:4`
- `docs/map/CON-authority.md:72`
- `docs/map/CON-authority.md:81`
- `docs/map/CON-authority.md:82`
- `docs/map/CON-authority.md:84`
- `docs/map/CON-authority.md:85`
- `docs/map/CON-packs-and-token-economy.md:53`
- `docs/map/INV-frozen-surfaces.md:640`
- `docs/map/SEAM-manifest-x-schools.md:215`
- `docs/map/SUB-evaluation.md:184`
- `docs/map/SUB-evaluation.md:185`
- `docs/map/SUB-periphery.md:276`
- `docs/map/SUB-scheduler.md:168`

`src/deepreason/llm/contracts.py` — 2 hit(s):

- `docs/map/CON-conjecture-kinds.md:4`
- `docs/map/SEAM-llm-x-rules.md:4`

`src/deepreason/llm/wire.py` — 12 hit(s):

- `docs/map/CON-capability-lifecycle.md:49`
- `docs/map/CON-discharge-channel.md:69`
- `docs/map/SEAM-llm-x-rules.md:4`
- `docs/map/SEAM-llm-x-rules.md:100`
- `docs/map/SEAM-llm-x-rules.md:147`
- `docs/map/SEAM-llm-x-rules.md:152`
- `docs/map/SEAM-rules-x-scratch.md:165`
- `docs/map/SUB-llm.md:102`
- `docs/map/SUB-llm.md:281`
- `docs/map/SUB-llm.md:313`
- `docs/map/SUB-llm.md:326`
- `docs/map/SUB-scratch.md:226`

`src/deepreason/rules/crit.py` — 76 hit(s):

- `docs/map/CON-authority.md:4`
- `docs/map/CON-authority.md:86`
- `docs/map/CON-authority.md:87`
- `docs/map/CON-authority.md:88`
- `docs/map/CON-authority.md:89`
- `docs/map/CON-authority.md:157`
- `docs/map/CON-capability-lifecycle.md:51`
- `docs/map/CON-conjecture-kinds.md:4`
- `docs/map/CON-conjecture-kinds.md:42`
- `docs/map/CON-conjecture-kinds.md:215`
- `docs/map/CON-conjecture-source.md:109`
- `docs/map/CON-criticism-source.md:4`
- `docs/map/CON-criticism-source.md:27`
- `docs/map/CON-criticism-source.md:59`
- `docs/map/CON-criticism-source.md:102`
- `docs/map/CON-criticism-source.md:130`
- `docs/map/CON-discharge-channel.md:252`
- `docs/map/CON-packs-and-token-economy.md:4`
- `docs/map/CON-packs-and-token-economy.md:54`
- `docs/map/CON-packs-and-token-economy.md:280`
- `docs/map/CON-schools.md:4`
- `docs/map/CON-warrants-and-attacks.md:53`
- `docs/map/SCHEMA.md:85`
- `docs/map/SEAM-adjudication-x-rules.md:79`
- `docs/map/SEAM-adjudication-x-rules.md:85`
- `docs/map/SEAM-adjudication-x-rules.md:138`
- `docs/map/SEAM-adjudication-x-rules.md:146`
- `docs/map/SEAM-adjudication-x-rules.md:237`
- `docs/map/SEAM-calculus-x-rules.md:64`
- `docs/map/SEAM-capabilities-x-rules.md:4`
- `docs/map/SEAM-capabilities-x-rules.md:40`
- `docs/map/SEAM-evaluation-x-ontology.md:122`
- `docs/map/SEAM-evaluation-x-rules.md:84`
- `docs/map/SEAM-evaluation-x-rules.md:94`
- `docs/map/SEAM-evaluation-x-rules.md:167`
- `docs/map/SEAM-evaluation-x-rules.md:198`
- `docs/map/SEAM-llm-x-rules.md:4`
- `docs/map/SEAM-llm-x-rules.md:39`
- `docs/map/SEAM-llm-x-rules.md:57`
- `docs/map/SEAM-llm-x-rules.md:117`
- `docs/map/SEAM-llm-x-rules.md:140`
- `docs/map/SEAM-llm-x-rules.md:147`
- `docs/map/SEAM-llm-x-rules.md:152`
- `docs/map/SEAM-llm-x-rules.md:159`
- `docs/map/SEAM-llm-x-rules.md:169`
- `docs/map/SEAM-llm-x-rules.md:204`
- `docs/map/SEAM-llm-x-rules.md:353`
- `docs/map/SEAM-llm-x-workflow.md:143`
- `docs/map/SEAM-llm-x-workflow.md:248`
- `docs/map/SEAM-manifest-x-schools.md:138`
- `docs/map/SEAM-manifest-x-schools.md:148`
- `docs/map/SEAM-ontology-x-rules.md:35`
- `docs/map/SEAM-ontology-x-rules.md:179`
- `docs/map/SEAM-rules-x-scratch.md:4`
- `docs/map/SEAM-rules-x-scratch.md:64`
- `docs/map/SEAM-rules-x-scratch.md:137`
- `docs/map/SEAM-rules-x-workflow.md:4`
- `docs/map/SEAM-rules-x-workflow.md:49`
- `docs/map/SEAM-rules-x-workflow.md:57`
- `docs/map/SEAM-rules-x-workflow.md:93`
- `docs/map/SEAM-rules-x-workflow.md:106`
- `docs/map/SEAM-rules-x-workflow.md:115`
- `docs/map/SEAM-rules-x-workflow.md:140`
- `docs/map/SEAM-rules-x-workflow.md:166`
- `docs/map/SEAM-scheduler-x-rules.md:4`
- `docs/map/SEAM-scheduler-x-rules.md:105`
- `docs/map/SEAM-scheduler-x-rules.md:124`
- `docs/map/SEAM-scheduler-x-rules.md:144`
- `docs/map/SEAM-schools-x-scratch.md:115`
- `docs/map/SEAM-schools-x-scratch.md:157`
- `docs/map/SUB-evaluation.md:89`
- `docs/map/SUB-rules.md:87`
- `docs/map/SUB-rules.md:129`
- `docs/map/SUB-rules.md:175`
- `docs/map/SUB-rules.md:239`
- `docs/map/SUB-workflow.md:330`

`src/deepreason/ontology/problem.py` — 2 hit(s):

- `docs/map/SEAM-ontology-x-rules.md:4`
- `docs/map/SEAM-ontology-x-rules.md:87`

`src/deepreason/signals.py` — 10 hit(s):

- `docs/map/INV-signal-contract.md:4`
- `docs/map/REC-add-signal.md:21`
- `docs/map/REC-add-signal.md:35`
- `docs/map/REC-add-signal.md:55`
- `docs/map/SUB-harness.md:131`
- `docs/map/SUB-harness.md:175`
- `docs/map/SUB-rules.md:133`
- `docs/map/SUB-rules.md:134`
- `docs/map/SUB-scheduler.md:134`
- `docs/map/SUB-scheduler.md:135`

`_versioned_source_config_data` — 12 hit(s):

- `docs/map/INV-frozen-surfaces.md:338`
- `docs/map/INV-frozen-surfaces.md:359`
- `docs/map/INV-frozen-surfaces.md:429`
- `docs/map/INV-frozen-surfaces.md:651`
- `docs/map/INV-frozen-surfaces.md:694`
- `docs/map/INV-frozen-surfaces.md:723`
- `docs/map/INV-frozen-surfaces.md:877`
- `docs/map/SEAM-adjudication-x-authority.md:162`
- `docs/map/SEAM-capabilities-x-channels.md:111`
- `docs/map/SEAM-schools-x-scheduler.md:118`
- `docs/map/SUB-manifest.md:198`
- `docs/map/SUB-manifest.md:244`

`ArgumentativeCriticOutput` — 1 hit(s):

- `docs/map/CON-criticism-source.md:147`

`BatchCase` — 1 hit(s):

- `docs/map/CON-criticism-source.md:147`

`SpawnTrigger` — 33 hit(s):

- `docs/map/CON-problem-layer-lifecycle.md:256`
- `docs/map/CON-problem-layer-lifecycle.md:267`
- `docs/map/CON-scheduler-ranking.md:30`
- `docs/map/CON-scheduler-ranking.md:74`
- `docs/map/CON-scheduler-ranking.md:163`
- `docs/map/INV-axiom-basis.md:250`
- `docs/map/INV-axiom-basis.md:281`
- `docs/map/INV-axiom-basis.md:283`
- `docs/map/INV-evidence-channels.md:104`
- `docs/map/SEAM-capabilities-x-rules.md:153`
- `docs/map/SEAM-capabilities-x-rules.md:155`
- `docs/map/SEAM-capabilities-x-rules.md:238`
- `docs/map/SEAM-evaluation-x-ontology.md:207`
- `docs/map/SEAM-ontology-x-rules.md:27`
- `docs/map/SEAM-ontology-x-rules.md:38`
- `docs/map/SEAM-ontology-x-rules.md:56`
- `docs/map/SEAM-ontology-x-rules.md:181`
- `docs/map/SEAM-ontology-x-rules.md:227`
- `docs/map/SEAM-ontology-x-rules.md:230`
- `docs/map/SEAM-rules-x-scratch.md:143`
- `docs/map/SEAM-rules-x-scratch.md:151`
- `docs/map/SEAM-scheduler-x-rules.md:91`
- `docs/map/SEAM-scheduler-x-rules.md:155`
- `docs/map/SEAM-scheduler-x-rules.md:235`
- `docs/map/SUB-ontology.md:41`
- `docs/map/SUB-ontology.md:75`
- `docs/map/SUB-ontology.md:172`
- `docs/map/SUB-ontology.md:211`
- `docs/map/SUB-rules.md:136`
- `docs/map/SUB-rules.md:144`
- `docs/map/SUB-rules.md:150`
- `docs/map/SUB-rules.md:192`
- `docs/map/SUB-scheduler.md:251`


### Census notes

Two entries in the map-check list are not consumers of this change at all and
are recorded so a later reader does not chase them: `docs/map/SCHEMA.md:85`
names `rules/crit.py` inside a worked EXAMPLE of check syntax, and the
`docs/map/*.md:4` hits are `Owns:` headers rather than checks. Both are left
untouched.

Nine of the map-check hits on `src/deepreason/rules/crit.py` belong to documents
this tranche does NOT edit (`CON-authority`, `CON-conjecture-kinds`,
`CON-packs-and-token-economy`, `CON-schools`, `SEAM-adjudication-x-rules`,
`SEAM-capabilities-x-rules`, `SEAM-evaluation-x-rules`, `SEAM-llm-x-rules`,
`SEAM-rules-x-workflow`, `SEAM-scheduler-x-rules`, `SUB-rules`,
`SUB-workflow`). They stay green because `crit.py` takes a zero-line diff under
the granted cone. If Q3 answers Road A, EVERY ONE of them must be re-run before
that commit, and `SEAM-llm-x-rules` and `SEAM-scheduler-x-rules` re-read — that
cost is part of Road A's price and is stated here rather than discovered later.

## Measurements

Every number below was measured on this branch (`claude/b2-lane-B`, worktree
`/home/user/dr-lanes/lane-B`) at spec time, on an otherwise idle box, and is
pasted rather than recalled.

M1: `python tools/blast_radius.py --files ... --symbols ...` (the command in the
forecast section) -> `frozen_surface_verdict: CONTACT`, 2 `frozen_surface_contacts`,
0 `frozen_adjacent_contacts`. — supports the Q1 request and its exact scope.

M2: `python -m pytest tests/test_decommissioned_pipeline_stays_out.py tests/test_h1_no_spawn_from_refutation.py -q`
->

    ..........                                                               [100%]
    10 passed in 0.34s

— supports P-FIX-1 and P-FIX-2: both guard files are GREEN before this tranche,
so anything red afterwards is this tranche's doing and nothing else's.

M3: `python -c "from deepreason.config import Config; from deepreason.run_manifest import source_config_hash; [print(v, source_config_hash(Config(), schema_version=v)) for v in (1,2,3,4,5,6)]"`
->

    1 6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81
    2 6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81
    3 2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
    4 2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
    5 2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
    6 2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5

— supports S15's accept command: these are the two literals that must be
byte-identical after the two `data.pop` lines land.

M4: a scan of every `.py` under `src/deepreason` for the four producer spellings
`SpawnTrigger.SUCCESSOR`, `trigger="successor"`, `trigger='successor'`,
`"trigger": "successor"` -> `[]`. — supports the claim that SUCCESSOR has ZERO
producers today, and therefore that S13 creates the first one and P-FIX-1 is
unavoidable rather than optional.

M5: `echo "scratch=$(grep -c scratch src/deepreason/rules/crit.py) fence=$(grep -c fence src/deepreason/rules/crit.py)"`
-> `scratch=2 fence=6`. — supports S12's accept command and the claim that the
two pinned counts in `docs/map/SEAM-rules-x-scratch.md` are green now, so any
movement is this tranche's.

M6: `python -c "from deepreason.ontology.problem import SpawnTrigger; print(SpawnTrigger.SEED != SpawnTrigger.SEED, SpawnTrigger.SUCCESSOR != SpawnTrigger.SEED, sorted([True, False]))"`
-> `False True [False, True]`. And
`grep -c "provenance.trigger != SpawnTrigger.SEED" src/deepreason/scheduler/scheduler.py`
-> `2`. — supports Q4's Reading 1: a minted successor loses the rank TIE to the
seed by construction, in both selection modes, with no code change. It does NOT
support strict domination, and this measurement is the reason Q4 exists.

M7: `grep -c '^    data\.pop(' src/deepreason/run_manifest.py` -> `25`; the
eight-space (schema-version-conditional) count is `2`. — supports S15's
"insertions only, 25 -> 27" and its exact-indent accept command.

M8: `grep -rn "unknown_channel_notices" --include=*.py src/deepreason/ | grep -v channels.py | grep -v v6_policy`
-> no production caller. — supports Q2 Road B's honest cost: the shipped
registry template's own notice function has no production caller either, so
"typed and tested but not printed by today's CLI" is the shipped state of the
art here, not a shortcut invented for this tranche.

## Options

**Q2 — where the enablement warning is emitted.**

A: `_CARRIAGE_REQUALIFIES` row inside `run_manifest.py` | frozen contact: a
SECOND surface-4 edit | ~1 line | risk: widens Q1's grant | rejected as the
default: cites M8 — the shipped pattern does not require it, and a second
frozen contact for one line of stderr text is the operator's price to accept,
not mine.

B: the registry declares the text; `minting_notices(config)` returns it typed;
the mint path records it on the append-only record | frozen contact: none | ~25
lines | risk: not printed by today's CLI | **CHOSEN (provisionally)**: cites M8.

**Q3 — who writes the successor question to its destination.**

A: `rules/crit.py` dispatches, late-bound, beside `_file_attribution` | frozen
contact: none | ~20 lines in `crit.py` + 12 map documents to re-run | risk: a
workaround of `SEAM-rules-x-scratch` rule 6's letter while its own prose says
the spirit is the operator's call; also outside this lane's granted cone
(`crit.py` OUTPUT SCHEMA ONLY) | rejected pending the operator's word.

B: a reader outside `rules/` walks what criticism already recorded
(`LLMCall.raw_ref`) and routes it | frozen contact: none | ~60 lines, more
failure modes (alias resolution, recomputing the originating problem) | risk:
more code, more ways to be wrong | **CHOSEN (provisionally)**: it is the only
road that leaves the asymmetry as written AND fits the granted cone. Cites the
`DR-CON-discharge-channel` precedent, which is a reader of what
`_observe_case` already records.

**Q4 — how strong R5 is.**

A: tie guarantee | code change: none | proof: S18 | **CHOSEN**: cites M6.

B: strict domination | code change: `Scheduler._select_problem`'s rank key |
risk: a socket pinned by two map checks and one regression | rejected for this
tranche: a separate tranche against a pinned promise, and no recorded run has
yet exhibited the failure it would prevent.

## Budget

Itemised per spec item, then summed. The headline equals the computed sum.

    S1 18, S2 16, S3 140, S4 30                     -> B-i    204
    S5 90, S6 15, S7 98, S8 80                      -> B-ii   283
    S9 80, S10 14, S11 110, S12 45                  -> B-iii  249
    S13 60, S16 14, S17 100, S18 60, S21 40, S22 25 -> B-iv   299
    S14 20, S15 2, S19 34, S20 18, S23 20, S24 40   -> B-v    134

    $ python3 -c "print(204+283+249+299+134)"
    1169

**~1169 changed lines, 5 commits — one per sub-tranche, each with its own
delivery.** Over the ~300-line single-tranche threshold, so the split above is
the proposal the skill requires, ordered so that each sub-tranche is
independently green and independently deliverable:

- **B-i** (204) — the optional field and its law line. Lands first because it is
  the only piece with no open question against it, and because R1's architecture
  test must exist before anything can read the field.
- **B-ii** (283) — the destination registry. Depends on nothing; delivers R3 and
  the modularity law's failable check on its own.
- **B-iii** (249) — the default scratchpad route. PROVISIONAL on Q3.
- **B-iv** (299) — the minting road, its gate declaration, and the rank-tie
  proof. PROVISIONAL on Q3; the gate is inert until B-v gives it a switch.
- **B-v** (134) — the two `Config` switches, the two `data.pop` lines, the
  frozen-surface grant record, and the two superseded fixtures. GATED on Q1 and
  Q5. Deliberately last and deliberately smallest: it is the only sub-tranche
  that touches a frozen surface, and it is the only one that trips a tripwire.

Frozen surfaces touched: **ONE — surface 4 (`run_manifest.py`), two insertions,
grant REQUESTED in Q1 and not granted.** Frozen-adjacent: none.

Ceiling held: `python tools/diff_budget.py <tranche-base> --ceiling 1169
--paths src/deepreason tests docs/map experiments/2026-08-30-change-successor-questions`.
An `EXCEEDED` verdict is a STOP and a re-plan, never a quiet overrun.

Rubric: 9/9 yes
- every R has a spec item with a machine-decidable accept? yes (R1 S1/S2/S3, R2 S9/S10/S11, R3 S5/S6/S7/S8, R4 S13/S14/S16/S17, R5 S18, R6 S5/S6/S14)
- every item traces to an R or C number? yes
- the frozen-surface forecast was RUN, not guessed, and its output pasted verbatim? yes (M1, and the pasted JSON)
- every plausible contact is a written REQUEST rather than an assumption? yes (Q1; Q2 prices a second one rather than taking it)
- the blast-radius census lists every hit, none omitted? yes
- every open question is a STOP rather than a silent choice? yes (Q1-Q5; the Questions section is non-empty, so the tranche stops here)
- every predicted fixture change is recorded BEFORE the edit, with its reason? yes (P-FIX-1..4)
- the budget headline equals the pasted arithmetic sum of the itemisation? yes (1169)
- the nearest tempting neighbours are named out of scope? yes (nine of them)
