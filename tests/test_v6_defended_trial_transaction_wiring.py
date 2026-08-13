"""R1/R5 (defended-trial-wiring tranche, 2026-08-13): informal/trial.py's
defender and judge calls dispatch through InquiryTransactionService under
RunManifest v6, carrying a dispatch_authorization the same way the ordinary
batch-critic call already does -- proving the operator's diagnosed gap
(``WorkflowAuthorizationError`` mid-cycle the first time a defender call
fires) is closed. Modeled on ``test_v6_nonconjecture_recovery.py``'s own
manifest/adapter fixture discipline.
"""

from __future__ import annotations

import pytest

from deepreason.canonical import canonical_json
from deepreason.harness import Harness
from deepreason.informal.trial import run_argument_trial_from_case
from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
from deepreason.llm.budget import TokenMeter
from deepreason.llm.contracts import DefenderOutput
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Provenance
from deepreason.storage.blobs import BlobStore
from deepreason.workflow.models import WorkflowTaskKind
from tests.test_v6_compact_recovery_transition import _bind_classification
from tests.test_v6_nonconjecture_recovery import _defended_trial_manifest


CASE_TEXT = "the mechanism omits a required boundary check"
DEFENCE_TEXT = "the boundary check happens implicitly via the type system"
DECISIVE_POINT = "the boundary check happens implicitly"


def _v6_adapter(harness, manifest, *, defender_response=None, judge_responses=None):
    defender_response = defender_response or canonical_json(
        {"answer": DEFENCE_TEXT}
    ).decode("utf-8")
    judge_responses = judge_responses or [
        canonical_json(
            {"verdict": "fail", "decisive_point": DECISIVE_POINT}
        ).decode("utf-8")
    ] * 2
    defender_route = manifest.roles["defender"][0]
    judge_routes = manifest.roles["judge"]
    adapter = LLMAdapter(
        {
            "defender": [
                MockEndpoint(
                    [defender_response],
                    name=defender_route.base_url,
                    model=defender_route.model_id,
                    max_tokens=defender_route.max_tokens,
                )
            ],
            "judge": [
                MockEndpoint(
                    [response],
                    name=route.base_url,
                    model=route.model_id,
                    max_tokens=route.max_tokens,
                )
                for route, response in zip(judge_routes, judge_responses, strict=True)
            ],
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


def test_defender_and_judge_calls_carry_dispatch_authorization_under_v6(tmp_path):
    _config_value, manifest = _defended_trial_manifest()
    harness = Harness(tmp_path / "defended-trial-v6-wiring")
    _bind_classification(harness, manifest)
    target = harness.create_artifact(
        "the mechanism under trial", provenance=Provenance(role="conjecturer")
    )
    adapter = _v6_adapter(harness, manifest)

    critic = run_argument_trial_from_case(
        harness,
        adapter,
        _config_value,
        target.id,
        CASE_TEXT,
        None,
        authority="status",
    )

    assert critic is not None
    assert critic.warrants
    work = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.DEFENDED_TRIAL_STEP
    ]
    # One defender call, two judge-ensemble calls -- no variator role
    # configured, so the paraphrase screen is a no-op ("skipped", not
    # dispatched) and adds no further work items.
    assert len(work) == 3
    assert {item.preparation.route_lease.role for item in work} == {
        "defender",
        "judge",
    }
    for item in work:
        assert item.authorization is not None
        assert item.terminal is not None
        assert item.terminal.status == "completed"
        provider = item.provider_attempts[item.preparation.attempt_index]
        assert (
            provider.authorization_bundle_ref == item.authorization.id
        )
    calls = [event.llm for event in harness.log.read() if event.llm is not None]
    assert len(calls) == 3
    assert {call.dispatch_authorization_ref for call in calls} == {
        item.authorization.id for item in work
    }


def test_unbound_trial_defender_call_is_refused_by_the_global_v6_guard(tmp_path):
    """The precondition the fix satisfies, not bypasses: an ordinary
    ``adapter.call`` with no ``dispatch_authorization`` still raises under
    v6, exactly as SEAM-llm-x-workflow.md's own guard probe proves for the
    critic call. Mirrors that check's shape for the defender role."""

    harness = Harness(tmp_path / "unbound-defender-refused")
    endpoint = MockEndpoint(
        [canonical_json({"answer": DEFENCE_TEXT}).decode("utf-8")]
    )
    adapter = LLMAdapter(
        {"defender": endpoint},
        BlobStore(tmp_path / "blobs"),
        transaction_authority_required=True,
    )
    with pytest.raises(WorkflowAuthorizationError) as caught:
        adapter.call("defender", "pack", DefenderOutput)
    assert "RunManifest v6 provider dispatch requires a bound transaction" in str(
        caught.value
    )
    assert endpoint.last_transport_attempts == 0
