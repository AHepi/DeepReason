"""D0, migrated to the V6-only boundary.

Mini's historical opt-in v4 control envelope is retired together with every
pre-v6 manifest: a root bound to the v4 shadow controller now fails closed in
the parent loader.  New mini roots are V6-native and run through the parent
Harness primitive layer only — provider calls stay plain canonical events
with the shared bounded-repair protocol and no workflow records, and a
pre-bound v6 mini manifest is semantically indistinguishable from the one
mini compiles for itself.
"""

from __future__ import annotations

import inspect
import json

from deepreason import programs
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.firewall import route_from_endpoint
from deepreason.ontology import Rule
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    SchoolExecutionPolicyV1,
    UnsupportedRunManifestVersionError,
    bind_run_manifest,
    compile_run_manifest,
)
from minireason.call import MockEndpoint
from minireason.compat import bind_mini_root
from minireason.loop import run

import pytest


def _candidate() -> str:
    content = json.dumps(
        {
            "claim": "A compact mechanism remains open semantic text.",
            "mechanism": "A bounded feedback path could explain the effect.",
            "forbidden": [
                {"case": "the payload must be JSON", "eval": "program:json-wf"}
            ],
        }
    )
    return json.dumps(
        {"candidates": [{"content": content, "typicality": 0.37}]}
    )


def _shadow_policy() -> ControlPlanePolicyV1:
    return ControlPlanePolicyV1(
        controller_version="workflow.controller.v1",
        mode="shadow",
        workflow_profile="conjecture.shadow.v1",
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
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v1",
            conjecturer_turn_contract="conjecturer.legacy.v1",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )


def _bind_legacy_shadow_manifest(endpoint, root):
    """Reproduce a historical opt-in v4 shadow root byte-for-byte."""
    config = Config(
        roles={"conjecturer": route_from_endpoint(endpoint).endpoint_spec()},
        model_profile="compact",
    )
    manifest = compile_run_manifest(
        config,
        engine_profile="mini",
        model_profile="compact",
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-16T00:00:00Z",
        control_plane_policy=_shadow_policy(),
    )
    bind_run_manifest(manifest, root)
    return manifest


