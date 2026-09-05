<!-- DR-SUB-minireason -->
Verified-at: 9d87325c3
Verify: python -m pytest mini/tests/ -q
Owns: mini/minireason/
Seams: DR-SEAM-llm-x-minireason
Seams-undocumented: minireason x application, minireason x harness, minireason x manifest, minireason x verification

# MiniReason — the reduced engine, and what it deliberately does not have

## What it is

A small outer scheduling loop over the parent's canonical record. It proposes
candidates, checks them, logs, and rotates; everything else — registration,
object identity, replay, attack construction, status — is a parent operation
called from here. That is the whole design: MiniReason owns scheduling, and
owns no second ontology, no second event schema and no second protocol.

It is reached in production through one public flag, `deepreason reason
--shallow`, which is the declared low-cost option and the supported fallback
for a model that cannot complete production qualification. It never consults
or writes the qualification cache.

**This document exists because until 2026-09-05 the map had none.** `docs/map`
described `src/deepreason/`, and a reader following the routing table for a
mini question landed nowhere and could not tell a gap from a miss.

Its size is a claim the parent's own plan makes, so it is checked rather than
stated: MiniReason is the measured fraction of DeepReason, not a rewrite of it.
`check: python -c "
import pathlib
total = sum(len(p.read_text().splitlines())
            for p in pathlib.Path('mini/minireason').glob('*.py'))
parent = sum(len(p.read_text().splitlines())
             for p in pathlib.Path('src/deepreason').rglob('*.py'))
assert 1000 < total < 6000, total
assert total * 20 < parent, (total, parent)
"`

## Entry points

| Called by | Entry | What it does |
|---|---|---|
| `deepreason reason --shallow` (via `src/deepreason/shallow.py`) | `loop.run(problems, endpoint, budget, root, …)` | drives cycles until budget death, queue exhaustion, or global dryness; returns the summary, while the log at `root` is the real output |
| `loop.run`, once, before the first call | `compat.initialize(root, endpoint, model_profile, run_input, dossier)` | freezes the route, the compact wire contract and the v6 manifest |
| anyone binding a root without running | `compat.bind_mini_root(...)` | binds (or verifies) one immutable schema-6 manifest and its run input |
| a reader | `log.replay(root)` → `log.State` | the dict-shaped read view, projected from one canonical `Harness` |
| a seat brief, before its walk | `sources.mini_section_request(session, problem_id, target_id=…, supplied=…)` | the ONE read-only projection from a mini session to the `SectionRequestV1` the shipped section plugins read; it appends nothing and moves no digest |
| a mini seat's brief | `seats.render_mini_brief(session, seat_id, problem_id, target_id=…, receipts=…)` | shell → layout → request → the PUBLIC walk and allocation in `deepreason.llm.packs`; builds no section, names no private symbol |
| the commitment seat, after its call | `seats.record_commitment_proposals(session, proposals, spend=…)` | one record per proposal; drops one that names nothing in the run, typed |
| a mini seat's form | `seats.form_for_seat(seat_id, form_id=None, shell_id=None)` | the form resolved THROUGH the shell's `form_id` — that field's first consumer anywhere; argument and `DEEPREASON_MINI_FORM` still win |

`check: python -c "
import inspect
from minireason import compat, loop
run = inspect.signature(loop.run).parameters
for name in ('problems', 'endpoint', 'budget', 'root', 'run_input', 'dossier'):
    assert name in run, (name, list(run))
init = inspect.signature(compat.initialize).parameters
for name in ('root', 'endpoint', 'model_profile', 'run_input', 'dossier'):
    assert name in init, (name, list(init))
"`

## State it owns

**None that the parent does not.** A mini root is a strict subset of a parent
root — `log.jsonl`, `blobs/`, `objects/`, `run-manifest.json`,
`run-input.json`, `evidence-dossier.json` — so `Harness(root)` opens one
unchanged. `log.ObjectStore` and `log.EventLog` are adapters over the parent's
stores, not stores; `log.State` recomputes nothing, and its `refuted` and
`accepted` sets read the canonical adjudicator's labels rather than relabelling.

`check: python -c "
import inspect
from minireason import log
for name in ('artifacts', 'problems', 'commitments', 'warrants', 'statuses'):
    body = inspect.getsource(getattr(log.State, name).fget)
    assert '_harness' in body, (name, body)
assert 'Status.REFUTED' in inspect.getsource(log.State.refuted.fget)
"`

