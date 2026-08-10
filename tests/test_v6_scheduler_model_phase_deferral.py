from types import SimpleNamespace

import pytest

import deepreason.scheduler.scheduler as scheduler_module
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.measures.hv import HV_FLOOR_PROGRAM
from deepreason.ontology import Problem, ProblemProvenance, Provenance, Status
from deepreason.oracle import PROPERTY_PROGRAM
from deepreason.scheduler.scheduler import Scheduler
from tests.test_v6_compact_recovery_transition import _bind_classification
from tests.test_v6_transaction_qualification import _manifest


class _Log:
    def __init__(self):
        self.events = []

    def read(self):
        return tuple(self.events)


class _Harness:
    def __init__(self):
        self.log = _Log()
        self.commitments = {}
        self.state = SimpleNamespace(
            artifacts={},
            problems={},
            status={},
            addr=set(),
            hv={},
        )

    def record_measure(self, *, inputs, **_kwargs):
        self.log.events.append(SimpleNamespace(inputs=tuple(inputs)))


class _Adapter:
    def __init__(self, roles=()):
        self.roles = set(roles)

    def has_role(self, role):
        return role in self.roles


def _scheduler(*, schema_version=6, roles=()):
    scheduler = object.__new__(Scheduler)
    scheduler.run_manifest = SimpleNamespace(
        schema_version=schema_version,
        criticism_policy=None,
    )
    scheduler.harness = _Harness()
    scheduler.adapter = _Adapter(roles)
    scheduler.diagnostics = []
    scheduler._cycles = 0
    return scheduler


def _markers(scheduler):
    return [
        event.inputs
        for event in scheduler.harness.log.read()
        if event.inputs[0] == "v6-model-phase-deferred.v1"
    ]


def test_v6_scheduler_rejects_an_unguarded_adapter_before_work():
    harness = _Harness()
    with pytest.raises(WorkflowAuthorizationError, match="global transaction"):
        Scheduler(
            harness,
            _Adapter({"conjecturer"}),
            Config(N_SCHOOLS=0),
            run_manifest=SimpleNamespace(schema_version=6),
        )
    assert harness.log.events == []


def test_v6_deferral_marker_is_durable_bounded_and_resume_deduplicated():
    scheduler = _scheduler()

    assert scheduler._defer_untransactional_v6_phase(
        "phase", "role", "target", "obligation"
    )
    del scheduler._v6_deferred_model_phases
    assert scheduler._defer_untransactional_v6_phase(
        "phase", "role", "target", "obligation"
    )

    assert _markers(scheduler) == [
        (
            "v6-model-phase-deferred.v1",
            "phase",
            "role",
            "target",
            "obligation",
            "transaction-contract-unavailable",
        )
    ]
    assert len(scheduler.diagnostics) == 1


def test_legacy_scheduler_keeps_ordinary_argumentative_dispatch(monkeypatch):
    scheduler = _scheduler(schema_version=5, roles={"argumentative_critic"})
    scheduler.config = SimpleNamespace(
        ARG_CRIT_PER_CYCLE=None,
        RECRIT_STANDING=False,
        CRIT_BATCH_K=None,
    )
    scheduler._arg_crit_this_cycle = 0
    scheduler.harness.state.status["A"] = Status.ACCEPTED
    calls = []
    monkeypatch.setattr(
        scheduler_module,
        "crit_argumentative_batch",
        lambda _harness, targets, _adapter, _config: calls.append(tuple(targets)),
    )

    scheduler._arg_crit(["A"])

    assert calls == [("A",)]
    assert _markers(scheduler) == []