def _files(root):
    return {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_legacy_v4_shadow_root_fails_closed_without_mutation(tmp_path):
    endpoint = MockEndpoint(
        [_candidate()], name="mock://mini-v4", model="mini-v4-model"
    )
    root = tmp_path / "mini-v4"
    _bind_legacy_shadow_manifest(endpoint, root)
    tracked = _files(root)

    with pytest.raises(UnsupportedRunManifestVersionError):
        run(
            [("pi-mini-v4", "Why might this happen?")],
            endpoint,
            budget=100_000,
            root=root,
            vs_k=1,
            max_cycles=1,
        )

    assert _files(root) == tracked


def test_v6_mini_call_is_one_plain_canonical_event_without_workflow_records(
    tmp_path,
):
    endpoint = MockEndpoint(
        [_candidate()], name="mock://mini-v6", model="mini-v6-model"
    )
    root = tmp_path / "mini-v6"

    summary = run(
        [("pi-mini-v6", "Why might this happen?")],
        endpoint,
        budget=100_000,
        root=root,
        vs_k=1,
        max_cycles=1,
    )

    replayed = Harness(root)
    workflow = replayed.workflow_state
    # Mini exercises the parent primitive layer only: the v6 transactional
    # controller (and the retired v4 envelope) leave no records here.
    assert workflow.work_orders == {}
    assert workflow.proposal_receipts == {}
    assert workflow.transaction_work == {}
    call_events = [event for event in replayed.log.read() if event.llm is not None]
    assert len(call_events) == 1
    assert call_events[0].llm.work_order_id is None
    assert call_events[0].llm.dispatch_authorization_ref is None
    assert any(event.rule == Rule.CONJ for event in replayed.log.read())
    assert summary["meter_equals_log"]
    assert verify_root(root)["violations"] == []


def test_mini_v6_repairs_use_the_shared_bounded_repair_protocol(tmp_path):
    content = json.loads(_candidate())["candidates"][0]["content"]
    endpoint = MockEndpoint(
        [
            json.dumps(
                {"candidates": [{"content": content, "typicality": 2.0}]}
            ),
            _candidate(),
        ],
        name="mock://mini-v6-repair",
        model="mini-v6-model",
    )
    root = tmp_path / "mini-v6-repair"

    run(
        [("pi-mini-v6-repair", "Why might this happen?")],
        endpoint,
        budget=100_000,
        root=root,
        vs_k=1,
        max_cycles=1,
    )

    harness = Harness(root)
    call_event, = (
        event for event in harness.log.read() if event.llm is not None
    )
    assert call_event.llm.attempts == 2
    assert [attempt.valid for attempt in call_event.llm.attempt_trace] == [
        False,
        True,
    ]
    report = verify_root(root)
    assert report["violations"] == []
    totals = report["stats"]["process"]["profile_totals"]["compact"]
    assert totals["repair_attempts"] == 1
    assert totals["eventual_valid"] == 1
    assert totals["first_pass_valid"] == 0


def test_mini_v6_schema_exhaustion_is_a_typed_logged_drop(tmp_path):
    content = json.loads(_candidate())["candidates"][0]["content"]
    invalid = json.dumps(
        {"candidates": [{"content": content, "typicality": 2.0}]}
    )
    endpoint = MockEndpoint(
        [invalid, invalid, invalid],
        name="mock://mini-v6-exhausted",
        model="mini-v6-model",
    )
    root = tmp_path / "mini-v6-exhausted"

    summary = run(
        [("pi-mini-v6-exhausted", "Why might this happen?")],
        endpoint,
        budget=100_000,
        root=root,
        vs_k=1,
        max_cycles=1,
    )

    harness = Harness(root)
    dropped, = (
        event
        for event in harness.log.read()
        if event.llm is not None and "dropped-call" in event.inputs
    )
    assert dropped.llm.attempts == 3
    assert not any(attempt.valid for attempt in dropped.llm.attempt_trace)
    assert summary["meter_equals_log"]
    report = verify_root(root)
    assert report["violations"] == []
    assert report["stats"]["process"]["profile_totals"]["compact"][
        "schema_exhausted"
    ] == 1


def test_mini_client_does_not_implement_workflow_records_or_transitions():
    import minireason.loop as mini_loop

    source = inspect.getsource(mini_loop)
    for forbidden in (
        "WorkOrderEnvelopeV1",
        "ProposalReceiptV1",
        "TransitionDecisionV1",
        "record_control_transition",
    ):
        assert forbidden not in source


def test_mini_prebound_v6_manifest_preserves_semantic_diversity_and_executable_utility(
    tmp_path,
):
    families = ("mini-family-alpha", "mini-family-beta")
    bodies = [
        json.dumps(
            {
                "claim": f"A compact explanation from {family}.",
                "mechanism": f"A bounded feedback path preserves {family}.",
                "forbidden": [
                    {
                        "case": "the candidate must remain valid JSON",
                        "eval": "program:json-wf",
                    }
                ],
            },
            sort_keys=True,
        )
        for family in families
    ]
    response = json.dumps(
        {
            "candidates": [
                {"content": body, "typicality": 0.21 + index / 10}
                for index, body in enumerate(bodies)
            ]
        }
    )
    prompts = {"default": [], "prebound": []}

    def endpoint(mode):
        def complete(prompt):
            prompts[mode].append(prompt)
            return response

        return MockEndpoint(
            complete,
            name="mock://mini-d2-semantic",
            model="mini-d2-semantic-model",
        )

    default_endpoint = endpoint("default")
    prebound_endpoint = endpoint("prebound")
    default_root = tmp_path / "default"
    prebound_root = tmp_path / "prebound"
    # Pre-binding through the shared kernel interface (the same call the
    # advisory/scratch phases build on) must be indistinguishable from the
    # manifest mini compiles for itself on first contact.
    prebound = bind_mini_root(prebound_root, prebound_endpoint)
    assert prebound.schema_version == 6
    assert prebound.engine_profile == "mini"

    summaries = {
        "default": run(
            [("pi-mini-d2", "Compare two compact mechanisms.")],
            default_endpoint,
            budget=100_000,
            root=default_root,
            vs_k=2,
            max_cycles=1,
        ),
        "prebound": run(
            [("pi-mini-d2", "Compare two compact mechanisms.")],
            prebound_endpoint,
            budget=100_000,
            root=prebound_root,
            vs_k=2,
            max_cycles=1,
        ),
    }
    assert summaries["prebound"]["run_manifest_sha256"] == prebound.sha256
    harnesses = {
        "default": Harness(default_root),
        "prebound": Harness(prebound_root),
    }

    def semantic_projection(harness):
        artifacts = tuple(
            sorted(
                (
                    artifact.id,
                    programs.content_text(artifact, harness.blobs),
                    harness.state.status[artifact.id].value,
                )
                for artifact in harness.state.artifacts.values()
                if artifact.provenance.role == "conjecturer"
            )
        )
        verdicts = tuple(
            sorted(
                (
                    artifact.id,
                    tuple(
                        programs.evaluate(
                            harness.commitments[commitment_id],
                            artifact,
                            harness.blobs,
                        )[0]
                        for commitment_id in artifact.interface.commitments
                    ),
                )
                for artifact in harness.state.artifacts.values()
                if artifact.provenance.role == "conjecturer"
            )
        )
        return artifacts, verdicts

    default_projection = semantic_projection(harnesses["default"])
    prebound_projection = semantic_projection(harnesses["prebound"])
    assert prompts["prebound"] == prompts["default"]
    assert prebound_projection == default_projection
    artifacts, verdicts = prebound_projection
    assert len(artifacts) == 2
    assert len({content for _id, content, _status in artifacts}) == 2
    assert all(
        any(family in content for _id, content, _status in artifacts)
        for family in families
    )
    assert {artifact_id for artifact_id, _candidate_verdicts in verdicts} == {
        artifact_id for artifact_id, _content, _status in artifacts
    }
    # Every Mini skeleton has its canonical well-formedness check plus the
    # fixture's explicit json-wf check.  Both must remain executable and pass.
    assert all(
        candidate_verdicts == (programs.PASS, programs.PASS)
        for _artifact_id, candidate_verdicts in verdicts
    )
    assert summaries["prebound"]["tokens"] == summaries["default"]["tokens"]
    assert summaries["prebound"]["problems"] == summaries["default"]["problems"]
    assert verify_root(prebound_root)["violations"] == []
    assert verify_root(default_root)["violations"] == []