The run manifest it binds is the smallest honest v6 surface: the mandatory
control plane in its explicit minimal/disabled form, and the transactional-only
authorities set to `None` rather than declared-and-ignored, because mini runs
through the Harness primitive layer and never through the v6 transaction
controller.
`check: python -c "
from minireason.compat import _TRANSACTIONAL_ONLY_FIELDS
expected = {'compact_recovery_policy', 'contract_schema_repair_policy',
            'route_seat_behavioral_capability_plan',
            'route_seat_contract_decomposition_plan',
            'production_qualification_policy', 'terminal_commitment_policy'}
assert set(_TRANSACTIONAL_ONLY_FIELDS) == expected, _TRANSACTIONAL_ONLY_FIELDS
"`

## The starting input: constant, or the standard frozen one

A mini root binds ONE run input, and there are exactly two kinds. Supplying
none binds mini's constant process root (`minireason:process-root`), which
declares honestly that it carries no frozen criteria and attaches no evidence.
Supplying a `RunInputManifestV2` — the record `deepreason input freeze` writes
and the full harness takes — binds THAT, and the manifest's
`run_input_digest` is the frozen record's.

Reopening a root against a DIFFERENT frozen input is refused
`MINI_ROOT_RUN_INPUT_MISMATCH`: a root's identity includes what it was asked,
and a manifest saying one thing while the run answered another is a reader's
trap. Rebinding the SAME one is not a refusal — it is the crash-recovery path.

`check: python -m pytest mini/tests/test_compat.py -k "frozen_input or process_root or run_input" -q`

## Forms, and the commitment channels a run executes

**A FORM is what a mini seat is ASKED FOR.** `minireason/forms.py` registers
them by id, beside each other, so selecting one is configuration rather than a
code edit. Four ship: the STORED conjecturer form (the shipped
`ReferenceFreeConjecturerWireContract` instance, held rather than copied, so
"stored, not deleted" is a property of an object nobody rewrote), a relaxed
conjecturer, a relaxed critic and a relaxed commitment proposal.

Selection is argument, then `DEEPREASON_MINI_FORM` (as `<seat>=<form_id>`
terms, because one process renders every seat), then the caller's declared
default. **Never `Config` and never the manifest**, for the measured reason:
`run_manifest.py` dumps every `Config` field into `engine_config_json` and
`qualification.py` folds that into every qualification subject digest, so an
id declared there would move the digest of every qualification bundle in the
tree.

No mini form bounds a string or a list. Checked over every registered form's
whole rendered schema rather than over the fields one tranche happened to
write, because a bound added later to a nested model would be just as much a
limit and just as invisible.
`check: python -m pytest mini/tests/test_mini_forms.py -q`

