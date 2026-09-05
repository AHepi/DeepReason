<!-- DR-SUB-minireason -->
Verified-at: f2b736b6a
Verify: python -m pytest mini/tests/ -q
Owns: mini/minireason/
Seams:
Seams-undocumented: llm x minireason, minireason x application, minireason x harness, minireason x manifest, minireason x verification

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
| the stop conditions, or the cycle ceiling | `loop.run`'s `while` conditions and `max_cycles` | `mini/tests/test_loop.py::test_budget_death_is_a_logged_stop` |
| when a problem is called dry, or the stance rotates | `rotate.Turnover` and `rotate.Rotation` | `mini/tests/test_loop.py::test_turnover_advances_the_queue` |
| what counts as orbiting, or a gate block | `gate.orbit`, `gate.gate_blocks` | `mini/tests/test_gate.py` |
| which commitments a candidate must satisfy | NOT here: `checks.compile_checks` delegates to `deepreason.informal.skeleton`; mini owns the reduced POLICY of executing them immediately, not the constructors | `mini/tests/test_checks.py`, `mini/tests/test_normative_kernel.py` |
| what mini sends on the wire | NOT here: `compat.initialize` selects a parent `WireContract`; mini owns no schema | `mini/tests/test_call.py`, `tests/test_wire_contracts.py` |
| which packages a mini run may reach | `mini/tests/test_isolation_fence.py`'s `FENCED` and `ALLOWED` tuples, which quote SPEC S1 verbatim | `mini/tests/test_isolation_fence.py` |

`check: python -m pytest mini/tests/test_loop.py mini/tests/test_gate.py mini/tests/test_checks.py mini/tests/test_compat.py -q`

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
