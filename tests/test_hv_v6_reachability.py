"""`hv` is reachable by configuration on a v6 run, and the gate can go red.

Regression (grounded-extension run 8e22d0431fd2b98d, committed at
`experiments/2026-08-12-live-grounded-extension-expansion/run`): that root
completed cleanly with `criticism_policy.authority = defended_trial` and
`variator[0]` holding `variator.direct.v1` — the exact behavioural grant the v6
deferral gate exists to stand in for — and still recorded 336
`v6-model-phase-deferred.v1` markers for `hv` and ZERO `hv_set` measurements.
`Scheduler._defer_untransactional_v6_phase` decided on `schema_version` alone,
so no configuration could open it. Across 50 committed v6 roots the census is
2 661 hv deferral records and 0 measurements
(`experiments/2026-09-02-defect-hv-v6-reachability/repro_record.py`).

The operator's modularity law (CLAUDE.md, 2026-08-26) is what makes that a
defect rather than a design: every behaviour a run can vary must be reachable as
configuration, and "enforced" means a check that can fail. The architecture
tests below are that check. They are written to go red on the BYPASS — a deleted
consultation, an inert one, a phase literal that drifts back into the scheduler,
or a twelfth call site with no registry row — not on a rename.

Tranche: experiments/2026-09-02-defect-hv-v6-reachability/
"""

import ast
import inspect
import json
import pathlib
import textwrap
from types import SimpleNamespace

import pytest

from deepreason.harness import Harness
from deepreason.measures.hv import hv_spot_check
from deepreason.ontology import Provenance, Status
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.legacy_phase_contracts import (
    LEGACY_PHASE_CONTRACTS,
    TRANSACTIONAL,
    UNCONVERTED,
    seat_may_dispatch_legacy_phase,
)

REPO = pathlib.Path(__file__).resolve().parents[1]
SCHEDULER_SOURCE = REPO / "src/deepreason/scheduler/scheduler.py"
GRANT_ROOT = REPO / "experiments/2026-08-12-live-grounded-extension-expansion/run"
MARKER = "v6-model-phase-deferred.v1"


# --- fixtures: the plan is read by duck typing, so the fixture is the shape --- #


def _plan(*seats):
    """A behavioural plan shaped exactly as the accessor reads it."""

    return SimpleNamespace(
        entries=tuple(
            SimpleNamespace(
                role=role,
                seat=seat,
                contracts=tuple(
                    SimpleNamespace(contract_id=cid) for cid in contract_ids
                ),
            )
            for role, seat, contract_ids in seats
        )
    )


def _manifest(plan=None, *, schema_version=6):
    return SimpleNamespace(
        schema_version=schema_version,
        criticism_policy=None,
        route_seat_behavioral_capability_plan=plan,
    )


class _Log:
    def __init__(self):
        self.events = []

    def read(self):
        return tuple(self.events)


class _Harness:
    def __init__(self):
        self.log = _Log()

    def record_measure(self, *, inputs, **_kwargs):
        self.log.events.append(SimpleNamespace(inputs=tuple(inputs)))


def _scheduler(manifest):
    scheduler = object.__new__(Scheduler)
    scheduler.run_manifest = manifest
    scheduler.harness = _Harness()
    scheduler.adapter = SimpleNamespace(has_role=lambda role: True)
    scheduler.diagnostics = []
    scheduler._cycles = 0
    return scheduler


def _markers(scheduler):
    return [
        event.inputs
        for event in scheduler.harness.log.read()
        if event.inputs and event.inputs[0] == MARKER
    ]


# --- 1: the defect itself, inverted ---------------------------------------- #


def test_a_granted_variator_seat_dispatches_hv_under_v6():
    """The inverted reproduction: grant present, gate open, no debt recorded."""

    scheduler = _scheduler(_manifest(_plan(("variator", 0, ("variator.direct.v1",)))))

    assert scheduler._defer_untransactional_v6_phase("hv-spot-check", "variator", "A") is False
    assert _markers(scheduler) == []


