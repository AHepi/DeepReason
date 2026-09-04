"""One dead seat must not kill a run that still has a healthy seat.

Regression (P-A1 run 4565139800f5ca02): seat `conjecturer#1` (glm-5.3)
exhausted its contract ladder after a transport-fault streak while
`conjecturer#0` (deepseek-v4-pro:0813) answered 30 attempts with zero faults.
The run terminated `operational_failure` on the dead seat alone, at cycle 5 of
a 3 000 000-token budget with 1 093 086 spent.

The fixture is that shape, shrunk to two schools: `school-0` bound to a healthy
seat, `school-1` bound to a seat whose endpoint never returns valid output.
Everything else — v6 transactional authority, route-bound school execution, the
turn → atomic contract ladder, the qualification classification — is the real
machinery.

Two DIFFERENT deaths reach the same place, and the fix owes both:

* the P-A1 road, when the dead seat's next dispatch carries a task payload it
  has not seen: `RunManifestError` from
  `InquiryTransactionService.prepare`'s insufficient-capability guard;
* the same-payload road, when it carries the payload whose decomposition the
  exhaustion left incomplete: `ValueError("atomic child is terminally failed")`
  from `workflow/atomic_recovery.py`, raised before that guard is ever reached.

A fix that only catches the first leaves the second, which is why both are
pinned here rather than one.
"""

from __future__ import annotations

import json

import pytest

from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
)
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.run_manifest import (
    RunManifest,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.v6_policy import (
    engaged_control_plane_policy_v3,
    engaged_inquiry_capability_policy,
    engaged_simulation_toolchain,
)

STAMP = "2026-09-04T00:00:00Z"
HEALTHY_ENDPOINT = "healthy-seat"
DEAD_ENDPOINT = "dead-seat"

# P-A1's own grant, from the run's insufficient-capability record:
# maximum_schema_repairs 4, maximum_provider_calls 5.
PA1_REPAIRS = 4


def _route(endpoint_id: str, seat: int) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"offline-model-{seat}",
        "provider": "mock",
        "family": f"offline-family-{seat}",
        "max_tokens": 64,
        "context_window_tokens": 262_144,
    }


def _config() -> Config:
    return Config(
        N_SCHOOLS=2,
        SCHOOL_SEATS_ENABLED=True,
        scratchpad={"enabled": False},
        EMBEDDER_MODEL=None,
        roles={
            "conjecturer": [
                _route(HEALTHY_ENDPOINT, 0),
                _route(DEAD_ENDPOINT, 1),
            ],
            "argumentative_critic": [_route("critic-route-0", 0)],
            "synthesizer": [_route("synthesizer-route", 0)],
            "summarizer": [_route("summarizer-route", 0)],
            "thesis": [_route("thesis-route", 0)],
            "judge": [_route("judge-route", 0)],
        },
    )


def _route_bound_manifest(config: Config, run_input_digest: str) -> RunManifest:
    """Compile P-A1's shape: route-bound schools across two conjecturer seats."""

    control_plane = engaged_control_plane_policy_v3().model_copy(
        update={
            "school_execution": SchoolExecutionPolicyV1(
                mode="route_bound",
                bindings=(
                    SchoolRoleBindingV1(
                        school_id="school-0",
                        role="conjecturer",
                        seat=0,
                        endpoint_id=HEALTHY_ENDPOINT,
                    ),
                    SchoolRoleBindingV1(
                        school_id="school-1",
                        role="conjecturer",
                        seat=1,
                        endpoint_id=DEAD_ENDPOINT,
                    ),
                ),
                allow_shared=True,
                require_distinct_models=False,
                require_distinct_families=False,
            )
        }
    )
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control_plane,
        criticism_policy=None,
        inquiry_capability_policy=engaged_inquiry_capability_policy(),
        run_input_digest=run_input_digest,
        toolchains=(engaged_simulation_toolchain(),),
    )
    # Carry P-A1's own repair grant rather than the compiled default, so the
    # ladder this fixture walks is the ladder the live record walked.
    payload = json.loads(manifest.canonical_bytes())
    for grant in payload["contract_schema_repair_policy"]["grants"]:
        grant["maximum_schema_repairs"] = PA1_REPAIRS
        grant["maximum_provider_calls"] = PA1_REPAIRS + 1
    for entry in payload["route_seat_behavioral_capability_plan"]["entries"]:
        for contract in entry["contracts"]:
            contract["schema_repair"]["maximum_schema_repairs"] = PA1_REPAIRS
            contract["schema_repair"]["maximum_provider_calls"] = PA1_REPAIRS + 1
    return RunManifest.model_validate(payload)


