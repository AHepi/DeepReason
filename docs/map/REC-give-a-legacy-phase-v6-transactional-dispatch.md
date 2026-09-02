<!-- DR-REC-give-a-legacy-phase-v6-transactional-dispatch -->
Verified-at: 66e56fe88
Verify: python -m pytest tests/test_hv_v6_reachability.py -q
Owns: src/deepreason/workflow/legacy_phase_contracts.py
Seams: DR-SEAM-scheduler-x-workflow

# Recipe — give a legacy model phase v6 transactional dispatch

Eleven optional model phases sit behind
`Scheduler._defer_untransactional_v6_phase`. Until 2026-09-02 that gate decided
on `schema_version` alone, so all eleven were dead on every current run; it now
consults a declared table and opens for a phase whose seat holds the grant it
needs. **Two of the eleven are converted.** This is the path for the next one.

One phase per tranche. A tranche that converts two has no way to say which one
broke the gate.

## Before you start

The phase must be one whose acceptance can be stated as *"the seat holds a
contract that authorizes this exact call"*. If it cannot — if the phase needs a
contract nothing mints, or a work kind replay validation would have to learn —
this recipe does not cover it, and the answer is a PRICED STOP, not an
improvisation. `DR-INV-frozen-surfaces` says why: a new work kind is contact
with surface 3.

Read `DR-SEAM-scheduler-x-workflow` first, and its `Traps`. The agreement this
recipe operates inside is that the scheduler owns attention and no transaction,
and the workflow plane owns process authority and no cycle.

## Step 1 — read the phase's row

`src/deepreason/workflow/legacy_phase_contracts.py` already has a row for every
call site. The row names the phase, the role it calls, the contract ids that
authorize it, and whether a dispatch has been written.

    python -c "
    from deepreason.workflow.legacy_phase_contracts import LEGACY_PHASE_CONTRACTS as C
    for row in C.values(): print(row.dispatch, row.phase, row.role, sorted(row.contract_ids))
    "

If the row's `contract_ids` is empty, **stop here**: no compiler mints a grant
for that role today, so the gate can never open for it and writing a dispatch
would be writing dead code. `property-design` and `vision-criticism` are both in
that state. Making the grant exist is a `run_manifest.py` change — frozen
surface 4 — and belongs to its own tranche with its own operator grant.

## Step 2 — confirm the contract is already minted

The contract id must be one `wire_contract_for` yields for the phase's role and
output model, at BOTH profiles. A row naming only the `.direct.v1` id silently
refuses every compact seat.

    python -c "
    from deepreason.llm.wire import wire_contract_for
    from deepreason.llm.contracts import VariatorOutput   # the phase's model
    for profile in ('compact', 'standard', 'frontier'):
        print(profile, wire_contract_for('variator', VariatorOutput, profile).contract_id)
    "

A contract id this does not print is a NEW contract id. Priced stop.

## Step 3 — route the call through the shared bracket

`informal/trial.py::v6_transactional_phase_call` is the whole v6 provider
boundary: one durable preparation, a call-local context plan, one atomic issue,
and a typed provider/admission/terminal sequence. It takes
`task_payload_schema`, `trigger_prefix` and `reason_prefix` so the record says
truthfully which phase made the call while the work kind stays
`DEFENDED_TRIAL_STEP`.