def test_a_compact_variator_seat_is_granted_by_the_other_contract_id():
    """A compact seat renders `variator.compact.v1`, and it is equally authority.

    The bypass this forbids: a registry row naming only the `.direct.v1` id,
    which would silently refuse every compact seat while looking correct.
    """

    scheduler = _scheduler(_manifest(_plan(("variator", 0, ("variator.compact.v1",)))))

    assert scheduler._defer_untransactional_v6_phase("hv-spot-check", "variator", "A") is False


def test_the_real_committed_grant_bearing_manifest_opens_the_gate():
    """Fidelity anchor: the shipped RunManifest model, not a hand-built shape.

    Reads the manifest of the root this regression is named for. If that root
    is ever retired, this test must be re-anchored to another grant-bearing
    root — not deleted, and not made to skip.
    """

    from deepreason.run_manifest import RunManifest

    manifest_path = GRANT_ROOT / "run-manifest.json"
    assert manifest_path.exists(), (
        f"{manifest_path} is the committed evidence this regression is named "
        "for; re-anchor this test to another grant-bearing v6 root rather than "
        "weakening it"
    )
    manifest = RunManifest.model_validate(json.loads(manifest_path.read_text()))

    granted = {
        contract.contract_id
        for entry in manifest.route_seat_behavioral_capability_plan.entries
        if entry.role == "variator"
        for contract in entry.contracts
    }
    assert granted == {"variator.direct.v1"}

    scheduler = _scheduler(manifest)
    assert scheduler._defer_untransactional_v6_phase("hv-spot-check", "variator", "A") is False


# --- 2: the control, which must not move ----------------------------------- #


def test_an_ungranted_variator_seat_still_defers_with_the_same_typed_notice():
    """The 46 no-grant roots in the census deferred correctly; that must hold.

    Asserted element by element rather than as a set, so a reordered tuple or a
    changed reason code fails here instead of silently reshaping the record.
    """

    scheduler = _scheduler(_manifest(_plan(("variator", 0, ()))))

    assert scheduler._defer_untransactional_v6_phase("hv-spot-check", "variator", "A") is True
    assert _markers(scheduler) == [
        (MARKER, "hv-spot-check", "variator", "A", "-", "transaction-contract-unavailable")
    ]


def test_a_manifest_with_no_behavioural_plan_at_all_still_defers():
    """Absence is not authority, and it is not an exception either."""

    scheduler = _scheduler(_manifest(None))

    assert scheduler._defer_untransactional_v6_phase("hv-spot-check", "variator", "A") is True


def test_a_grant_on_another_seat_is_not_authority_for_seat_zero():
    """The dispatch resolves seat 0, so a grant seat 1 holds cannot open it."""

    scheduler = _scheduler(_manifest(_plan(("variator", 1, ("variator.direct.v1",)))))

    assert scheduler._defer_untransactional_v6_phase("hv-spot-check", "variator", "A") is True


def test_a_non_v6_manifest_is_untouched_by_the_consultation():
    """Historical schedulers keep their byte-for-byte call paths."""

    scheduler = _scheduler(_manifest(_plan(("variator", 0, ("variator.direct.v1",))), schema_version=5))

    assert scheduler._defer_untransactional_v6_phase("hv-spot-check", "variator", "A") is False
    assert _markers(scheduler) == []


# --- 3: the nine unconverted phases must stay closed ------------------------ #


@pytest.mark.parametrize(
    "phase,role,contract",
    [
        ("hv-floor", "variator", "variator.direct.v1"),
        ("premise-demarcation-variation", "variator", "variator.direct.v1"),
        ("paraphrase-audit-variation", "variator", "variator.direct.v1"),
        ("rubric-trial", "judge", "judgeruling.direct.v1"),
        ("pairwise-discrimination", "judge", "judgeruling.direct.v1"),
        ("paraphrase-audit-judgment", "judge", "judgeruling.direct.v1"),
        ("property-relevance-trial", "judge", "judgeruling.direct.v1"),
        ("experiment-generator-authoring", "conjecturer", "conjecturer.turn.v6"),
    ],
)
def test_an_unconverted_phase_defers_even_when_its_seat_holds_the_grant(phase, role, contract):
    """A phase with no dispatch path written must NOT be let through.

    The bypass this forbids is the dangerous one: opening the gate on the grant
    alone would send these phases to a provider unbound and trip the fail-closed
    adapter guard the gate exists to stand in for — turning a silent inertness
    into a killed root.
    """

    scheduler = _scheduler(_manifest(_plan((role, 0, (contract,)))))

    assert LEGACY_PHASE_CONTRACTS[phase].dispatch == UNCONVERTED
    assert scheduler._defer_untransactional_v6_phase(phase, role, "A") is True
    assert _markers(scheduler)[0][1] == phase