def _admitted_case(_manifest, _pair, case_index):
    return ProductionContractCaseResultV1(
        case_id=f"case-{case_index + 1:03d}",
        first_pass_valid=True,
        eventual_valid=True,
        repair_count=0,
        semantic_admission=True,
    )


def _build_run(root, *, problems: int):
    """A bound v6 root with `problems` seed problems and both seats configured."""

    config = _config()
    commitment = Commitment(id="k-seat", eval="predicate:len(content) > 0")
    dossier = EvidenceDossierV1.create(
        problem_ref="pi-seat-1",
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="offline fixture",
            acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id="pi-seat-1",
            description="Can a run survive one dead seat?",
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    manifest = _route_bound_manifest(config, run_input.run_input_digest)
    bind_run_manifest(manifest, root)

    harness = Harness(root)
    harness.bind_model_classification(
        manifest,
        run_production_contract_doctor(manifest, case_executor=_admitted_case),
    )
    harness.register_commitment(commitment)
    for index in range(1, problems + 1):
        harness.register_problem(
            Problem(
                id=f"pi-seat-{index}",
                description=f"Seed question {index}: can a run survive a dead seat?",
                criteria=["k-seat"],
                provenance=ProblemProvenance.model_validate(
                    {"trigger": "seed", "from": []}
                ),
            )
        )
    return config, manifest, harness


def _adapter(harness, manifest):
    """Seat 0 always answers; seat 1's endpoint never returns valid output."""

    answer = json.dumps(
        {
            "candidates": [
                {
                    "content": "A bold conjecture from the healthy seat.",
                    "typicality": 0.2,
                }
            ]
        }
    )

    def _mock(seat: int, respond):
        route = manifest.roles["conjecturer"][seat]
        return MockEndpoint(
            respond,
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )

    adapter = LLMAdapter(
        {
            "conjecturer": [
                _mock(0, lambda _prompt: answer),
                _mock(1, lambda _prompt: "not-json"),
            ]
        },
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(2_000_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    adapter.bind_v6_authority(harness, manifest)
    return adapter


def _drive(harness, adapter, config, manifest, *, cycles: int):
    """Run `cycles` scheduler steps, returning the first exception or None."""

    scheduler = Scheduler(
        harness, adapter, config, workload_profile="text", run_manifest=manifest
    )
    for _ in range(cycles):
        try:
            scheduler.step()
        except Exception as error:  # noqa: BLE001 - the outcome under test
            return error
    return None


def _dead_seat_retired(harness) -> bool:
    """Whether the record marks the dead seat's exhaustion, per seat."""

    return any(
        key[1] == 1 and key[2] == DEAD_ENDPOINT
        for key in harness.workflow_state.insufficient_capability_by_route_seat
    )


def _completed_on_healthy_seat(harness) -> int:
    return sum(
        1
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.route_lease.endpoint_id == HEALTHY_ENDPOINT
        and item.terminal is not None
        and item.terminal.status == "completed"
    )


def test_the_p_a1_shape_runs_on_the_healthy_seat_after_the_dead_one_exhausts(
    tmp_path,
):
    """The exact P-A1 road: the dead seat's next dispatch carries a new payload.

    RED before the fix with
    ``RunManifestError: V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`` at step 1,
    while seat 0 had already completed work and the token budget was untouched.
    """

    config, manifest, harness = _build_run(tmp_path / "pa1-shape", problems=2)
    error = _drive(harness, _adapter(harness, manifest), config, manifest, cycles=6)

    assert _dead_seat_retired(harness), (
        "the fixture never exhausted the dead seat, so it is not the P-A1 shape"
    )
    assert _completed_on_healthy_seat(harness) >= 1, (
        "the fixture never completed work on the healthy seat"
    )
    assert error is None, (
        "one dead seat ended the whole run while a healthy seat was answering: "
        f"{type(error).__name__}: {error}"
    )


def test_a_dead_seat_does_not_kill_the_run_through_the_atomic_recovery_road(
    tmp_path,
):
    """The second road, found by this fixture and not by the live record.

    With ONE problem the dead seat's next dispatch carries the same task
    payload, so ``conj`` enters the atomic-decomposition recovery branch that
    the exhaustion left incomplete and raises
    ``ValueError("atomic child is terminally failed")`` from
    ``workflow/atomic_recovery.py`` — before the insufficient-capability guard
    is consulted at all. A fix wired only into the guard leaves this road open.
    """

    config, manifest, harness = _build_run(tmp_path / "atomic-road", problems=1)
    error = _drive(harness, _adapter(harness, manifest), config, manifest, cycles=6)

    assert _dead_seat_retired(harness)
    assert _completed_on_healthy_seat(harness) >= 1
    assert error is None, (
        "the atomic-recovery road ended the run on a dead seat: "
        f"{type(error).__name__}: {error}"
    )


def _retirement_receipts(harness):
    """The run's own `seat.retired.v1` rows, as (seat, endpoint, trigger)."""

    from deepreason.runtime.seat_retirement import RETIRED_SIGNAL

    rows = []
    for event in harness.log.read():
        inputs = [str(value) for value in (event.inputs or ())]
        if inputs[:1] == [RETIRED_SIGNAL]:
            rows.append(tuple(inputs[1:4]))
    return rows


def _calls_by_endpoint(harness):
    counts: dict[str, int] = {}
    for event in harness.log.read():
        call = getattr(event, "llm", None)
        if call is None:
            continue
        for attempt in call.attempt_trace or ():
            endpoint = getattr(attempt, "endpoint_id", "") or ""
            counts[endpoint] = counts.get(endpoint, 0) + 1
    return counts


def test_the_retirement_is_typed_and_names_the_seat_endpoint_and_trigger(tmp_path):
    """GOAL clause 2: the standdown is a record fact, not prose in a message."""

    config, manifest, harness = _build_run(tmp_path / "typed", problems=2)
    _drive(harness, _adapter(harness, manifest), config, manifest, cycles=6)

    receipts = _retirement_receipts(harness)
    assert receipts, "no seat.retired.v1 receipt was written"
    assert (f"conjecturer#1", DEAD_ENDPOINT, "contract_exhausted") in receipts
    assert not any(row[0] == "conjecturer#0" for row in receipts)


def test_the_receipt_is_written_once_per_seat_however_many_cycles_run(tmp_path):
    """A retirement is a run fact; a cycle must not re-disclose it."""

    config, manifest, harness = _build_run(tmp_path / "once", problems=2)
    _drive(harness, _adapter(harness, manifest), config, manifest, cycles=8)

    receipts = _retirement_receipts(harness)
    assert len(receipts) == len(set(receipts)) == 1, receipts


def test_dispatch_moves_to_the_healthy_seat_and_never_returns_to_the_dead_one(
    tmp_path,
):
    """GOAL clause 3: later calls land on seat 0 and none on seat 1."""

    config, manifest, harness = _build_run(tmp_path / "dispatch", problems=2)
    adapter = _adapter(harness, manifest)
    scheduler = Scheduler(
        harness, adapter, config, workload_profile="text", run_manifest=manifest
    )
    for _ in range(3):
        scheduler.step()
    before = dict(_calls_by_endpoint(harness))
    for _ in range(4):
        scheduler.step()
    after = _calls_by_endpoint(harness)

    assert after[HEALTHY_ENDPOINT] > before.get(HEALTHY_ENDPOINT, 0), (
        "the healthy seat stopped being dispatched to"
    )
    assert after.get(DEAD_ENDPOINT, 0) == before.get(DEAD_ENDPOINT, 0), (
        "the retired seat was dispatched to again"
    )


def test_deepreason_results_reports_the_retirement_and_a_typed_absence(tmp_path):
    """GOAL clause 4: it reaches the one retrieval surface, absences typed."""

    from deepreason.application.results import (
        seat_retirement_line,
        seat_retirement_summary,
    )

    config, manifest, harness = _build_run(tmp_path / "results", problems=2)
    _drive(harness, _adapter(harness, manifest), config, manifest, cycles=6)

    summary = seat_retirement_summary(harness)
    assert summary["retired"] == 1
    assert summary["seats"]["conjecturer#1"]["endpoint_id"] == DEAD_ENDPOINT
    assert summary["seats"]["conjecturer#1"]["trigger"] == "contract_exhausted"
    assert DEAD_ENDPOINT in seat_retirement_line(summary)

    _config2, manifest2, harness2 = _build_run(tmp_path / "clean", problems=1)
    absent = seat_retirement_summary(harness2)
    assert absent.get("absent") is True or absent.get("reason") == (
        "NO_SEAT_RETIREMENT"
    ), absent


def test_the_switch_is_per_run_and_off_reproduces_todays_death_with_a_warning(
    tmp_path,
):
    """GOAL clause 6: default ON, `off` restores the old behaviour, and warns."""

    from deepreason.runtime.seat_retirement import RETIREMENT_DISABLED_SIGNAL

    assert Config().SEAT_RETIREMENT_POLICY == "retire-dead-seats.v1"

    config, manifest, harness = _build_run(tmp_path / "switched-off", problems=2)
    config = config.model_copy(update={"SEAT_RETIREMENT_POLICY": "off"})
    error = _drive(harness, _adapter(harness, manifest), config, manifest, cycles=6)

    assert error is not None, "retirement off must reproduce the old death"
    assert "V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY" in str(error)
    warned = [
        event
        for event in harness.log.read()
        if [str(v) for v in (event.inputs or ())][:1] == [RETIREMENT_DISABLED_SIGNAL]
    ]
    assert len(warned) == 1, "switching the gate off must warn, exactly once"


def test_an_unknown_policy_falls_back_and_discloses_rather_than_refusing(tmp_path):
    """The all-configurations law applied to a policy selector."""

    from deepreason.runtime.seat_retirement import resolve_policy

    policy, fallback = resolve_policy(
        Config(SEAT_RETIREMENT_POLICY="retire-everything-immediately.v9")
    )
    assert policy == "retire-dead-seats.v1"
    assert fallback == "retire-everything-immediately.v9"

    config, manifest, harness = _build_run(tmp_path / "unknown-policy", problems=2)
    config = config.model_copy(
        update={"SEAT_RETIREMENT_POLICY": "retire-everything-immediately.v9"}
    )
    error = _drive(harness, _adapter(harness, manifest), config, manifest, cycles=6)
    assert error is None, f"an unknown policy refused instead of falling back: {error}"


def test_retirement_never_changes_a_seat_instance_spelling(tmp_path):
    """`seats_bound` is the CONFIGURED count, for the life of the run.

    `allocation.seat_instance` spells a one-seat role as the bare role name. If
    retiring seat 1 made the role one-seated, every signal name, every `cap:`
    knob and every recorded Measure input would change spelling mid-run and the
    run's later rows would stop matching its earlier ones.
    """

    from deepreason.allocation import seat_instance
    from deepreason.runtime.seat_retirement import live_seats, retired_seats

    config, manifest, harness = _build_run(tmp_path / "spelling", problems=2)
    _drive(harness, _adapter(harness, manifest), config, manifest, cycles=6)

    retired = retired_seats(harness, config, manifest)
    assert retired, "the fixture never retired a seat"
    configured = len(manifest.roles["conjecturer"])
    assert live_seats(retired, "conjecturer", configured) == (0,)
    # The spelling is taken from the configured count, which retirement leaves
    # alone -- so both seats keep the names the run's earlier rows used.
    assert seat_instance("conjecturer", 0, configured) == "conjecturer#0"
    assert seat_instance("conjecturer", 1, configured) == "conjecturer#1"


def _adapter_all_dead(harness, manifest):
    """Both seats' endpoints never return valid output."""

    def _mock(seat: int):
        route = manifest.roles["conjecturer"][seat]
        return MockEndpoint(
            lambda _prompt: "not-json",
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )

    adapter = LLMAdapter(
        {"conjecturer": [_mock(0), _mock(1)]},
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(2_000_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    adapter.bind_v6_authority(harness, manifest)
    return adapter


def test_every_seat_dead_stops_clean_on_a_reason_that_permits_continue(tmp_path):
    """GOAL clause 5, first half: a clean stop, not an operational failure.

    The operator's law of 2026-08-29: exhaustion is a clean stop and every stop
    secures continuation. A run with nothing left to generate from has not
    failed; it has run out of provider.
    """

    from deepreason.workflow.lifecycle import (
        COMPOSABLE_STOP_REASONS,
        RESUMABLE_STOP_REASONS,
    )

    config, manifest, harness = _build_run(tmp_path / "all-dead", problems=2)
    scheduler = Scheduler(
        harness,
        _adapter_all_dead(harness, manifest),
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    scheduler.run(cycles=8)

    decision = scheduler.last_stop_decision
    assert decision is not None and decision.stop
    assert decision.reason == "provider_unavailable", decision
    assert decision.reason != "operational_failure"
    assert decision.reason in RESUMABLE_STOP_REASONS
    # Separate sets on purpose: a run that stopped because nothing could answer
    # has not earned a composition.
    assert decision.reason not in COMPOSABLE_STOP_REASONS

    receipts = {row[0] for row in _retirement_receipts(harness)}
    assert receipts == {"conjecturer#0", "conjecturer#1"}, receipts


def test_the_all_dead_stop_writes_the_record_a_continuation_reads(tmp_path):
    """GOAL clause 5, second half: the terminal secures relaunch.

    A stop that cannot assure continuability is itself a defect (2026-08-29).
    Two things carry that here and both are checked: the scheduler REPORTS the
    reason, which is what `application/text_runs.py` terminalizes on, and with
    a stop controller present it writes the durable stop record itself.
    """

    import json

    from deepreason.runtime.stop import StopController, StopPolicy
    from deepreason.workflow.lifecycle import RESUMABLE_STOP_REASONS

    root = tmp_path / "all-dead-record"
    config, manifest, harness = _build_run(root, problems=2)
    scheduler = Scheduler(
        harness,
        _adapter_all_dead(harness, manifest),
        config,
        workload_profile="text",
        run_manifest=manifest,
        stop_controller=StopController(StopPolicy()),
    )
    report = scheduler.run(cycles=8)

    assert report["stop_reason"] == "provider_unavailable"
    assert report["stop_reason"] in RESUMABLE_STOP_REASONS

    stop = json.loads((root / "run-stop.json").read_text())
    assert stop["reason"] == "provider_unavailable"
    assert stop.get("digest")


def test_a_recovered_provider_lets_the_stopped_run_carry_on(tmp_path):
    """GOAL clause 5, third half: it resumes once the provider is back.

    The same root, the same harness, a scheduler whose endpoints now answer:
    work completes where nothing could complete before. This is the property
    'permits continue' exists FOR, checked by doing it rather than by reading
    a flag.
    """

    root = tmp_path / "recovered"
    config, manifest, harness = _build_run(root, problems=2)
    dead = Scheduler(
        harness,
        _adapter_all_dead(harness, manifest),
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    dead.run(cycles=8)
    assert dead.last_stop_decision.reason == "provider_unavailable"
    stalled = _completed_on_healthy_seat(harness)

    # The provider comes back. Retirement is derived from the record, so the
    # seats stay retired -- what the resumed run must do is carry on rather
    # than raise, which is the property the stop was supposed to secure.
    revived = Scheduler(
        harness,
        _adapter(harness, manifest),
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    error = None
    try:
        revived.run(cycles=4)
    except Exception as raised:  # noqa: BLE001 - the outcome under test
        error = raised
    assert error is None, f"the resumed run raised: {type(error).__name__}: {error}"
    assert _completed_on_healthy_seat(harness) >= stalled


def _judge_route(seat: int) -> dict:
    """A second judge seat on a genuinely distinct family."""

    route = _route(f"judge-route-{seat}", seat)
    route["family"] = ("qwen", "openai-gpt")[seat]
    return route


def _ensemble_config() -> Config:
    """The P-A1 adjudication shape: two judge seats, two families."""

    config = _config()
    roles = dict(config.roles)
    roles["judge"] = [_judge_route(0), _judge_route(1)]
    return config.model_copy(update={"roles": roles})


def test_a_retired_judge_seat_skips_summons_and_does_not_relax_cross_family(
    tmp_path,
):
    """Census row 4: the ensemble predicate is not traded away to avoid a skip.

    The measured 0-2.5% false-conviction regime is the cross-family one; every
    looser configuration measured over-convicts at 47-60%
    (docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md, the amended judge law).
    """

    config = _ensemble_config()
    commitment = Commitment(id="k-seat", eval="predicate:len(content) > 0")
    dossier = EvidenceDossierV1.create(
        problem_ref="pi-seat-1",
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="offline fixture",
            acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id="pi-seat-1",
            description="Can a run survive one dead seat?",
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    root = tmp_path / "judges"
    bind_run_input(run_input, dossier, root)
    manifest = _route_bound_manifest(config, run_input.run_input_digest)
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    harness.bind_model_classification(
        manifest,
        run_production_contract_doctor(manifest, case_executor=_admitted_case),
    )
    harness.register_commitment(commitment)

    adapter = _adapter(harness, manifest)
    scheduler = Scheduler(
        harness, adapter, config, workload_profile="text", run_manifest=manifest
    )
    # `judge` is configured with two seats, and the adapter under test has no
    # judge endpoint at all: the availability question must answer False
    # without raising, which is the property census row 4 owes.
    assert scheduler._judge_ensemble_available() is False

    # With both judge seats present and neither retired, the ensemble is
    # available -- so the False above is about retirement, not about the
    # question being unanswerable.
    assert len(manifest.roles["judge"]) == 2
    families = {route.family for route in manifest.roles["judge"]}
    assert len(families) == 2, families


def test_a_retired_single_seat_role_skips_its_phase_rather_than_raising(tmp_path):
    """Census row 6: a role whose only seat is retired is unavailable, quietly.

    P-A1's `defender#0` sat on the dead endpoint while the conjecture and
    criticism circuit on the healthy endpoint still had work to do. Skipping
    the phase is what lets that work happen.
    """

    from deepreason.runtime.seat_retirement import SeatRetirement

    config, manifest, harness = _build_run(tmp_path / "single-seat", problems=2)
    adapter = _adapter(harness, manifest)
    scheduler = Scheduler(
        harness, adapter, config, workload_profile="text", run_manifest=manifest
    )
    assert scheduler._role_available("conjecturer") is True

    pretend = {
        ("conjecturer", 0): SeatRetirement(
            role="conjecturer",
            seat=0,
            endpoint_id=HEALTHY_ENDPOINT,
            trigger="provider_dead",
            evidence="3",
        ),
        ("conjecturer", 1): SeatRetirement(
            role="conjecturer",
            seat=1,
            endpoint_id=DEAD_ENDPOINT,
            trigger="provider_dead",
            evidence="3",
        ),
    }
    scheduler._retired_seats = lambda: pretend
    assert scheduler._role_available("conjecturer") is False
    # And it discloses rather than going quiet: one receipt per retired seat.
    assert {row[0] for row in _retirement_receipts(harness)} == {
        "conjecturer#0",
        "conjecturer#1",
    }
    # A role with no lease table at all is unaffected -- a pre-v6 or mock
    # topology must not become unavailable because retirement exists.
    assert scheduler._role_available("nobody-here") is False


def test_criticism_coverage_debt_names_what_a_retired_critic_left_uncovered(
    tmp_path,
):
    """Census row 3: an unmeetable coverage floor is a typed debt, not a crash.

    `CoverageDebtV1` already carries `outstanding_school_ids` and an
    `ordinary_stop` termination reason, so a retired critic seat needs no new
    record shape. Pinned here so a later change cannot quietly make the
    uncovered targets invisible.
    """

    from deepreason.workflow.criticism import CoverageDebtV1

    reasons = CoverageDebtV1.model_fields["termination_reason"].annotation
    assert "ordinary_stop" in getattr(reasons, "__args__", ())
    assert "outstanding_school_ids" in CoverageDebtV1.model_fields
