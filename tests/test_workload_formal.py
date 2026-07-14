from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from deepreason.authority import AuthoritySurface, TrialAuthority, trial_authority_for
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import Commitment, Status
from deepreason.ontology.artifact import RefRole
from deepreason.rules.warrants import register_fail_warrant
from deepreason.verification.models import VerificationRequest, VerificationResult
from deepreason.verification._sandbox import seccomp_available
from deepreason.verification.runner import TrustedCheckRunner
from deepreason.workloads.code import CheckSpec
from deepreason.workloads.formal import (
    AssumptionMapping,
    FormalClaim,
    FormalMismatchTest,
    FormalWorkloadSpec,
    FormalizationRelation,
    PinnedLeanRequest,
    register_formal_workflow,
)


def _spec(harness: Harness, *, explicit: bool = False) -> FormalWorkloadSpec:
    statement = "For every natural n, n + 0 = n."
    source_ref = harness.blobs.put(b"theorem add_zero_nat (n : Nat) : n + 0 = n := by simp\n")
    return FormalWorkloadSpec(
        claim=FormalClaim(statement=statement, context=("natural-number addition",)),
        request=PinnedLeanRequest(
            toolchain_id="lean4@4.19.0",
            source_ref=source_ref,
            target_theorems=["add_zero_nat"],
        ),
        relation=FormalizationRelation(
            informal_target=statement,
            theorem="add_zero_nat",
            assumption_mapping=(
                AssumptionMapping(
                    informal_assumption="n is a natural number",
                    formal_assumption="n : Nat",
                    relation="equivalent",
                ),
            ),
            omitted_conditions=(),
            scope="Natural-number addition in Lean core",
            counterconditions=("A different addition operation is intended",),
            mismatch_tests=(
                FormalMismatchTest(
                    id="non-nat-domain",
                    case="Interpret n in a non-natural algebra",
                    expected_informal="outside scope",
                    expected_formal="the theorem does not apply",
                ),
            ),
        ),
        explicit_formal_dependence=explicit,
    )


def _result(harness: Harness, spec: FormalWorkloadSpec, verdict: str) -> VerificationResult:
    diagnostics = harness.blobs.put(
        canonical_json({"schema": "test-verifier-receipt-v1", "verdict": verdict})
    )
    fingerprint = {
        "backend": "lean4",
        "toolchain_id": spec.request.toolchain_id,
        "executable_sha256": "b" * 64,
        "available": True,
    }
    return VerificationResult(
        backend="lean4",
        fingerprint=fingerprint,
        verdict=verdict,
        diagnostics_ref=diagnostics,
        axioms_ref=harness.blobs.put(canonical_json({"theorems": {}})),
        theorems=[spec.relation.theorem] if verdict == "pass" else [],
        source_sha256=spec.request.source_ref,
        toolchain_sha256=sha256_hex(canonical_json(fingerprint)),
    )


def test_lean_requests_forbid_sorry_and_require_a_target():
    source = "a" * 64
    with pytest.raises(ValidationError, match="never permits sorry"):
        VerificationRequest(
            backend="lean4",
            toolchain_id="lean4@4.19.0",
            source_ref=source,
            allow_sorry=True,
            target_theorems=["sample"],
        )
    with pytest.raises(ValidationError, match="at least one target"):
        VerificationRequest(
            backend="lean4",
            toolchain_id="lean4@4.19.0",
            source_ref=source,
        )


def test_check_limit_is_positive_and_enforced_as_finite_result_items(tmp_path: Path):
    assert CheckSpec(id="default", runner="command", argv=("true",)).step_or_item_limit > 0
    with pytest.raises(ValidationError):
        CheckSpec(id="zero", runner="command", argv=("true",), step_or_item_limit=0)

    check = CheckSpec(
        id="bounded-output",
        runner="command",
        argv=(sys.executable, "-c", "print('a'); print('b'); print('c')"),
        step_or_item_limit=2,
    )
    result = TrustedCheckRunner().run(check, tmp_path)

    assert result.verdict == "overrun"
    assert result.returncode == 0
    assert result.detail == {
        "sandbox_abort": "declared item containment limit",
        "output_items": 3,
        "step_or_item_limit": 2,
    }


