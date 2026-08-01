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


def _atomic_child_responses(index: int, *, repaired: bool) -> list[str]:
    """One atomic child's provider responses, optionally via a repair step.

    A wire-invalid first response (``typicality`` out of range) is the same
    class of rejection the live run took — a generic envelope failure — and the
    patch that follows is the minimal one that makes the candidate admissible.
    """

    candidate = {
        "content": f"atomic mechanism {index}",
        "typicality": 0.5,
        "neighbours": [],
    }
    if not repaired:
        return [json.dumps({"candidate": candidate})]
    return [
        json.dumps({"candidate": {**candidate, "typicality": 2.0}}),
        json.dumps(
            {
                "schema": "repair.patch.v1",
                "op": "replace",
                "path": "/candidate/typicality",
                "value": 0.5,
            }
        ),
    ]


def _engaged_root(tmp_path: Path, *, repair_child: int | None = None) -> Path:
    """Drive one turn through rejected patches into a decomposition merge.

    ``repair_child`` makes that atomic child's first response wire-invalid so
    the child is re-dispatched as ``repair.semantic-task.v1`` work and the
    completion names the REPAIR in that slot rather than the child itself.
    That shape occurs live (run-b4d6dfda0c20676a864a051fbc97bda4, slot 0 of two
    of three merges) and no fixture exercised it before.
    """

    root = tmp_path / ("engaged-repair" if repair_child is None else f"engaged-repair-r{repair_child}")
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
        # All four granted repair steps (the conjecture family's explicit
        # multi-pointer ceiling) return wire-VALID patches whose application
        # is rejected: repair_step_rejected x3, then schema_exhausted.
        unrelated_patch,
        unrelated_patch,
        unrelated_patch,
        unrelated_patch,
        # The decomposition transacts six atomic children, all admitted.
        *(
            piece
            for index in range(6)
            for piece in _atomic_child_responses(
                index, repaired=(index == repair_child)
            )
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
        for item in work[:5]
    ] == [
        (WorkflowTaskKind.CONJECTURE, "rejected", "conjecture_repair_requested"),
        (WorkflowTaskKind.REPAIR, "rejected", "conjecture_repair_step_rejected"),
        (WorkflowTaskKind.REPAIR, "rejected", "conjecture_repair_step_rejected"),
        (WorkflowTaskKind.REPAIR, "rejected", "conjecture_repair_step_rejected"),
        (WorkflowTaskKind.REPAIR, "schema_exhausted", "conjecture_schema_exhausted"),
    ]
    assert work[1].preparation.task_payload_value["mode"] == "patch"
    return root


@pytest.fixture(scope="module")
def engaged_root(tmp_path_factory) -> Path:
    return _engaged_root(tmp_path_factory.mktemp("engaged-repair-verification"))


@pytest.fixture(scope="module", params=[0, 5], ids=["first-child", "latest-child"])
def repaired_child_root(request, tmp_path_factory) -> Path:
    """A merge whose completion names a repair work item in one slot.

    Both positions are exercised because the LATEST child is also the one whose
    provider call the merge marker names, so a repair there moves the marker as
    well as the payload schema.
    """

    return _engaged_root(
        tmp_path_factory.mktemp(f"engaged-repaired-child-{request.param}"),
        repair_child=request.param,
    )


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
    # parent turn, four patch steps, six atomic children
    assert len(providers) == 11
    assert [attempt["valid"] for attempt in providers[0]["llm"]["attempt_trace"]] == [
        False
    ]
    for patch_call in providers[1:5]:
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
    child_seqs = [row["seq"] for row in _provider_rows(rows)[5:]]
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
    child_seqs = [row["seq"] for row in providers[5:]]
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


def test_merge_whose_child_was_repaired_verifies_clean(repaired_child_root):
    """Regression (jolt run-b4d6dfda0c20676a864a051fbc97bda4): a decomposition
    merge containing a repaired child was reported non-replay-valid.

    When an atomic child is rejected, the work that produces the admitted
    candidate is a DIFFERENT work item — ``repair.semantic-task.v1``, whose
    decomposition authority is its ``parent_work_id``. The completion must name
    that repair, because the repair is what carries the admission:
    ``workflow/replay.py`` refuses a completion whose per-slot inventory
    differs. The merge exemption resolved each slot by work id and demanded a
    ``contract-decomposition-child.v1`` payload, so it rejected the shape its
    own writer requires.

    Live evidence: slot 0 of two of that run's three merges, giving exactly two
    findings at Conj seq 245 and 386, recorded by the run about itself in
    REPLAY_VALIDATION.json. Nothing else about those merges differed — all 6/6
    child admissions resolved as admitted, the latest-child marker matched, and
    the outputs were a subset of admitted_effect_refs.
    """

    result = verify_root(repaired_child_root)

    assert result["violations"] == []


def test_the_repaired_child_slot_really_names_repair_work(repaired_child_root):
    """Guards the regression above against passing for the wrong reason.

    If the fixture stopped producing a repaired child — a wire-valid first
    response, a changed repair budget — the test above would go green while
    exercising nothing. This pins the shape it is meant to cover.
    """

    preparations = {}
    for path in (
        repaired_child_root / "objects" / "workflow-work-preparation-v1"
    ).glob("*.json"):
        record = json.loads(path.read_text())
        record = record.get("data", record)
        preparations[record.get("work_id") or record["id"]] = record

    schemas: list[list[str | None]] = []
    for path in (
        repaired_child_root
        / "objects"
        / "workflow-contract-decomposition-completion-v1"
    ).glob("*.json"):
        record = json.loads(path.read_text())
        record = record.get("data", record)
        schemas.append(
            [
                (
                    preparations.get(work_id, {}).get("task_payload_value") or {}
                ).get("schema")
                for work_id in record["child_work_ids"]
            ]
        )

    assert schemas, "the fixture produced no decomposition completion"
    assert any(
        "repair.semantic-task.v1" in row for row in schemas
    ), f"no completion names a repair work item: {schemas}"


def test_a_tampered_repair_preparation_fails_closed(repaired_child_root, tmp_path):
    """The merge exemption now walks ``parent_work_id``; a forged parent must
    not survive that walk.

    It cannot even reach it. Preparations load through ``objects.get``, which
    verifies each record against its stored digest, so editing one to name a
    different parent (or a different contract) raises ``corrupt object record``
    and the root fails closed on ``workflow-decision`` before the pairing check
    runs. The walk's own parent guards are therefore defence-in-depth against a
    future writer change, not against a forged record — and this pins the outer
    guarantee that actually holds.
    """

    root = _copy_root(repaired_child_root, tmp_path, "tampered-repair-preparation")
    tampered = 0
    for path in (root / "objects" / "workflow-work-preparation-v1").glob("*.json"):
        record = json.loads(path.read_text())
        body = record.get("data", record)
        payload = body.get("task_payload_value") or {}
        if payload.get("schema") == "repair.semantic-task.v1":
            body["contract_id"] = "conjecturer.turn.v6"
            path.write_text(json.dumps(record))
            tampered += 1

    assert tampered, "the fixture produced no repair preparation to tamper with"

    result = verify_root(root)
    assert result["violations"], "a tampered repair preparation verified clean"
    assert any(
        "corrupt object record" in item["detail"] for item in result["violations"]
    ), result["violations"]
