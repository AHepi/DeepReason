"""Verification of engaged-preset patch-repair rejections and merge Conj events.

First live engaged run (mistral-large-3:675b, deepreason.v6.engaged.v1)
produced two durable patterns the verifier predated:

1. A separately authorized patch-repair step dispatches under the patch wire
   contract, so its single attempt can honestly record ``valid=True`` while
   applying the patch still fails the parent contract.  The transaction then
   terminalizes as ``rejected``/``schema_exhausted`` and the old checker
   demanded a wire-invalid trace ("failed call must contain no valid attempt").

2. After schema exhaustion, a contract decomposition transacts atomic children
   whose admitted candidates are merged by ONE formal Conj event referencing
   only the LATEST child provider call.  The old pairing checker required a
   single admission from that one attempt to cover every output.

Both are proven by durable transaction records (preparations, admissions,
typed terminals, decomposition transition + completion), so the verifier is
taught those exact chains; everything else keeps failing closed.
"""

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
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.rules.conj import conj
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
from deepreason.verification.report import verify_root_report
from deepreason.workflow.models import WorkflowTaskKind
from tests.test_v6_compact_recovery_transition import _bind_classification
from tests.test_v6_live_repair_transactions import STAMP, _control

PROBLEM_ID = "pi-engaged-repair-verification"


def _config() -> Config:
    return Config(
        N_SCHOOLS=0,
        roles={
            "conjecturer": [
                {
                    "endpoint_id": "engaged-repair-route",
                    "endpoint": "mock://engaged-repair-route",
                    "model": "offline-engaged-repair",
                    "provider": "mock",
                    "family": "offline-engaged-repair",
                    "max_tokens": 64,
                    "context_window_tokens": 16_384,
                }
            ]
        },
    )


