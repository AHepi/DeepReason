import json

import pytest

from deepreason import programs
from deepreason.config import Config
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.rules.conj import conj
from deepreason.workloads.text import (
    Countercondition,
    ReasoningEnvelopeV1,
    ReasoningWorkloadSpec,
    WorkloadProblem,
    compile_countercondition_commitments,
    envelope_json,
    seed_reasoning_workload,
)


def test_reasoning_envelope_checks_form_not_truth():
    envelope = ReasoningEnvelopeV1(
        claim="An intentionally disputable claim",
        mechanism="A stated causal mechanism",
        counterconditions=(Countercondition(case="observation differs", eval="observation"),),
    )
    verdict, trace = programs._reasoning_envelope_wf(envelope_json(envelope), type("B", (), {"extra": {}})())
    assert verdict == "pass"
    assert trace["counterconditions"] == 1
    with pytest.raises(ValueError, match="attack surface"):
        ReasoningEnvelopeV1(claim="bare assertion")


def test_counterconditions_compile_before_candidate_identity(harness):
    envelope = ReasoningEnvelopeV1(
        claim="claim",
        mechanism="mechanism",
        counterconditions=(Countercondition(case="measure X", eval="observation"),),
    )
    commitment_ids = compile_countercondition_commitments(harness, envelope)
    commitment = harness.commitments[commitment_ids[0]]
    assert commitment.observation_valued
    assert commitment.eval == "program:reasoning_observation_pending"


def test_compact_v2_reasoning_conjecture_compiles_harness_interfaces(harness):
    spec = ReasoningWorkloadSpec(
        problem=WorkloadProblem(id="reason:test", description="Why does X happen?")
    )
    problem = seed_reasoning_workload(harness, spec)
    response = json.dumps(
        {
            "candidates": [
                {
                    "claim": "X follows from a feedback mechanism",
                    "mechanism": "A increases B and B stabilizes A",
                    "counterconditions": ["the feedback sign reverses"],
                    "typicality": 0.4,
                    "optional_refs": [],
                    "sidecar": {
                        "search_signal": "productive",
                        "requested_context_aliases": [],
                    },
                }
            ]
        }
    )
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda _prompt: response)},
        harness.blobs,
        model_profile="compact",
    )
    artifacts = conj(harness, problem.id, adapter, Config(VS_K=1, model_profile="compact"))
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert "reasoning-envelope-wf" in artifact.interface.commitments
    assert any(item.startswith("reason-counter@") for item in artifact.interface.commitments)
    assert json.loads(artifact.content_ref.removeprefix("inline:"))["claim"].startswith("X follows")
    assert not any(key in artifact.content_ref for key in ("search_signal", "typicality"))


def test_compact_reasoning_contract_rejects_control_fields(harness):
    spec = ReasoningWorkloadSpec(
        problem=WorkloadProblem(id="reason:control", description="Why?")
    )
    seed_reasoning_workload(harness, spec)
    response = json.dumps(
        {
            "candidates": [
                {
                    "claim": "claim",
                    "mechanism": "mechanism",
                    "counterconditions": ["counter"],
                    "typicality": 0.5,
                    "optional_refs": [],
                    "route": "other-model",
                }
            ]
        }
    )
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda _prompt: response)},
        harness.blobs,
        retry_max=0,
        model_profile="compact",
    )
    with pytest.raises(Exception, match="CONTROL_FIELD|control field|extra field"):
        conj(harness, "reason:control", adapter, Config(VS_K=1, RETRY_MAX=0))


def test_reason_cli_dry_run_accepts_bound_v6_manifest(tmp_path, capsys):
    from deepreason.cli.main import main
    from tests.test_v6_only_cli_admission import _prepared_v6_root

    text = "Why does X happen?"
    prepared = _prepared_v6_root(tmp_path / "run", text=text)
    assert main(
        [
            "--root", str(prepared.root), "reason",
            "--text", text, "--run-manifest", str(prepared.manifest_path),
            "--dry-run",
        ]
    ) == 0
    output = capsys.readouterr().out
    assert "offline-model" in output and "sha256=" in output
