"""Native replay verification for canonical controller-v3 transactions."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import (
    leases_from_manifest,
    resolve_school_role_lease,
)
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.rules.conj import conj
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
from deepreason.storage.objects import ObjectStore
from deepreason.verification.report import verify_root_report
from deepreason.workflow.transaction import (
    WorkLifecycleTransitionV1,
    WorkTransitionKind,
)
from tests.test_v6_transaction_qualification import (
    STAMP,
    _bind_classification,
    _control,
)


PROBLEM_ID = "pi-controller-v3-verification"


def _canonical_root(tmp_path: Path, *, unique_content: bool = True) -> Path:
    root = tmp_path / "canonical"
    commitment = Commitment(id="k-controller-v3", eval="predicate:len(content) > 0")
    dossier = EvidenceDossierV1.create(
        problem_ref=PROBLEM_ID,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="controller-v3 verifier fixture",
            acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=PROBLEM_ID,
            description="Invent two independently routed provisional mechanisms.",
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    config = Config(
        N_SCHOOLS=2,
        VS_K=1,
        FLOOR=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        NEAR_DUP_EPS=None,
        roles={
            "conjecturer": [
                {
                    "endpoint_id": "controller-v3-route",
                    "endpoint": "mock://controller-v3-route",
                    "model": "offline-controller-v3",
                    "provider": "mock",
                    "family": "offline-controller-v3",
                    "max_tokens": 512,
                    "context_window_tokens": 262_144,
                }
            ]
        },
    )
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        run_input_digest=run_input.run_input_digest,
    )
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    harness.register_commitment(commitment)
    harness.register_problem(
        Problem(
            id=PROBLEM_ID,
            description=run_input.problem.description,
            criteria=[commitment.id],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )

    call_count = 0

    def respond(_prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": (
                            f"Controller-v3 mechanism {call_count}."
                            if unique_content
                            else "A content-addressed controller-v3 mechanism."
                        ),
                        "typicality": 0.4 + call_count / 100,
                    }
                ]
            }
        )

    route = manifest.roles["conjecturer"][0]
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(
                respond,
                name=route.base_url,
                model=route.model_id,
                max_tokens=route.max_tokens,
            )
        },
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    _bind_classification(harness, manifest)
    adapter.bind_v6_authority(harness, manifest)
    for school_id in ("school-0", "school-1"):
        lease = resolve_school_role_lease(
            manifest,
            adapter.leases,
            school_id=school_id,
            role="conjecturer",
        )
        admitted = conj(
            harness,
            PROBLEM_ID,
            adapter,
            config,
            school={
                "id": school_id,
                "stance_text": f"Independent stance for {school_id}.",
                "weight": 1.0,
            },
            workload_profile="text",
            endpoint_lease=lease,
            execution_school_id=school_id,
            run_manifest=manifest,
        )
        assert len(admitted) == (1 if unique_content or school_id == "school-0" else 0)
    assert call_count == 2
    return root


def _copy_root(source: Path, tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(source, target)
    return target


def _log_rows(root: Path) -> list[dict]:
    return [json.loads(line) for line in (root / "log.jsonl").read_text().splitlines()]


def _write_log(root: Path, rows: list[dict]) -> None:
    (root / "log.jsonl").write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows)
    )


def _provider_rows(rows: list[dict]) -> list[dict]:
    return [
        row
        for row in rows
        if row.get("control", {}).get("action") == "provider_result"
    ]


def _conj_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("rule") == "Conj"]


def _replace_transition(
    root: Path,
    row: dict,
    *,
    work_id: str,
    transition_kind: WorkTransitionKind,
    trigger_ref: str,
) -> None:
    transition = WorkLifecycleTransitionV1.create(
        work_id=work_id,
        attempt_index=0,
        transition_kind=transition_kind,
        trigger_ref=trigger_ref,
    )
    ObjectStore(root / "objects").put(
        "workflow-work-lifecycle-transition-v1", transition
    )
    row["inputs"] = [transition.work_id, transition.trigger_ref]
    row["outputs"][-1] = transition.id
    row["control"]["inputs"] = list(row["inputs"])
    row["control"]["outputs"] = list(row["outputs"])
    row["control"]["decision_ref"] = transition.id


def _checks(root: Path) -> set[str]:
    result = verify_root(root)
    report = verify_root_report(root, allow_missing_terminal=True)
    assert not report.valid
    return {item["check"] for item in result["violations"]}


def test_canonical_controller_v3_history_has_zero_replay_violations(tmp_path):
    root = _canonical_root(tmp_path)

    assert verify_root(root)["violations"] == []
    report = verify_root_report(root, allow_missing_terminal=True)
    assert report.integrity_valid
    assert report.security_valid
    assert report.valid
    assert report.stats["verification_v2"]["legacy_adapter_suppressed_count"] == 0


def test_independent_attempts_may_admit_the_same_content_address(tmp_path):
    root = _canonical_root(tmp_path, unique_content=False)

    assert verify_root(root)["violations"] == []


def test_missing_lifecycle_transition_fails_closed(tmp_path):
    root = _copy_root(_canonical_root(tmp_path), tmp_path, "missing-transition")
    rows = _log_rows(root)
    provider = _provider_rows(rows)[0]
    provider["rule"] = "Measure"
    provider.pop("control")
    _write_log(root, rows)

    assert "workflow-decision" in _checks(root)


def test_duplicate_out_of_order_transition_fails_closed(tmp_path):
    root = _copy_root(_canonical_root(tmp_path), tmp_path, "duplicate-transition")
    rows = _log_rows(root)
    semantic = next(
        row
        for row in rows
        if row.get("control", {}).get("action") == "work_transition"
        and len(row.get("outputs", ())) == 2
        and row["seq"] > _provider_rows(rows)[0]["seq"]
    )
    _replace_transition(
        root,
        semantic,
        work_id=semantic["inputs"][0],
        transition_kind=WorkTransitionKind.WORK_ISSUED,
        trigger_ref="duplicate-issued-transition",
    )
    _write_log(root, rows)

    assert "workflow-decision" in _checks(root)


def test_transition_bound_to_wrong_work_fails_closed(tmp_path):
    root = _copy_root(_canonical_root(tmp_path), tmp_path, "wrong-transition-work")
    rows = _log_rows(root)
    first, second = _provider_rows(rows)
    _replace_transition(
        root,
        first,
        work_id=second["inputs"][0],
        transition_kind=WorkTransitionKind.PROVIDER_RESULT,
        trigger_ref="cross-work-provider-result",
    )
    _write_log(root, rows)

    assert "workflow-decision" in _checks(root)


def test_provider_result_without_authorized_attempt_fails_closed(tmp_path):
    root = _copy_root(_canonical_root(tmp_path), tmp_path, "orphan-result")
    rows = _log_rows(root)
    provider = _provider_rows(rows)[0]
    provider["outputs"] = [provider["control"]["decision_ref"]]
    provider["control"]["outputs"] = list(provider["outputs"])
    _write_log(root, rows)

    assert "workflow-call-pairing" in _checks(root)


def test_conj_paired_to_wrong_attempt_fails_closed(tmp_path):
    root = _copy_root(_canonical_root(tmp_path), tmp_path, "wrong-conj-attempt")
    rows = _log_rows(root)
    providers = _provider_rows(rows)
    conj_row = _conj_rows(rows)[0]
    conj_row["inputs"] = [
        f"conjecture-call:{providers[1]['seq']}"
        if value.startswith("conjecture-call:")
        else value
        for value in conj_row["inputs"]
    ]
    _write_log(root, rows)

    assert "workflow-call-pairing" in _checks(root)


def test_duplicate_ambiguous_result_pairing_fails_closed(tmp_path):
    root = _copy_root(_canonical_root(tmp_path), tmp_path, "ambiguous-result")
    rows = _log_rows(root)
    providers = _provider_rows(rows)
    conj_row = _conj_rows(rows)[0]
    conj_row["inputs"].append(f"conjecture-call:{providers[1]['seq']}")
    _write_log(root, rows)

    assert "workflow-call-pairing" in _checks(root)


def test_route_differing_from_frozen_route_seat_plan_fails_closed(tmp_path):
    root = _copy_root(_canonical_root(tmp_path), tmp_path, "wrong-route")
    rows = _log_rows(root)
    call = _provider_rows(rows)[0]["llm"]
    call["school_route"]["route_sha256"] = "0" * 64
    for attempt in call["attempt_trace"]:
        attempt["route_sha256"] = "0" * 64
    _write_log(root, rows)

    assert "school-route" in _checks(root)


@pytest.mark.parametrize("mutation", ("missing", "mismatched"))
def test_missing_or_mismatched_route_lease_fails_closed(tmp_path, mutation):
    root = _copy_root(_canonical_root(tmp_path), tmp_path, f"{mutation}-lease")
    rows = _log_rows(root)
    call = _provider_rows(rows)[0]["llm"]
    if mutation == "missing":
        call.pop("school_route")
    else:
        call["school_route"]["seat"] = 1
        for attempt in call["attempt_trace"]:
            attempt["seat"] = 1
    _write_log(root, rows)

    assert "school-route" in _checks(root)


def test_cross_work_attempt_reuse_fails_closed(tmp_path):
    root = _copy_root(_canonical_root(tmp_path), tmp_path, "cross-work-attempt")
    rows = _log_rows(root)
    first, second = _provider_rows(rows)
    second["llm"]["work_order_id"] = first["llm"]["work_order_id"]
    second["llm"]["dispatch_authorization_ref"] = first["llm"][
        "dispatch_authorization_ref"
    ]
    _write_log(root, rows)

    assert "workflow-call-pairing" in _checks(root)