def _engaged_root(tmp_path: Path) -> Path:
    """Drive one turn through rejected patches into a decomposition merge."""

    root = tmp_path / "engaged-repair"
    commitment = Commitment(
        id="k-engaged-repair", eval="predicate:len(content) > 0"
    )
    dossier = EvidenceDossierV1.create(
        problem_ref=PROBLEM_ID,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="engaged repair verifier fixture",
            acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=PROBLEM_ID,
            description="Invent one provisional mechanism.",
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    config = _config()
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

    unrelated_patch = json.dumps(
        {
            "schema": "repair.patch.v1",
            "op": "replace",
            "path": "/candidates/0/content",
            "value": "laundered replacement",
        }
    )
    responses = [
        # Turn output is wire-invalid (typicality out of range): the parent
        # transaction terminates rejected/conjecture_repair_requested.
        json.dumps(
            {
                "candidates": [
                    {"content": "preserve this mechanism", "typicality": 2.0}
                ]
            }
        ),
        # Both repair steps return wire-VALID patches whose application is
        # rejected: repair_step_rejected, then schema_exhausted.
        unrelated_patch,
        unrelated_patch,
        # The decomposition transacts six atomic children, all admitted.
        *(
            json.dumps(
                {
                    "candidate": {
                        "content": f"atomic mechanism {index}",
                        "typicality": 0.5,
                        "neighbours": [],
                    }
                }
            )
            for index in range(6)
        ),
    ]
    _bind_classification(harness, manifest)
    route = manifest.roles["conjecturer"][0]
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(
                responses,
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
    adapter.bind_v6_authority(harness, manifest)

    artifacts = conj(harness, PROBLEM_ID, adapter, config, run_manifest=manifest)

    assert len(artifacts) == 6
    work = list(harness.workflow_state.transaction_work.values())
    assert [
        (item.preparation.task_kind, item.terminal.status, item.terminal.reason_code)
        for item in work[:3]
    ] == [
        (WorkflowTaskKind.CONJECTURE, "rejected", "conjecture_repair_requested"),
        (WorkflowTaskKind.REPAIR, "rejected", "conjecture_repair_step_rejected"),
        (WorkflowTaskKind.REPAIR, "schema_exhausted", "conjecture_schema_exhausted"),
    ]
    assert work[1].preparation.task_payload_value["mode"] == "patch"
    return root


@pytest.fixture(scope="module")
def engaged_root(tmp_path_factory) -> Path:
    return _engaged_root(tmp_path_factory.mktemp("engaged-repair-verification"))


def _copy_root(source: Path, tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(source, target)
    return target


def _log_rows(root: Path) -> list[dict]:
    return [
        json.loads(line) for line in (root / "log.jsonl").read_text().splitlines()
    ]


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


def _checks(root: Path) -> set[str]:
    return {item["check"] for item in verify_root(root)["violations"]}


def test_rejected_wire_valid_patches_and_merge_conj_verify_clean(engaged_root):
    result = verify_root(engaged_root)

    assert result["violations"] == []

    report = verify_root_report(engaged_root, allow_missing_terminal=True)
    assert report.integrity_valid
    assert report.security_valid
    assert report.valid
    # The rejected/exhausted repair terminals stay visible as honest
    # operational observations without breaking authority validity.
    operational = {finding.detail for finding in report.operational}
    assert any("conjecture_repair_requested" in detail for detail in operational)
    assert any("conjecture_schema_exhausted" in detail for detail in operational)


def test_rejected_patch_calls_keep_their_wire_valid_final_attempt(engaged_root):
    rows = _log_rows(engaged_root)
    providers = _provider_rows(rows)
    # parent turn, patch step 1, patch step 2, six atomic children
    assert len(providers) == 9
    assert [attempt["valid"] for attempt in providers[0]["llm"]["attempt_trace"]] == [
        False
    ]
    for patch_call in providers[1:3]:
        assert [
            attempt["valid"] for attempt in patch_call["llm"]["attempt_trace"]
        ] == [True]


def test_fabricated_valid_attempt_on_wire_invalid_turn_fails_closed(
    engaged_root, tmp_path
):
    root = _copy_root(engaged_root, tmp_path, "fabricated-parent-validity")
    rows = _log_rows(root)
    parent = _provider_rows(rows)[0]
    parent["llm"]["attempt_trace"][-1]["valid"] = True
    _write_log(root, rows)

    assert "attempt-validity" in _checks(root)


def test_merge_conj_bound_to_non_latest_child_fails_closed(engaged_root, tmp_path):
    root = _copy_root(engaged_root, tmp_path, "non-latest-child-merge")
    rows = _log_rows(root)
    child_seqs = [row["seq"] for row in _provider_rows(rows)[3:]]
    merge_conj = next(
        row
        for row in rows
        if row.get("rule") == "Conj"
        and f"conjecture-call:{child_seqs[-1]}" in row.get("inputs", ())
    )
    merge_conj["inputs"] = [
        f"conjecture-call:{child_seqs[0]}"
        if value == f"conjecture-call:{child_seqs[-1]}"
        else value
        for value in merge_conj["inputs"]
    ]
    _write_log(root, rows)

    assert "workflow-call-pairing" in _checks(root)


def test_merge_conj_bound_to_non_child_work_fails_closed(engaged_root, tmp_path):
    root = _copy_root(engaged_root, tmp_path, "non-child-merge")
    rows = _log_rows(root)
    providers = _provider_rows(rows)
    child_seqs = [row["seq"] for row in providers[3:]]
    rejected_patch_seq = providers[1]["seq"]
    merge_conj = next(
        row
        for row in rows
        if row.get("rule") == "Conj"
        and f"conjecture-call:{child_seqs[-1]}" in row.get("inputs", ())
    )
    merge_conj["inputs"] = [
        f"conjecture-call:{rejected_patch_seq}"
        if value == f"conjecture-call:{child_seqs[-1]}"
        else value
        for value in merge_conj["inputs"]
    ]
    _write_log(root, rows)

    assert "workflow-call-pairing" in _checks(root)