The rule SELF-DETECTS the bound manifest; the scheduler's call to it stays
keyword-free (`DR-SEAM-scheduler-x-rules`'s invariant). Copy the shape from
`measures/hv.py::_v6_manifest` and `_sample_edits`, which is itself copied from
`informal/trial.py::_v6_trial_manifest` and `rules/crit.py`.

**The token-accounting rule is the part that is easy to get wrong.** Under v6
the transaction records the spend, so the call must NOT also reach `event.llm` —
`Harness.record_llm_calls`'s own docstring states it: every call reaches the log
exactly once, or replay and `eval_report` silently under-count. Return `None` in
place of the `LLMCall` and every downstream `record_measure(llm=…)` and
`record_llm_calls([…])` becomes correct with no edit.

## Step 4 — flip the row

    _row("<phase>", "<role>", _CONTRACTS, TRANSACTIONAL),

Nothing in `scheduler.py` changes. That is the point of the table: the gate is
already reading it.

## Step 5 — prove it, RED then GREEN

Three obligations, and the third is the one tranches forget.

1. **The phase now dispatches on a granted seat.** Extend
   `tests/test_hv_v6_reachability.py` — its `_plan`/`_manifest` helpers take any
   role and contract set — and move the phase out of the
   `test_an_unconverted_phase_defers_even_when_its_seat_holds_the_grant`
   parametrisation into a dispatch assertion.
2. **The phase still defers on an ungranted seat**, with the six-element marker
   tuple unchanged element by element. The record format is not yours to move.
3. **Mutation proof.** Flip the row back to `UNCONVERTED` and confirm the new
   test goes RED; delete the gate's consultation and confirm it goes RED. A test
   that passes under both is testing nothing.

Then the soak, which is where a real dispatch either works or does not:

    python -u scripts/cycle_soak.py --case hv-grant     # grant present
    python -u scripts/cycle_soak.py --case reach-rich   # the control

`hv-grant` is the only committed case whose `variator[0]` holds a behavioural
grant. A phase on a different role needs its own grant-bearing case, built the
same way: a committed config differing from its control in only the fields that
mint the grant, and a `SoakCase` that READS it.

## Step 6 — move the map in the same commit

`DR-SEAM-scheduler-x-workflow`'s `Traps` entry counts which phases still defer.
Rewrite it — never delete it — to say which one moved and when, and name the run
id or tranche. `DR-SUB-scheduler` and the subsystem owning the phase's own
module get the same treatment.

## What this recipe may NOT do

- **Convert more than one phase.** One per tranche.
- **Mint a contract, a work kind, or a payload schema replay validation must
  recognise.** Contact with `DR-INV-frozen-surfaces` surface 3. Priced stop,
  grant requested in FIX.md before a line of code.
- **Widen the grant compiler** so more seats get grants. That is
  `run_manifest.py`, surface 4, and the manifest's plan is RE-DERIVED and
  compared on every reload — so a compiler change invalidates every committed v6
  root on load. Reader-side is not merely preferred; it is the only road that
  does not break the corpus.
- **Convert a phase whose dispatch would change what counts as accepted,
  refuted, or warranted, without an operator ruling.** `hv-floor` is the worked
  example, and the way it was handled is the pattern: it mints a demonstrative
  fail warrant, and `rules/spawn.py` pins its criterion onto every connection
  problem, so converting it changes refutation outcomes. The tranche STOPPED,
  priced both roads, and the operator ruled it on
  (`experiments/2026-09-02-defect-hv-v6-reachability/` FIX.md §7 and §10:
  "It used to be on. And it's absolutely necessary. So switch it on. And you
  can test whether it works as intended"). Two obligations follow from that
  shape. Check the phase's own module for a `register_fail_warrant`, a
  `set_status`, or a warrant mint before you assume a phase is inert — and
  where you find one, the conversion owes tests that the phase still reaches
  every one of its verdicts correctly, not merely that the call dispatches.

`check: python -c "
from deepreason.workflow.legacy_phase_contracts import LEGACY_PHASE_CONTRACTS, TRANSACTIONAL
converted = [r.phase for r in LEGACY_PHASE_CONTRACTS.values() if r.dispatch == TRANSACTIONAL]
assert sorted(converted) == ['hv-floor', 'hv-spot-check'], converted
assert all(r.contract_ids for r in LEGACY_PHASE_CONTRACTS.values() if r.dispatch == TRANSACTIONAL)
assert len(LEGACY_PHASE_CONTRACTS) == 11, len(LEGACY_PHASE_CONTRACTS)
"`
`check: grep -q "def v6_transactional_phase_call\|^v6_transactional_phase_call = " src/deepreason/informal/trial.py && python -c "
import inspect
from deepreason.informal.trial import v6_transactional_phase_call as f
names = set(inspect.signature(f).parameters)
assert {'task_payload_schema', 'trigger_prefix', 'reason_prefix'} <= names, sorted(names)
"`
`check: python -c "
import ast, pathlib
tree = ast.parse(pathlib.Path('src/deepreason/scheduler/scheduler.py').read_text())
calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
         and isinstance(n.func, ast.Attribute)
         and n.func.attr == '_defer_untransactional_v6_phase']
assert len(calls) == 11, len(calls)
from deepreason.workflow.legacy_phase_contracts import LEGACY_PHASE_CONTRACTS
assert {c.args[0].value for c in calls} == set(LEGACY_PHASE_CONTRACTS)
"`