**COMMITMENTS ARE TWO CHANNELS, AND EACH SWITCHES INDEPENDENTLY.**
`minireason/policy.py` declares `MiniCommitmentPolicyV1`, with
`mandatory_skeleton_wf` (the well-formedness commitment compiled onto EVERY
candidate) and `model_authored_forbidden` (the candidate's own `forbidden[]`).
Both default ON, so a caller that selects nothing gets exactly the behaviour
that shipped before this existed.

Why two and not one: the operator must be able to restore either. And why the
switch exists at all — relaxing the FORM buys nothing on its own, because free
prose already passes the shipped wire schema. Measured, and committed as a
test rather than left in a proof file: a three-cycle run of free prose under
the default policy ends 6 admitted, 6 refuted, ZERO survivors; the same run
with both channels off ends 0 refuted, 6 survivors, and still replays.

**Switching a channel off writes a typed WARNING into the run's own record**,
never a refusal and never silence — one marker per disabled channel plus a
summary line, all prefixed `mini:commitments-disabled`. Per channel rather
than one blob, because a reader wants to know WHICH check did not run.
`check: python -m pytest mini/tests/test_mini_commitment_policy.py -q`

`check: python -c "
from minireason.checks import compile_checks
from minireason.policy import MiniCommitmentPolicyV1
off = MiniCommitmentPolicyV1(mandatory_skeleton_wf=False,
                             model_authored_forbidden=False)
assert compile_checks('free prose, no skeleton', policy=off) == []
assert compile_checks('free prose, no skeleton') != []
assert MiniCommitmentPolicyV1().warning_markers() == ()
assert len(off.warning_markers()) == 3, off.warning_markers()
"`

**Within mini, a criticism overturns nothing** (operator, 2026-09-05: "within
mini, criticism can't overturn anything. The point is content generation for
now. Then testing on the full harness."). The critic and commitment forms
carry no score, rank, weight, confidence, priority, authority or severity
field, and no elimination road is built for mini — not behind a switch, not
off by default, not at all.
`check: python -c "
from minireason.forms import mini_form_ids, resolve_mini_form
banned = {'score', 'rank', 'weight', 'confidence', 'priority', 'authority',
          'severity'}
for form_id in mini_form_ids():
    schema = resolve_mini_form(form_id).wire_model.model_json_schema()
    fields = set(schema.get('properties', {}))
    for nested in schema.get('\$defs', {}).values():
        fields |= set(nested.get('properties', {}))
    assert not (fields & banned), (form_id, fields & banned)
"`

## Who sees what: the three seats' briefs

**Every mini seat's brief is a registered LAYOUT walked through the one public
road the full harness's seats share** (`deepreason.llm.packs.render_seat_brief`
and `allocate_seat_brief`); mini builds no section and has no renderer of its
own. `minireason/sources.py` holds the projection that feeds the walk and the
four mini section plugins; `minireason/seats.py` holds the three layouts, one
per seat, bound as each seat's default.

| seat | layout | sections, in order |
|---|---|---|
| `mini.conjecturer` | `seat-pack.mini.conjecturer.v0` | problem · everything-so-far · directive |
| `mini.critic` | `seat-pack.mini.critic.v0` | problem · target-conjecture · directive |
| `mini.commitment` | `seat-pack.mini.commitment.v0` | problem · everything-so-far · target-conjecture · directive |

**The critic's blinding is STRUCTURAL, not a filter** (R5, "critics see the
conjecture artifact, not the proposed commitments"): the critic layout
registers NO section that could carry a proposal, so there is no slot, blank
or otherwise — the shape the amended judge law (2026-08-28) already required
of provenance blinding. And no mini brief renders a status label of any kind:
the audit of 2026-09-05 (row 3) found the full harness's default critic brief
printing one, and mini's sources may not read a status at all, checked over
the AST.
`check: python -c "
import sys; sys.path.insert(0, 'mini')
from deepreason.llm.seat_sections import resolve_seat_pack_layout
import minireason.seats as seats
critic = resolve_seat_pack_layout(seats.CRITIC_SEAT, seats.CRITIC_LAYOUT_ID)
ids = [e.plugin_id for e in critic.entries]
assert ids == ['mini.problem', 'mini.target-conjecture', 'mini.directive'], ids
assert not any('commitment' in i or 'everything' in i for i in ids), ids
for seat in seats.MINI_SEATS:
    layout = resolve_seat_pack_layout(seat)
    assert layout.layout_id == seats.MINI_LAYOUTS[seat].layout_id, seat
    for entry in layout.entries:
        assert not entry.droppable and not entry.compressible, (seat, entry.plugin_id)
"`

**Three shells, and the shell's form is READ.** `seat.mini.conjecturer.v0`,
`seat.mini.critic.v0` and `seat.mini.commitment.v0` each pair a layout with a
relaxed form; binding another shell in a seat's place changes both what the
seat is shown and what it is asked for, because `form_for_seat` takes the
shell's `form_id` as its default.
`check: python -c "
import sys; sys.path.insert(0, 'mini')
from deepreason.llm.seat_sections import resolve_seat_shell
from deepreason.llm.seat_layouts import CONJECTURER_LEGACY_SHELL, CRITIC_LEGACY_SHELL
from minireason.seats import MINI_SEATS, MINI_SHELLS, form_for_seat
for seat in MINI_SEATS:
    shell = resolve_seat_shell(seat)
    assert shell == MINI_SHELLS[seat] and form_for_seat(seat).form_id == shell.form_id, seat
assert resolve_seat_shell('conjecturer') == CONJECTURER_LEGACY_SHELL
assert resolve_seat_shell('argumentative_critic') == CRITIC_LEGACY_SHELL
"`

**"Everything generated so far" is shown in FULL, and what stays visible as
the pool grows is a RULE, never a verdict** (R6; monitor's recommendation the
operator accepted 2026-09-05). `mini.everything-so-far` renders every artifact
in the record, whole, oldest first — the legacy loop's eight-survivor window
and 300-character cut are gone from this road — and a declared budget
withholds the OLDEST whole entries first, naming them in the section itself
under the rule's id. Two rules ship, `mini.retention.everything.v1` (the
default) and `mini.retention.recency.v1`; a third is a registration.
`check: python -m pytest mini/tests/test_mini_sources.py -q`

