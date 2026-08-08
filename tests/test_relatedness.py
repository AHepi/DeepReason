"""Relatedness-claim mechanism (D2 rev 2, R43/R35/M21/M27): mint,
read, and the referee-free relatedness trial that can strip protection
from one commitment without a faithfulness referee (Amendment 1)."""

import json

from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Status, WarrantType
from deepreason.rules.relatedness import (
    mint_relatedness_claim,
    relatedness_claim_holds,
    relatedness_trial,
)

PASS_RULING = json.dumps({"verdict": "pass", "decisive_point": "doubling composes"})
FAIL_RULING = json.dumps({"verdict": "fail", "decisive_point": "doubling composes"})

CONJECTURE_TEXT = "doubling composes with addition: multiplying by two is repeated addition."


def _judge_adapter(harness, judge1, judge2):
    return LLMAdapter(
        {
            "judge": [
                MockEndpoint(judge1, name="mock://judge-gemma", model="gemma-test"),
                MockEndpoint(judge2, name="mock://judge-qwen", model="qwen-test"),
            ],
        },
        harness.blobs,
        retry_max=2,
    )


def test_mint_relatedness_claim_links_via_mention_and_carries_the_commitment(harness):
    from deepreason.ontology import Ref
    from deepreason.ontology.artifact import RefRole
    from deepreason.programs import content_text

    conjecture = harness.create_artifact(CONJECTURE_TEXT)
    claim_id = mint_relatedness_claim(
        harness, conjecture.id, "some-commitment-id", "the checker tests exactly the doubling claim"
    )
    claim = harness.state.artifacts[claim_id]
    data = json.loads(content_text(claim, harness.blobs))
    assert data["commitment"] == "some-commitment-id"
    assert claim.interface.refs == [Ref(target=conjecture.id, role=RefRole.MENTION)]
    assert harness.state.status[claim_id] == Status.ACCEPTED
    assert relatedness_claim_holds(harness, conjecture.id, "some-commitment-id") is True


def test_no_linked_claim_is_the_opt_out_default(harness):
    conjecture = harness.create_artifact(CONJECTURE_TEXT)
    assert relatedness_claim_holds(harness, conjecture.id, "never-minted") is True


def test_relatedness_trial_unanimous_pass_leaves_the_claim_accepted(harness):
    conjecture = harness.create_artifact(CONJECTURE_TEXT)
    claim_id = mint_relatedness_claim(
        harness, conjecture.id, "k-checker", "the checker tests exactly the doubling claim"
    )
    claim = harness.state.artifacts[claim_id]
    adapter = _judge_adapter(harness, [PASS_RULING], [PASS_RULING])

    result = relatedness_trial(harness, claim, CONJECTURE_TEXT, adapter, config=None)

    assert result is True
    assert harness.state.status[claim_id] == Status.ACCEPTED
    assert not any(w.target == claim_id for w in harness.warrants.values())


def test_relatedness_trial_sustained_challenge_refutes_only_the_claim(harness):
    """R35/R43: a losing relatedness trial registers an ARGUMENTATIVE fail
    warrant against the RELATEDNESS-CLAIM artifact -- never the conjecture
    or the commitment -- mirroring relevance_trial's own target choice."""
    conjecture = harness.create_artifact(CONJECTURE_TEXT)
    claim_id = mint_relatedness_claim(
        harness, conjecture.id, "k-checker", "the checker tests exactly the doubling claim"
    )
    claim = harness.state.artifacts[claim_id]
    adapter = _judge_adapter(harness, [PASS_RULING], [FAIL_RULING])

    result = relatedness_trial(harness, claim, CONJECTURE_TEXT, adapter, config=None)

    assert result is False
    assert harness.state.status[claim_id] == Status.REFUTED
    assert harness.state.status[conjecture.id] == Status.ACCEPTED
    warrant = next(w for w in harness.warrants.values() if w.target == claim_id)
    assert warrant.type == WarrantType.ARGUMENTATIVE
    assert relatedness_claim_holds(harness, conjecture.id, "k-checker") is False