def test_trusted_code_check_has_no_network_when_seccomp_is_available(tmp_path: Path):
    if not seccomp_available():
        pytest.skip("libseccomp is unavailable")
    source = (
        "import socket\n"
        "try:\n"
        "    socket.socket()\n"
        "except PermissionError:\n"
        "    print('network denied')\n"
        "else:\n"
        "    raise SystemExit(2)\n"
    )
    result = TrustedCheckRunner().run(
        CheckSpec(
            id="no-network",
            runner="command",
            argv=(sys.executable, "-c", source),
            step_or_item_limit=4,
        ),
        tmp_path,
    )

    assert result.verdict == "pass"
    assert result.detail["network_isolated"] is True


def test_proof_pass_is_a_receipt_not_an_acceptance_edge(tmp_path: Path):
    harness = Harness(tmp_path / "run")
    spec = _spec(harness, explicit=False)
    artifacts = register_formal_workflow(harness, spec, result=_result(harness, spec, "pass"))

    assert artifacts.receipt is not None
    assert artifacts.criticism is None
    assert harness.warrants == {}
    assert not harness.state.att
    assert not [
        ref for ref in artifacts.claim.interface.refs if ref.role == RefRole.DEPENDENCE
    ]
    # This accepted label comes from ordinary registration in an unattacked
    # graph; the pass receipt did not set it or create any special edge.
    assert harness.state.status[artifacts.claim.id] == Status.ACCEPTED


def test_valid_fail_refutes_only_theorem_and_cascades_through_explicit_support(tmp_path: Path):
    harness = Harness(tmp_path / "run")
    spec = _spec(harness, explicit=True)
    artifacts = register_formal_workflow(harness, spec, result=_result(harness, spec, "fail"))

    assert artifacts.criticism is not None
    assert harness.state.status[artifacts.theorem.id] == Status.REFUTED
    assert harness.state.status[artifacts.relation.id] == Status.ACCEPTED
    assert harness.state.status[artifacts.claim.id] == Status.SUSPENDED_UNSUPPORTED
    assert set(harness.state.dep).issuperset(
        {
            (artifacts.claim.id, artifacts.theorem.id),
            (artifacts.claim.id, artifacts.relation.id),
        }
    )


def test_formal_verifier_authority_survives_text_policy_layer(tmp_path: Path):
    """The new text gate cannot demote a verifier-backed formal failure."""
    assert (
        trial_authority_for(Config(), "formal", AuthoritySurface.RUBRIC)
        == TrialAuthority.STATUS
    )
    harness = Harness(tmp_path / "run")
    spec = _spec(harness, explicit=True)

    artifacts = register_formal_workflow(harness, spec, result=_result(harness, spec, "fail"))

    assert artifacts.criticism is not None
    assert harness.state.status[artifacts.theorem.id] == Status.REFUTED


def test_relation_is_separately_refutable_and_suspends_only_explicit_dependent(tmp_path: Path):
    harness = Harness(tmp_path / "run")
    spec = _spec(harness, explicit=True)
    artifacts = register_formal_workflow(harness, spec)
    mismatch = spec.relation.mismatch_tests[0]
    commitment = Commitment(
        id=f"formalization-mismatch:{mismatch.id}",
        eval="predicate:False",
    )
    harness.register_commitment(commitment)
    register_fail_warrant(
        harness,
        commitment_id=commitment.id,
        target_id=artifacts.relation.id,
        nu_content="nu: the recorded mismatch case discriminates R",
        critic_content=f"critic: mismatch test {mismatch.id} refutes R",
        trace_ref=harness.blobs.put(
            json.dumps(mismatch.model_dump(mode="json"), sort_keys=True).encode()
        ),
    )

    assert harness.state.status[artifacts.theorem.id] == Status.ACCEPTED
    assert harness.state.status[artifacts.relation.id] == Status.REFUTED
    assert harness.state.status[artifacts.claim.id] == Status.SUSPENDED_UNSUPPORTED


def test_formal_relation_must_match_claim_and_pinned_theorem(tmp_path: Path):
    harness = Harness(tmp_path / "run")
    spec = _spec(harness)
    with pytest.raises(ValidationError, match="exact informal claim"):
        spec.model_copy(
            update={
                "relation": spec.relation.model_copy(update={"informal_target": "different"})
            }
        ).model_validate(
            {
                **spec.model_dump(mode="json"),
                "relation": {
                    **spec.relation.model_dump(mode="json"),
                    "informal_target": "different",
                },
            }
        )