## The commitment seat writes a RECORD, never an artifact

**A commitment proposal is recorded, not registered** (R4; the ruling of
2026-09-05 that within mini criticism overturns nothing; Q-A's E3 not built).
`seats.record_commitment_proposals` writes each proposal through
`records.record_mini_output`: a Measure event whose inputs name the marker
`mini:record`, the kind `mini.commitment-proposal.v1`, the conjecture it is
about, and a content-addressed blob holding the free-prose body. The
proposal's ONLY requirement is that it names a conjecture present in the run;
one that does not is DROPPED with a typed `mini:record-dropped` event, never
written dangling. The spend lands exactly once.

Why a record and not an artifact: every authority path — rank, admission,
immunity, attack edges, refutation, status — reads `state.artifacts`, and a
record is nowhere in that map, so "shape buys nothing" is a property of the
record's shape rather than of anyone's restraint. The other road, an artifact
under a new provenance role, was measured and closed: `tools/blast_radius.py`
reads widening `Provenance` as CONTACT on the harness surface, and no grant
exists. `records.mini_records` reads them back; `sources.everything_so_far`
merges artifacts and records into one pool in record order, and that pool is
what "everything generated so far" shows.
`check: python -m pytest mini/tests/test_mini_commitment_seat.py -q`

`check: python -c "
import ast, pathlib
src = pathlib.Path('mini/minireason/records.py').read_text()
tree = ast.parse(src)
names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
for forbidden in ('create_artifact', 'register_artifact', 'register_batch', 'register_commitment', 'register_fail_warrant', 'Artifact', 'Commitment', 'status'):
    assert forbidden not in names, forbidden
assert 'measure' in names and 'put' in names
"`

## The controller hook: declared, and called by nothing

R7 asks that what a seat is shown be "calibrated on the fly and modifiable by
the controller"; R8 is "Don't change the controller just yet". So
`seats.MiniCalibrationHookV1` is the SEAM and nothing behind it: a protocol
(`calibrate(seat_id, cycle, entries) -> entries | None`), a registry selected
by id with typed refusals, and ONE registered implementation,
`mini.calibration.noop.v1`, which returns `None`. The window ruling of
2026-09-05 binds the other half — the hook has ZERO callers, asserted on the
AST — and supersedes the programme SPEC's earlier "the loop calls it between
cycles". Exactly two lines under `src/` and `mini/minireason/` name the
registration function: its definition and the no-op's registration; a third
is a controller stepping in before the operator said how.
`check: test "$(grep -rn "register_mini_calibration_hook" src/ mini/minireason/ | wc -l)" -eq 2 && python -m pytest mini/tests/test_mini_calibration_hook.py -q`

## The flow: stage order and the set of artifact kinds are data

`minireason/flow.py` registers `MiniFlowV1`s by id: a tuple of `MiniStageV1`s
(seat, shell, the kind produced, the kinds read, once per cycle or once per
target), the SET of artifact kinds the flow may carry, its commitment policy
and its calibration hook id. A stage naming a kind the flow does not declare
is refused at construction. Two ship: `mini.flow.legacy-v0`, the DEFAULT —
one conjecturer stage under `seat.mini.conjecturer.legacy-v0`, which renders
today's prompt byte for byte through the same road as every other seat (one
section, pinned by `mini/tests/goldens/mini_legacy_prompt.txt`) and fills the
STORED form with both commitment channels ON; and `mini.flow.isolation.v1`,
conjecturer → critic → commitment with both channels OFF. Selection is
argument, then `DEEPREASON_MINI_FLOW`, then the default; never `Config`,
never the manifest.
`check: python -m pytest mini/tests/test_mini_flow.py -q`