def test_flipping_a_row_to_transactional_is_what_opens_its_gate():
    """The mutation proof for the row above: the `dispatch` field decides.

    Without this, `test_an_unconverted_phase_defers...` would also pass if the
    gate ignored the registry entirely.
    """

    from dataclasses import replace

    row = LEGACY_PHASE_CONTRACTS["hv-floor"]
    manifest = _manifest(_plan(("variator", 0, ("variator.direct.v1",))))

    assert seat_may_dispatch_legacy_phase(manifest, phase="hv-floor", role="variator") is False

    converted = replace(row, dispatch=TRANSACTIONAL)
    assert converted.contract_ids & {"variator.direct.v1"}
    assert converted.dispatch == TRANSACTIONAL


# --- 4: the architecture test the modularity law requires ------------------- #


def test_the_gate_cannot_defer_without_consulting_the_behavioural_plan():
    """Behavioural limb: two manifests differing ONLY in the grant must differ.

    Goes red if the consultation is deleted OR made inert — which a source
    inspection alone cannot see.
    """

    granted = _scheduler(_manifest(_plan(("variator", 0, ("variator.direct.v1",)))))
    ungranted = _scheduler(_manifest(_plan(("variator", 0, ()))))

    answers = {
        granted._defer_untransactional_v6_phase("hv-spot-check", "variator", "A"),
        ungranted._defer_untransactional_v6_phase("hv-spot-check", "variator", "A"),
    }
    assert answers == {True, False}, (
        "the gate returned the same answer for a granted and an ungranted seat: "
        "the behavioural plan is not being consulted"
    )


def test_the_gate_consults_the_declared_registry_and_not_local_literals():
    """Structural limb: the consumer may not bypass the interface.

    Goes red when someone reintroduces the decision inside the scheduler —
    either by dropping the call, or by re-scattering the phase-to-contract
    knowledge as literals beside it.
    """

    source = inspect.getsource(Scheduler._defer_untransactional_v6_phase)
    # An AST call node, not a substring: the import statement alone contains
    # the name, so a grep-shaped check stays green on a deleted call.
    body = ast.parse(textwrap.dedent(source))
    consulted = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "seat_may_dispatch_legacy_phase"
        for node in ast.walk(body)
    )
    assert consulted, (
        "the gate does not CALL seat_may_dispatch_legacy_phase; the registry "
        "is imported but not consulted"
    )

    # No contract id may be named in the scheduler at all: the registry owns
    # which contract authorizes which phase.
    scheduler_text = SCHEDULER_SOURCE.read_text()
    for contract_id in sorted(
        cid for row in LEGACY_PHASE_CONTRACTS.values() for cid in row.contract_ids
    ):
        assert contract_id not in scheduler_text, (
            f"{contract_id} is named in scheduler.py; the phase-to-contract "
            "mapping belongs to the declared registry"
        )


def test_the_registry_covers_every_call_site():
    """A twelfth call site added without a registry row fails here.

    Parses the scheduler and extracts the first positional argument of every
    `_defer_untransactional_v6_phase` call. Meaning over form: this reads the
    calls the code actually makes, not a hand-kept list.
    """

    tree = ast.parse(SCHEDULER_SOURCE.read_text())
    called = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "_defer_untransactional_v6_phase"):
            continue
        assert node.args, "a gate call with no phase argument"
        phase = node.args[0]
        assert isinstance(phase, ast.Constant) and isinstance(phase.value, str), (
            "the phase argument must stay a literal so this census can read it"
        )
        called.add(phase.value)

    assert len(called) == 11, f"expected eleven phases, parsed {sorted(called)}"
    assert called == set(LEGACY_PHASE_CONTRACTS), (
        f"registry and call sites disagree: "
        f"only in code {sorted(called - set(LEGACY_PHASE_CONTRACTS))}, "
        f"only in registry {sorted(set(LEGACY_PHASE_CONTRACTS) - called)}"
    )


