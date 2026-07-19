"""Minimized, incident-linked A1/A2/A3 verification regressions.

The original Wave A roots are intentionally not reconstructed or represented
as present.  These dependency-complete descriptors build small *derived*
RunManifest-v5 roots that isolate the incident mechanisms documented in the
available review, then exercise the production ``verify_root_report`` adapter.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from deepreason.application.models import RunResultV2
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json
from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.policy import (
    InquiryCapabilityPolicyV1,
    SimulationCapabilityPolicyV1,
)
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV1,
    RunInputProblemV1,
    bind_run_input,
)
from deepreason.evidence.dossier import (
    commit_dossier_pack_receipt,
    pack_dossier,
)
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Problem, ProblemProvenance, Provenance
from deepreason.rules.conj import conj
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV2,
    ControlPlanePolicyV2,
    CriticismPolicyV1,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    ToolchainEntry,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.verification.report import verify_root_report


INCIDENT_ID = "DR-2026-07-16-AUTONOMOUS-INQUIRY-WAVE-A"
INCIDENT_REVIEW_SHA256 = (
    "2f086397643e439dd711d656611f943a3edbb3327672faf81f16ea40d6ebf282"
)
INCIDENT_HEAD = "056af85e4c6018bcdf44e73c2ada78fabccb4a81"
FIXTURE_DIR = (
    Path(__file__).parent
    / "fixtures"
    / "incidents"
    / INCIDENT_ID
)
FIXTURE_IDS = ("A1", "A2", "A3")
COMPILED_AT = "2026-07-16T00:00:00Z"


class _FrozenEventDateTime(datetime):
    """Fixed event clock for byte-stable generated fixture roots."""

    @classmethod
    def now(cls, tz=None):
        return cls(2026, 7, 16, 12, 47, 0, tzinfo=tz)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _descriptor(fixture_id: str) -> dict:
    return _read_json(FIXTURE_DIR / f"{fixture_id}.json")


def _route(endpoint_id: str, seat: int) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"incident-fixture-model-{seat}",
        "provider": "mock",
        "family": f"incident-fixture-family-{seat}",
        "max_tokens": 1_024,
    }


def _control() -> ControlPlanePolicyV2:
    return ControlPlanePolicyV2(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="disabled",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=(),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV2(),
    )


def _criticism(minimum: int) -> CriticismPolicyV1:
    return CriticismPolicyV1(
        minimum_foreign_school_coverage=minimum,
        bindings=tuple(
            SchoolRoleBindingV1(
                school_id=f"school-{seat}",
                role="argumentative_critic",
                seat=seat,
                endpoint_id=f"critic-{seat}",
            )
            for seat in range(3)
        ),
        max_batch_size=4,
        target_eligibility="accepted_school_artifacts",
        authority="observe_only",
        allow_shared=False,
    )


def _simulation_authority() -> tuple[InquiryCapabilityPolicyV1, ToolchainEntry]:
    # This toolchain is never invoked.  Its stable, unavailable identity makes
    # the fixture cross-machine deterministic while retaining a valid frozen
    # proposal authority for the PROPOSED-only A3 prefix.
    toolchain = ToolchainEntry(
        id="python@incident-derived-fixture",
        runner="local",
        executable="/deepreason/derived-fixture/python",
        version_output_sha256=hashlib.sha256(
            b"deepreason-incident-derived-fixture-python"
        ).hexdigest(),
        network=False,
    )
    simulation = SimulationCapabilityPolicyV1(
        enabled=True,
        runner_profile="simulation.declarative.v1",
        python_toolchain_identity=toolchain.id,
        maximum_simulation_requests=1,
        maximum_simulation_executions=1,
        maximum_proposals_per_turn=1,
        maximum_generated_code_bytes=16_384,
        maximum_input_bytes=16_384,
        maximum_output_bytes=16_384,
        maximum_wall_ms=10_000,
        maximum_memory_bytes=256 * 1024 * 1024,
        maximum_steps=50_000,
        maximum_samples=32,
        deterministic_seed_policy="fixed_manifest",
        fixed_seed_set=(7,),
        maximum_follow_up_reasoning_turns=1,
        retry_ceiling=0,
    )
    return InquiryCapabilityPolicyV1(simulation=simulation), toolchain


def _write_terminal(root: Path, payload: dict) -> None:
    if payload.get("schema") == "deepreason-run-result-v2":
        payload = RunResultV2.model_validate(payload).model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
    (root / "run-result.json").write_bytes(canonical_json(payload) + b"\n")


def _build_derived_root_at_frozen_time(root: Path, descriptor: dict) -> Harness:
    problem = descriptor["problem"]
    reproductions = descriptor["reproductions"]
    provenance = AttachedSourceProvenanceV1(
        supplied_by="incident review linked by SHA-256",
        acquisition_method="minimized derived reconstruction",
        note="This is not an original Wave A run root.",
    )
    dossier = EvidenceDossierV1.create(
        problem_ref=problem["id"],
        sources=(),
        total_byte_count=0,
        creation_provenance=provenance,
    )
    run_input = RunInputManifestV1.create(
        problem=RunInputProblemV1(**problem),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)

    config = Config(
        N_SCHOOLS=3,
        CONTROLLER=False,
        RETRY_MAX=0,
        roles={
            "conjecturer": _route("conjecturer-0", 0),
            "argumentative_critic": [
                _route(f"critic-{seat}", seat + 1) for seat in range(3)
            ],
        },
    )
    criticism_minimum = reproductions.get(
        "criticism_minimum_foreign_school_coverage"
    )
    manifest_values = {
        "schema_version": descriptor["manifest_schema_version"],
        "workload_profile": "text",
        "rubric_policy": "forbid",
        "compiled_at": COMPILED_AT,
        "control_plane_policy": _control(),
        "run_input_digest": run_input.run_input_digest,
    }
    if criticism_minimum is not None:
        manifest_values["criticism_policy"] = _criticism(criticism_minimum)
    if "simulation_proposal" in reproductions:
        capability_policy, toolchain = _simulation_authority()
        manifest_values["inquiry_capability_policy"] = capability_policy
        manifest_values["toolchains"] = (toolchain,)
    manifest = compile_run_manifest(config, **manifest_values)
    bind_run_manifest(manifest, root)

    harness = Harness(root)
    harness.register_problem(
        Problem(
            id=problem["id"],
            description=problem["description"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )

    if "simulation_proposal" in reproductions:
        route = manifest.roles["conjecturer"][0]
        adapter = LLMAdapter(
            {
                "conjecturer": MockEndpoint(
                    [
                        json.dumps(
                            {
                                "simulation_proposals": [
                                    reproductions["simulation_proposal"]
                                ]
                            },
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                    ],
                    name=route.base_url,
                    model=route.model_id,
                    max_tokens=route.max_tokens,
                )
            },
            harness.blobs,
            retry_max=0,
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
        )
        assert conj(
            harness,
            problem["id"],
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        ) == []

    survivor = reproductions.get("accepted_survivor")
    if survivor is not None:
        harness.create_artifact(
            survivor["claim"],
            provenance=Provenance(
                role="conjecturer", school=survivor["owner_school_id"]
            ),
        )

    orphan = reproductions.get("orphan_exposure")
    if orphan is not None:
        receipt = pack_dossier(
            root=root,
            run_input=run_input,
            dossier=dossier,
            work_order_ref=orphan["work_order_ref"],
            query=orphan["query"],
            state_fence=orphan["state_fence"],
            maximum_sources=1,
            maximum_excerpt_bytes_per_source=1,
            maximum_total_excerpt_bytes=1,
        )
        commit_dossier_pack_receipt(harness, receipt)

    terminal = reproductions.get("terminal") or reproductions[
        "derived_audit_terminal"
    ]
    _write_terminal(root, terminal)
    return harness


def _build_derived_root(root: Path, descriptor: dict) -> Harness:
    with (
        patch("deepreason.harness.datetime", _FrozenEventDateTime),
        patch("deepreason.llm.adapter.time.monotonic", return_value=100.0),
    ):
        return _build_derived_root_at_frozen_time(root, descriptor)


def _root_digest(root: Path) -> str:
    files = []
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        payload = path.read_bytes()
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }
        )
    return hashlib.sha256(canonical_json(files)).hexdigest()


def _checks(findings) -> list[str]:
    return [finding.check for finding in findings]


@pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
def test_incident_derived_roots_receive_expected_v2_dimensions(
    tmp_path, fixture_id
):
    descriptor = _descriptor(fixture_id)
    root = tmp_path / fixture_id
    harness = _build_derived_root(root, descriptor)
    report = verify_root_report(root)
    expected = descriptor["expected"]

    assert report.integrity_valid is expected["integrity_valid"]
    assert report.security_valid is expected["security_valid"]
    assert report.completion_satisfied is expected["completion_satisfied"]
    assert report.operational_checks_passed is expected[
        "operational_checks_passed"
    ]
    assert report.valid is expected["valid"]
    assert _checks(report.integrity) == expected["integrity_checks"]
    assert _checks(report.security) == expected["security_checks"]
    assert _checks(report.completion) == expected["completion_checks"]
    assert _checks(report.epistemic) == expected["epistemic_checks"]
    assert _checks(report.operational) == expected["operational_checks"]

    if fixture_id == "A2":
        (event,) = tuple(
            item
            for item in harness.log.read()
            if item.inputs[:1] == ["dossier-pack-receipt.v1"]
        )
        _schema, receipt = harness.objects.get(
            event.inputs[1], schema="dossier-pack-receipt"
        )
        assert receipt.work_order_ref not in harness.workflow_state.work_orders
        assert "not an original terminal" in _read_json(
            root / "run-result.json"
        )["fixture_note"]
    if fixture_id == "A3":
        assert report.stats["capability_requests"] == expected[
            "capability_requests"
        ]
        assert report.stats["capability_executions"] == expected[
            "capability_executions"
        ]
        (transition,) = harness.capability_state.transitions.values()
        assert transition.lifecycle == CapabilityLifecycle.PROPOSED


def test_incident_descriptors_are_honest_and_source_linked():
    provenance = _read_json(FIXTURE_DIR / "PROVENANCE.json")
    assert provenance["incident_id"] == INCIDENT_ID
    assert provenance["repository_commit"] == INCIDENT_HEAD
    assert provenance["source_review"]["sha256"] == INCIDENT_REVIEW_SHA256
    assert provenance["original_archive"]["available_to_fixture_builder"] is False
    assert provenance["original_archive"]["original_root_bytes_included"] is False

    for fixture_id in FIXTURE_IDS:
        descriptor = _descriptor(fixture_id)
        assert descriptor["schema"] == "deepreason.incident-derived-fixture.v1"
        assert descriptor["fixture_kind"] == "minimized-derived-reproduction"
        assert descriptor["incident_id"] == INCIDENT_ID
        assert descriptor["repository_commit"] == INCIDENT_HEAD
        assert descriptor["source_review_sha256"] == INCIDENT_REVIEW_SHA256
        assert descriptor["original_root_bytes_included"] is False

    # The attachment is a development-time acceptance input, not a test
    # dependency.  Verify it when this workspace attachment is present.
    attachment = Path(
        r"C:\Users\darre\.codex\attachments"
        r"\1010d631-8837-4cf4-9a48-03cc7a1962a0\pasted-text.txt"
    )
    if attachment.is_file():
        assert hashlib.sha256(attachment.read_bytes()).hexdigest() == (
            INCIDENT_REVIEW_SHA256
        )


def test_incident_descriptors_and_generated_roots_are_frozen_and_deterministic(
    tmp_path,
):
    provenance = _read_json(FIXTURE_DIR / "PROVENANCE.json")
    for fixture_id in FIXTURE_IDS:
        descriptor_path = FIXTURE_DIR / f"{fixture_id}.json"
        assert hashlib.sha256(descriptor_path.read_bytes()).hexdigest() == (
            provenance["descriptor_sha256"][descriptor_path.name]
        )

        first = tmp_path / "first" / fixture_id
        second = tmp_path / "second" / fixture_id
        _build_derived_root(first, _descriptor(fixture_id))
        _build_derived_root(second, _descriptor(fixture_id))
        first_digest = _root_digest(first)
        assert first_digest == _root_digest(second)
        assert first_digest == provenance["generated_root_sha256"][fixture_id]


def test_fixture_area_does_not_misrepresent_original_archive_bytes():
    filenames = {
        path.relative_to(FIXTURE_DIR).as_posix()
        for path in FIXTURE_DIR.rglob("*")
        if path.is_file()
    }
    assert filenames == {
        "A1.json",
        "A2.json",
        "A3.json",
        "PROVENANCE.json",
        "README.md",
    }
    assert not any(name.endswith((".tar", ".tar.gz", "log.jsonl")) for name in filenames)