def test_v6_criterion_model_checks_defer_without_dispatch(monkeypatch):
    scheduler = _scheduler()
    scheduler.config = SimpleNamespace()
    scheduler.embedder = None
    target = SimpleNamespace(
        id="A",
        interface=SimpleNamespace(commitments=("hv", "rubric")),
    )
    scheduler.harness.commitments = {
        "hv": SimpleNamespace(id="hv", eval=f"program:{HV_FLOOR_PROGRAM}"),
        "rubric": SimpleNamespace(id="rubric", eval="rubric:quality"),
    }
    scheduler.harness.state.status["A"] = Status.ACCEPTED
    monkeypatch.setattr(scheduler_module, "crit_program", lambda *_args: None)
    monkeypatch.setattr(scheduler_module, "crit_fuzz", lambda *_args: None)
    monkeypatch.setattr(
        scheduler_module,
        "run_hv_floor",
        lambda *_args: pytest.fail("unbound v6 variator dispatched"),
    )

    scheduler._criticize(target)

    assert {marker[1] for marker in _markers(scheduler)} == {
        "hv-floor",
        "rubric-trial",
    }


def test_v6_experiment_and_property_design_defer_before_provider(monkeypatch):
    scheduler = _scheduler(roles={"conjecturer", "property_designer", "judge"})
    scheduler.config = SimpleNamespace(
        GEN_PROPOSE_PERIOD=1,
        GEN_MAX=1,
        PROP_PROPOSE_PERIOD=1,
        PROP_MAX=1,
        FUZZ_N=1,
    )
    problem = SimpleNamespace(id="P", criteria=("C",))
    scheduler.harness.state.problems = {"P": problem}
    scheduler.harness.commitments = {
        "C": SimpleNamespace(id="C", eval=f"program:{PROPERTY_PROGRAM}")
    }
    scheduler._fuzz_clean = set()
    import deepreason.rules.experiment as experiment

    monkeypatch.setattr(experiment, "accepted_generators", lambda *_args: [])
    monkeypatch.setattr(experiment, "active_properties", lambda *_args: [])
    monkeypatch.setattr(
        experiment,
        "propose_generators",
        lambda *_args: pytest.fail("unbound v6 generator authoring dispatched"),
    )
    monkeypatch.setattr(
        experiment,
        "propose_properties",
        lambda *_args: pytest.fail("unbound v6 property authoring dispatched"),
    )

    scheduler._experiment_step()
    scheduler._property_step()

    assert {marker[1] for marker in _markers(scheduler)} == {
        "experiment-generator-authoring",
        "property-design",
        "property-relevance-trial",
    }


def test_v6_audit_vision_and_lazy_hv_defer_without_dispatch(monkeypatch):
    scheduler = _scheduler(roles={"judge", "variator", "vision_critic"})
    scheduler._cycles = 1
    scheduler.config = SimpleNamespace(
        AUDIT_PERIOD=1,
        VISION_CRIT_PER_CYCLE=1,
        HV_CONTENT_MAX_CHARS=None,
        HV_K=3,
    )
    scheduler._vision_done = set()
    scheduler._hv_skipped = set()
    scheduler.embedder = None
    scheduler.harness.state.artifacts = {"A": SimpleNamespace()}
    scheduler.harness.state.status = {"A": Status.ACCEPTED}
    scheduler.harness.state.addr = {("A", "P")}

    import deepreason.informal.audits as audits
    import deepreason.rules.act as act
    import deepreason.rules.vision as vision

    monkeypatch.setattr(
        audits,
        "paraphrase_invariance_audit",
        lambda *_args: pytest.fail("unbound v6 audit dispatched"),
    )
    monkeypatch.setattr(act, "browser_evidence", lambda *_args: (object(),))
    monkeypatch.setattr(
        vision,
        "crit_vision",
        lambda *_args: pytest.fail("unbound v6 vision critic dispatched"),
    )
    monkeypatch.setattr(
        scheduler_module,
        "hv_spot_check",
        lambda *_args: pytest.fail("unbound v6 HV spot-check dispatched"),
    )

    scheduler._audit_step()
    scheduler._vision_step()
    scheduler._lazy_hv()

    assert {marker[1] for marker in _markers(scheduler)} == {
        "paraphrase-audit-variation",
        "paraphrase-audit-judgment",
        "vision-criticism",
        "hv-spot-check",
    }


