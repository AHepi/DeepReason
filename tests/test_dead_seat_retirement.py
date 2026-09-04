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