`check: python -c "
import sys; sys.path.insert(0, 'mini')
from minireason.flow import DEFAULT_MINI_FLOW_ID, resolve_mini_flow, select_mini_flow, mini_flow_ids
assert DEFAULT_MINI_FLOW_ID == 'mini.flow.legacy-v0' and select_mini_flow().flow_id == DEFAULT_MINI_FLOW_ID
legacy = resolve_mini_flow('mini.flow.legacy-v0'); iso = resolve_mini_flow('mini.flow.isolation.v1')
assert len(legacy.stages) == 1 and legacy.commitment_policy.disabled_channels == ()
assert [s.stage_id for s in iso.stages] == ['conjecture', 'criticism', 'commitment']
assert set(iso.artifact_kinds) == {s.produces_kind for s in iso.stages}
assert len(iso.commitment_policy.disabled_channels) == 2
"`

## The isolation fence
## The isolation fence
## The isolation fence
## The isolation fence

R1 and R11 — "mini needs to be tested in isolation", "without the larger
harness activated" — are enforced by `mini/tests/test_isolation_fence.py`
rather than by convention. Three parts: mini's own sources import no fenced
module directly; importing mini adds no fenced package beyond the closure the
allowed record modules already bring; and a run imports no fenced module that
was not loaded when it started.

**What it does not prove**, stated here so it is never over-read: four of the
eleven fenced packages (`adjudication`, `bridge`, `capabilities`,
`workflow.transaction_service`) are already loaded by the modules mini is
ALLOWED to use, because the event ontology imports its bridge and capability
payload types and the harness imports the adjudicator's edge builders. Those
modules ARE the record rather than the harness around it. No test here shows
that no code inside those four ever executes; proving non-execution is a
different instrument and is not built.

`check: python -m pytest mini/tests/test_isolation_fence.py -q`

## Invariants

- `DR-INV-frozen-surfaces` — mini writes through the parent's frozen record
  surfaces and may not fork them.
- `DR-CON-warrants-and-attacks` — no warrant, no edge, no REFUTED. Mini's
  `Session.refute` registers a fail warrant through
  `deepreason.rules.warrants`; it labels nothing itself.
- `DR-CON-run-identity` — a legacy pre-v6 mini root fails closed on reopen with
  `UNSUPPORTED_RUN_MANIFEST_VERSION` and is never migrated or rewritten;
  `log.replay` reads one read-only, from the event log alone.