def test_v6_pairwise_discrimination_never_reaches_unbound_judge(tmp_path, monkeypatch):
    harness = Harness(tmp_path / "run")
    manifest = _manifest()
    _bind_classification(harness, manifest)
    first = harness.create_artifact(
        "rival A", provenance=Provenance(role="conjecturer")
    )
    second = harness.create_artifact(
        "rival B", provenance=Provenance(role="conjecturer")
    )
    problem = harness.register_problem(
        Problem(
            id="disc:rivals",
            description="discriminate the rivals",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "discrimination", "from": [first.id, second.id]}
            ),
        )
    )
    adapter = LLMAdapter(
        {
            "judge": MockEndpoint(
                lambda _prompt: pytest.fail("unbound v6 pairwise judge dispatched")
            )
        },
        harness.blobs,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    scheduler = Scheduler(
        harness,
        adapter,
        Config(N_SCHOOLS=0, FUZZ_N=0, ADVISORY_TRIALS_PER_CYCLE=1),
        workload_profile="text",
        run_manifest=manifest,
    )
    monkeypatch.setattr(scheduler, "_simulation_capability_step", lambda: False)

    scheduler.step()

    assert not [event for event in harness.log.read() if event.llm]
    marker = next(
        event.inputs
        for event in harness.log.read()
        if event.inputs[:2]
        == ["v6-model-phase-deferred.v1", "pairwise-discrimination"]
    )
    assert marker[2:] == [
        "judge",
        problem.id,
        f"{first.id}|{second.id}",
        "transaction-contract-unavailable",
    ]


def test_critic_execution_permits_endpoint_only_dispatch():
    """S13h: an endpoint-only call (no school) is a valid combination now,
    distinct from the pre-existing school-routed and no-envelope cases."""

    from deepreason.llm.firewall import EndpointLease, Route
    from deepreason.rules.crit import _critic_execution

    lease = EndpointLease(
        role="argumentative_critic",
        seat=0,
        route=Route(
            endpoint_id="critic-mock-0",
            base_url="mock://legacy",
            model_id="model-legacy",
            provider="mock",
            family="legacy",
            max_tokens=64,
            context_window_tokens=1024,
        ),
    )

    call_kwargs, prefix = _critic_execution(
        endpoint_lease=lease,
        critic_school_id=None,
        critic_school_context=None,
    )

    assert call_kwargs == {
        "endpoint_index": 0,
        "endpoint_lease": lease,
        "school_id": None,
    }
    assert prefix == ""

    with pytest.raises(ValueError, match="school-routed criticism requires"):
        _critic_execution(
            endpoint_lease=lease,
            critic_school_id="school-0",
            critic_school_context=None,
        )


def test_llm_adapter_exposes_bound_v6_manifest(tmp_path):
    """S13i-1: crit.py's self-detection needs a read-only accessor for the
    manifest Scheduler.__init__ already binds via bind_v6_authority."""

    harness = Harness(tmp_path / "bound-v6-manifest-accessor")
    manifest = _manifest()
    _bind_classification(harness, manifest)
    adapter = LLMAdapter(
        {"argumentative_critic": MockEndpoint(lambda _prompt: "")},
        harness.blobs,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )

    assert adapter.bound_v6_manifest() is None

    adapter.bind_v6_authority(harness, manifest)

    assert adapter.bound_v6_manifest() is manifest


def test_legacy_argumentative_criticism_dispatches_under_v6(monkeypatch):
    """S13i-3 (corrected Step 3): v6 + no school criticism_policy must no
    longer defer — crit_argumentative_batch self-detects v6-ness via the
    adapter's bound manifest and dispatches live, with the scheduler's own
    call staying keyword-free (SEAM-scheduler-x-rules.md's checked
    invariant: the scheduler never chooses a prose authority)."""

    scheduler = _scheduler(roles={"argumentative_critic"})
    scheduler.config = SimpleNamespace(
        ARG_CRIT_PER_CYCLE=None,
        RECRIT_STANDING=False,
        CRIT_BATCH_K=None,
    )
    scheduler._arg_crit_this_cycle = 0
    scheduler.harness.state.status["A"] = Status.ACCEPTED
    calls = []
    monkeypatch.setattr(
        scheduler_module,
        "crit_argumentative_batch",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    scheduler._arg_crit(["A"])

    assert calls == [((scheduler.harness, ["A"], scheduler.adapter, scheduler.config), {})]
    assert _markers(scheduler) == []
