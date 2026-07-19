"""V6 imaginative scratch remains structurally atomic and non-formal."""

from __future__ import annotations

import pytest

from deepreason.run_manifest import ScratchAuthoringPolicyV1
from deepreason.scratch.authoring import ScratchAuthoringError, ScratchAuthoringService
from deepreason.scratch.proposals import (
    ScratchBlockDraftBodyV1,
    ScratchNewBlockDraftV1,
    ScratchProposalLinkV1,
    ScratchProposalV1,
)
from deepreason.scratch.service import ScratchService


def _policy() -> ScratchAuthoringPolicyV1:
    return ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=2,
        maximum_revisions_per_turn=1,
        maximum_links_per_turn=2,
        maximum_unresolved_questions_per_turn=1,
        maximum_cluster_suggestions_per_turn=1,
        maximum_total_bytes=32_768,
    )


def test_unknown_reference_is_rejected_before_any_scratch_event(tmp_path):
    service = ScratchService(tmp_path / "scratch")
    author = ScratchAuthoringService(service, object())
    before_events = tuple(service.harness.log.read())
    before_formal = service.harness.state.model_dump(mode="json")

    proposal = ScratchProposalV1(
        new_blocks=(
            ScratchNewBlockDraftV1(
                local_key="NEW_001",
                body=ScratchBlockDraftBodyV1(
                    content="Perhaps the mechanism is both causal and epiphenomenal."
                ),
            ),
        ),
        links=(
            ScratchProposalLinkV1(
                from_ref="NEW_001",
                to_ref="SCR_999",
                relation_hint="wild unresolved relation",
            ),
        ),
    )

    with pytest.raises(ScratchAuthoringError, match="SCRATCH_ALIAS_UNKNOWN"):
        author.admit_proposal(
            proposal,
            policy=_policy(),
            visible_aliases={},
            context_ref="transaction:test",
        )

    assert tuple(service.harness.log.read()) == before_events
    assert not service.state.blocks
    assert not service.state.links
    assert service.harness.state.model_dump(mode="json") == before_formal


def test_contradictory_speculation_is_admitted_only_to_scratch(tmp_path):
    service = ScratchService(tmp_path / "scratch")
    author = ScratchAuthoringService(service, object())
    before_formal = service.harness.state.model_dump(mode="json")
    proposal = ScratchProposalV1(
        new_blocks=(
            ScratchNewBlockDraftV1(
                local_key="NEW_001",
                body=ScratchBlockDraftBodyV1(
                    content=(
                        "Counterfactual: assume X and not-X provisionally; invent a "
                        "mechanism that would make the tension experimentally useful."
                    ),
                    unfinished="This may be wrong, impossible, or self-contradictory.",
                ),
            ),
        )
    )

    outputs = author.admit_proposal(
        proposal,
        policy=_policy(),
        visible_aliases={},
        context_ref="transaction:test",
    )

    assert outputs[0] in service.state.blocks
    assert service.harness.state.model_dump(mode="json") == before_formal
    assert outputs[0] not in service.harness.state.artifacts
    assert outputs[0] not in service.harness.commitments


def test_restart_consumes_durable_prefix_and_appends_only_missing_suffix(
    tmp_path,
    monkeypatch,
):
    service = ScratchService(tmp_path / "scratch-restart")
    author = ScratchAuthoringService(service, object())
    proposal = ScratchProposalV1(
        new_blocks=(
            ScratchNewBlockDraftV1(
                local_key="NEW_001",
                body=ScratchBlockDraftBodyV1(content="Wild mechanism A"),
            ),
            ScratchNewBlockDraftV1(
                local_key="NEW_002",
                body=ScratchBlockDraftBodyV1(content="Contradictory mechanism B"),
            ),
        ),
        links=(
            ScratchProposalLinkV1(
                from_ref="NEW_001",
                to_ref="NEW_002",
                relation_hint="unresolved imaginative tension",
            ),
        ),
    )
    original_create_link = service.create_link

    def crash_before_suffix(*_args, **_kwargs):
        raise OSError("injected crash after durable block prefix")

    monkeypatch.setattr(service, "create_link", crash_before_suffix)
    with pytest.raises(OSError, match="durable block prefix"):
        author.admit_proposal(
            proposal,
            policy=_policy(),
            visible_aliases={},
            context_ref="transaction:restart-prefix",
        )

    prefix_events = tuple(service.harness.log.read())
    assert len(prefix_events) == 2
    prefix_ids = tuple(
        output
        for event in prefix_events
        for output in event.outputs
    )

    monkeypatch.setattr(service, "create_link", original_create_link)
    outputs = author.admit_proposal(
        proposal,
        policy=_policy(),
        visible_aliases={},
        context_ref="transaction:restart-prefix",
    )
    events = tuple(service.harness.log.read())
    assert len(events) == 3
    assert outputs[:2] == prefix_ids
    assert outputs[2] in service.state.links

    replayed = author.admit_proposal(
        proposal,
        policy=_policy(),
        visible_aliases={},
        context_ref="transaction:restart-prefix",
    )
    assert replayed == outputs
    assert tuple(service.harness.log.read()) == events