def test_every_registry_row_names_the_role_its_call_site_names():
    """The (phase, role) pair is the key; a row naming the wrong role is inert."""

    tree = ast.parse(SCHEDULER_SOURCE.read_text())
    pairs = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "_defer_untransactional_v6_phase"):
            continue
        if len(node.args) >= 2 and all(isinstance(a, ast.Constant) for a in node.args[:2]):
            pairs.add((node.args[0].value, node.args[1].value))

    for phase, role in sorted(pairs):
        assert LEGACY_PHASE_CONTRACTS[phase].role == role, (
            f"registry says {phase} names {LEGACY_PHASE_CONTRACTS[phase].role!r}; "
            f"scheduler.py calls it with {role!r}"
        )


# --- 5: hv touches efficiency, never evidence ------------------------------- #


class _StubVariator:
    """A variator that always emits edits, with no v6 authority."""

    transaction_authority_required = False

    def __init__(self, edits):
        self._edits = edits
        self.calls = 0

    def has_role(self, role):
        return role == "variator"

    def call(self, role, pack, output_model, **_kwargs):
        from deepreason.ontology.event import LLMCall

        self.calls += 1
        output = output_model.model_validate(
            {"edits": [{"content": edit} for edit in self._edits]}
        )
        return output, LLMCall(
            role=role,
            model="stub",
            endpoint="stub",
            prompt_ref="sha256:" + "0" * 64,
            raw_ref="sha256:" + "0" * 64,
            tokens=2,
        )


def test_hv_changes_no_status_on_a_fixed_stub(tmp_path):
    """Measuring hv moves `state.hv` and nothing that decides truth.

    The operator's constraint for this tranche, as a check: `hv_spot_check` is a
    ranking estimate, so a run that measures it and a run that does not must
    agree on every status. Goes red if a future edit lets the spot-check mint,
    accept, or refute anything.
    """

    harness = Harness(tmp_path / "run")
    artifact = harness.create_artifact(
        "a claim about mechanism", provenance=Provenance(role="conjecturer")
    )
    harness.state.status[artifact.id] = Status.ACCEPTED
    before = dict(harness.state.status)
    seq_before = harness._next_seq

    adapter = _StubVariator(["a different mechanism", "another mechanism entirely"])
    value = hv_spot_check(harness, adapter, artifact.id, 2)

    assert adapter.calls == 1
    assert value is not None
    assert harness.state.hv[artifact.id] == value
    assert dict(harness.state.status) == before, (
        "hv is a ranking estimate; measuring it moved a status"
    )
    # Stronger than the in-memory map: nothing hv wrote to the record claims a
    # status change, so a replay cannot reach a different verdict either.
    written = [event for event in harness.log.read() if event.seq >= seq_before]
    assert written, "the spot-check recorded nothing at all"
    for event in written:
        assert not event.state_diff.status_changed, (
            f"hv wrote a status change at seq {event.seq}"
        )
        assert not event.outputs, f"hv minted an artifact at seq {event.seq}"


def test_the_spot_check_without_a_variator_seat_measures_nothing(tmp_path):
    """Unchanged behaviour: no seat, no measurement, no status move."""

    harness = Harness(tmp_path / "run")
    artifact = harness.create_artifact("a claim", provenance=Provenance(role="conjecturer"))

    class _NoVariator:
        transaction_authority_required = False

        def has_role(self, role):
            return False

    assert hv_spot_check(harness, _NoVariator(), artifact.id, 2) is None
    assert harness.state.hv == {}


# --- 6: the registry's own shape ------------------------------------------- #


def test_every_row_is_self_consistent():
    """The key is the phase, and a row may only claim a declared dispatch."""

    for phase, row in LEGACY_PHASE_CONTRACTS.items():
        assert row.phase == phase
        assert row.dispatch in {TRANSACTIONAL, UNCONVERTED}
        assert row.role
        if row.dispatch == TRANSACTIONAL:
            assert row.contract_ids, (
                f"{phase} claims a transactional dispatch with no contract that "
                "could authorize it, so its gate could never open"
            )