`check: python -c "
import inspect
from minireason import loop
body = inspect.getsource(loop.Session.refute)
assert 'register_fail_warrant' in body, body
assert 'REFUTED' not in body, 'mini must not label a status itself'
"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| what a mini run is started FROM | `compat.bind_mini_root`'s `run_input`/`dossier` parameters, and `shallow.py::_load_frozen_input` for the CLI road | `mini/tests/test_compat.py`, `tests/test_shallow_reason.py::test_shallow_takes_the_standard_frozen_input` |
| which FORM a seat is asked to fill, or add one | `minireason/forms.py`: register a `MiniFormV1` beside the others. Never `Config`, never the manifest | `mini/tests/test_mini_forms.py` |
| which commitment channels a run executes | `MiniCommitmentPolicyV1` in `minireason/policy.py`, passed to `loop.run` as `commitment_policy`. Switching one off writes its own typed warning into the record | `mini/tests/test_mini_commitment_policy.py` |
| the stop conditions, or the cycle ceiling | `loop.run`'s `while` conditions and `max_cycles` | `mini/tests/test_loop.py::test_budget_death_is_a_logged_stop` |
| when a problem is called dry, or the stance rotates | `rotate.Turnover` and `rotate.Rotation` | `mini/tests/test_loop.py::test_turnover_advances_the_queue` |
| what counts as orbiting, or a gate block | `gate.orbit`, `gate.gate_blocks` | `mini/tests/test_gate.py` |
| what a compiled commitment MEANS | NOT here: `checks.compile_checks` delegates to `deepreason.informal.skeleton`; mini owns which channels it COMPILES (the policy above), never what a commitment means | `mini/tests/test_checks.py`, `mini/tests/test_normative_kernel.py` |
| what mini sends on the wire | NOT here: `compat.initialize` selects a parent `WireContract`; mini owns no schema | `mini/tests/test_call.py`, `tests/test_wire_contracts.py` |
| what a mini seat's request CARRIES (a target, the frozen criteria, a caller's own keys) | `sources.mini_section_request`'s `supplied` mapping; the caller's keys win. It may READ the state and the record and may never append, and it never reads an artifact's status | `mini/tests/test_mini_sources.py` |
| what a mini seat is SHOWN, or add a section to a mini brief | a layout in `minireason/seats.py`, or a `.layout.json` under `<DEEPREASON_HOME>/seat_plugins/` naming a registered plugin (`DR-REC-add-a-section-plugin`) — no source edit; the directive wording is a layout entry's `text` param | `mini/tests/test_mini_sources.py`, `mini/tests/test_mini_exposure.py` |
| how much of the pool a seat sees as it grows | the `mini.everything-so-far` entry's `retention_rule`, `budget_chars`, `keep_last` params; a new rule is `sources.register_mini_retention_rule` | `mini/tests/test_mini_sources.py` |
| what a mini seat writes when it is not a conjecture, or add a record KIND | `records.record_mini_output(session, kind, body=…, about=…)` — a typed event and a blob, never an artifact; a kind is a string a flow names as data | `mini/tests/test_mini_commitment_seat.py` |
| how a controller would reshape what a seat is shown | NOT yet: implement `MiniCalibrationHookV1`, register it — and the operator says when (R8); today only the no-op is registered and nothing calls it | `mini/tests/test_mini_calibration_hook.py` |
| which seats run, in what order, producing which kinds — or add a stage | a `MiniFlowV1` registered through `flow.register_mini_flow` (from any module, a test file included), selected by argument or `DEEPREASON_MINI_FLOW`; never `loop.py`, which names no seat, kind or stage | `mini/tests/test_mini_flow.py`, `mini/tests/test_mini_architecture.py` |
| which packages a mini run may reach | `mini/tests/test_isolation_fence.py`'s `FENCED` and `ALLOWED` tuples, which quote SPEC S1 verbatim | `mini/tests/test_isolation_fence.py` |

`check: python -m pytest mini/tests/test_loop.py mini/tests/test_gate.py mini/tests/test_checks.py mini/tests/test_compat.py mini/tests/test_mini_forms.py mini/tests/test_mini_commitment_policy.py -q`

## Traps

- **Mini's own tests are outside the gate every tranche runs.** `pyproject.toml`
  declares `testpaths = ["tests", "mini/tests"]`, but the documented gate is
  `pytest tests/ -q -n 4`, and an explicit path argument overrides `testpaths`.
  So a tranche can report "0 failed" while never collecting a single mini test.
  Run `python -m pytest mini/tests/ -q` yourself. Parked, with its
  ready-to-send prompt, at
  `experiments/2026-09-05-change-mini-isolation-programme/PARKED.md` P1.
  `check: python -c "
  import subprocess, sys
  out = subprocess.run([sys.executable, '-m', 'pytest', 'tests/',
                        '--collect-only', '-q'], capture_output=True, text=True)
  assert 'test_isolation_fence' not in out.stdout, (
      'the documented gate now reaches mini; delete this trap')
  "`
- **The manifest names a conjecturer contract the dispatch does not use.**
  `compat` binds `ContractVersionPolicyV3()`, whose
  `conjecturer_turn_contract` defaults to `conjecturer.turn.v6`, while the
  compact profile dispatches `ReferenceFreeConjecturerWireContract`
  (`conjecturer.compact.reference_free.v1`). Measured harmless — a mini root
  with a contract id that never existed still returns `verify_root violations:
  0`, because the branch that would check it sits behind
  `h.workflow_state.work_orders`, which is empty for a mini root — but harmless
  is not truthful. Parked as P2 of the same file.
  `check: python -c "
  from deepreason.run_manifest import ContractVersionPolicyV3
  from deepreason.llm.wire import ReferenceFreeConjecturerWireContract
  declared = ContractVersionPolicyV3().conjecturer_turn_contract
  dispatched = ReferenceFreeConjecturerWireContract().contract_id
  assert declared != dispatched, (
      'the manifest and the dispatch agree now; delete this trap')
  "`
- **Importing `deepreason.application.conjecture` used to start the run
  engine.** The boundary package eagerly re-exported the text-run service, so a
  reduced-engine run that touches the conjecture boundary dragged the whole v6
  text-run stack in with it. Fixed 2026-09-05 (step 10a of the mini isolation
  programme) by making those three names lazy; the isolation fence's second
  part goes red if the eager import returns.
  `check: python -c "
  import pathlib
  src = pathlib.Path('src/deepreason/application/__init__.py').read_text()
  assert 'from deepreason.application.text_runs import' not in src, src[:200]
  assert '_LAZY_TEXT_RUNS' in src
  "`