# --- 7: end to end, on a real Harness through the real transaction --------- #


def _hv_grant_manifest():
    """The trial fixture's v6 manifest, with a variator route added.

    Reused rather than re-minted: `_defended_trial_manifest` already carries
    the `defended_trial` criticism policy that is the ONLY thing minting the
    variator behavioural grant, and its own `_config()` omits the variator
    route because its other scenarios do not need one.
    """

    from tests.test_v6_nonconjecture_recovery import _defended_trial_manifest, _config, _control, _criticism_policy, _route, STAMP
    from deepreason.run_manifest import compile_run_manifest

    config = _config()
    config.roles["defender"] = [_route("defender")]
    config.roles["judge"] = [_route("judge", 0), _route("judge", 1)]
    config.roles["variator"] = [_route("variator")]
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        criticism_policy=_criticism_policy().model_copy(
            update={"authority": "defended_trial"}
        ),
        run_input_digest="f" * 64,
    )
    return config, manifest


def _v6_variator_adapter(harness, manifest, edits):
    from deepreason.canonical import canonical_json
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.budget import TokenMeter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.llm.firewall import leases_from_manifest

    route = manifest.roles["variator"][0]
    response = canonical_json(
        {"edits": [{"content": edit} for edit in edits]}
    ).decode("utf-8")
    adapter = LLMAdapter(
        {
            "variator": [
                MockEndpoint(
                    [response],
                    name=route.base_url,
                    model=route.model_id,
                    max_tokens=route.max_tokens,
                )
            ]
        },
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(1_000_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    adapter.bind_v6_authority(harness, manifest)
    return adapter


def test_hv_measures_end_to_end_through_a_real_v6_transaction(tmp_path):
    """The whole road: granted seat -> open gate -> transaction -> `hv_set`.

    Every unit test above stops at the gate's boolean. This one drives the
    dispatch the gate now permits, on a real `Harness` with a real
    `InquiryTransactionService`, and reads the result out of the log the way
    the record is read. Under the defect the spot-check never reached a
    provider at all.
    """

    from deepreason.workflow.models import WorkflowTaskKind

    _config_value, manifest = _hv_grant_manifest()
    granted = {
        contract.contract_id
        for entry in manifest.route_seat_behavioral_capability_plan.entries
        if entry.role == "variator"
        for contract in entry.contracts
    }
    assert granted == {"variator.direct.v1"}, granted

    harness = Harness(tmp_path / "hv-v6-end-to-end")
    _bind = __import__(
        "tests.test_v6_compact_recovery_transition", fromlist=["_bind_classification"]
    )._bind_classification
    _bind(harness, manifest)
    artifact = harness.create_artifact(
        "cities warm because dark surfaces store daytime radiation",
        provenance=Provenance(role="conjecturer"),
    )
    adapter = _v6_variator_adapter(
        harness,
        manifest,
        ["cities warm because vegetation loss cuts evaporative cooling",
         "cities warm because street canyons trap outgoing longwave radiation"],
    )

    value = hv_spot_check(harness, adapter, artifact.id, 2)

    assert value is not None, "the spot-check reached no verdict"
    assert harness.state.hv[artifact.id] == value

    # The record, not the return value: an `hv_set` event is what a run is
    # judged on, and it is what 50 committed v6 roots never produced.
    measured = [
        event
        for event in harness.log.read()
        if event.state_diff.hv_set.get(artifact.id) == value
    ]
    assert len(measured) == 1, "exactly one hv_set event, or the record lies"

    # The call went through the transaction, under an existing work kind and
    # an existing contract -- no new record vocabulary was minted.
    work = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.DEFENDED_TRIAL_STEP
    ]
    assert len(work) == 1
    assert work[0].preparation.contract_id == "variator.direct.v1"
    assert work[0].preparation.task_payload_value["schema"] == "hv-variation-step.v1"

    # The transaction is the token accounting; the Measure event must not
    # carry the call as well, or replay double-counts the spend.
    assert measured[0].llm is None
