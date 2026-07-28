"""In-run research capability: allowlisted, budgeted, receipted, replayed.

Increment B of the research backend (docs/RESEARCH_BACKEND.md): the
controller drives the full capability chain PROPOSED → VALIDATED →
GRANTED/DENIED → COMPILED → DISPATCHED → SUCCEEDED/FAILED →
RESULT_PACKAGED → CONSUMED over the shared transition machinery, and the
replayed capability state is the only budget authority.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.models import (
    ResearchExecutionReceiptV1,
    ResearchFetchAttemptV1,
    ResearchFetchProposalDraftV1,
)
from deepreason.capabilities.policy import (
    InquiryCapabilityPolicyV1,
    ResearchCapabilityPolicyV1,
)
from deepreason.capabilities.research import ResearchCapabilityController
from deepreason.harness import Harness
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.workflow.models import CapabilityOutcome


PAGE = b"<html><body><h1>Tides</h1><p>The moon pulls the sea.</p></body></html>"


def _policy(**updates) -> ResearchCapabilityPolicyV1:
    values = {
        "enabled": True,
        "backend_identity": "web.contained.v1",
        "maximum_requests": 3,
        "maximum_sources": 2,
        "domain_allowlist": ("example.org",),
        "maximum_response_bytes": 65_536,
    }
    values.update(updates)
    return ResearchCapabilityPolicyV1(**values)


def _manifest(policy: ResearchCapabilityPolicyV1) -> SimpleNamespace:
    return SimpleNamespace(
        schema_version=6,
        sha256="a" * 64,
        run_input_digest="b" * 64,
        inquiry_capability_policy=SimpleNamespace(research=policy),
    )


def _work_order() -> SimpleNamespace:
    return SimpleNamespace(
        id="sha256:" + "c" * 64,
        problem_ref="pi-research",
        capability_grant=SimpleNamespace(
            allowed_outcomes=(CapabilityOutcome.RESEARCH_REQUEST,)
        ),
    )


def _transport(script):
    calls = []

    def transport(url, timeout, maximum_bytes):
        calls.append(url)
        entry = script[url]
        if isinstance(entry, Exception):
            raise entry
        return entry

    transport.calls = calls
    return transport


def _controller(tmp_path, policy, transport):
    harness = Harness(tmp_path / "run")
    harness.register_commitment(
        Commitment(id="k-tides", eval="predicate:True", observation_valued=True)
    )
    problem = harness.register_problem(
        Problem(
            id="pi-research",
            description="explain the tides",
            criteria=["k-tides"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    controller = ResearchCapabilityController(
        harness, _manifest(policy), transport=transport
    )
    return harness, problem, controller


def _draft(*urls: str) -> ResearchFetchProposalDraftV1:
    return ResearchFetchProposalDraftV1(
        request_identifier="req-1",
        purpose="find the published tide mechanism",
        urls=tuple(urls) or ("https://example.org/tides",),
    )


def test_full_chain_fetches_packages_and_consumes(tmp_path):
    transport = _transport(
        {"https://example.org/tides": (200, "text/html", None, PAGE)}
    )
    harness, problem, controller = _controller(tmp_path, _policy(), transport)
    work_order = _work_order()

    proposal = controller.propose(
        _draft(),
        proposal_index=0,
        work_order=work_order,
        source_call_seq=1,
        formal_fence_seq=4,
        scratch_fence_seq=4,
    )
    package = controller.execute(
        proposal, formal_fence_seq=4, scratch_fence_seq=4
    )
    assert package is not None and len(package.items) == 1
    item = package.items[0]
    assert item.content_sha256 == hashlib.sha256(PAGE).hexdigest()
    assert "moon pulls the sea" in harness.blobs.get(item.text_sha256).decode()

    evidence_refs = controller.consume(
        proposal, package, problem, formal_fence_seq=4, scratch_fence_seq=4
    )
    assert len(evidence_refs) == 1

    state = harness.capability_state
    lifecycles = [t.lifecycle for t in state.transitions.values()]
    assert lifecycles.count(CapabilityLifecycle.PROPOSED) == 1
    assert lifecycles.count(CapabilityLifecycle.CONSUMED) == 1
    receipt = next(iter(state.receipts.values()))
    assert receipt.outcome == "fetched"
    assert receipt.requests_used_total == 1 and receipt.requests_limit == 3

    # Replay from the log alone re-derives the identical capability state.
    reloaded = Harness(tmp_path / "run")
    assert reloaded.capability_state.digest == state.digest
    assert reloaded.capability_state.execution_count == 1


def test_off_allowlist_proposal_is_denied_without_dispatch(tmp_path):
    transport = _transport({})
    harness, _problem, controller = _controller(tmp_path, _policy(), transport)
    proposal = controller.propose(
        _draft("https://evil.example.com/x"),
        proposal_index=0,
        work_order=_work_order(),
        source_call_seq=1,
        formal_fence_seq=4,
        scratch_fence_seq=4,
    )
    assert (
        controller.execute(proposal, formal_fence_seq=4, scratch_fence_seq=4)
        is None
    )
    assert transport.calls == []
    denials = [
        t
        for t in harness.capability_state.transitions.values()
        if t.lifecycle == CapabilityLifecycle.DENIED
    ]
    assert len(denials) == 1
    assert denials[0].reason_code == "url_outside_frozen_allowlist"


def test_budget_is_cumulative_and_exhaustion_is_typed(tmp_path):
    transport = _transport(
        {
            "https://example.org/a": (200, "text/plain", None, b"alpha"),
            "https://example.org/b": (200, "text/plain", None, b"beta"),
            "https://example.org/c": (200, "text/plain", None, b"gamma"),
            "https://example.org/d": (200, "text/plain", None, b"delta"),
        }
    )
    harness, _problem, controller = _controller(tmp_path, _policy(), transport)
    work_order = _work_order()

    first = controller.propose(
        _draft("https://example.org/a", "https://example.org/b"),
        proposal_index=0,
        work_order=work_order,
        source_call_seq=1,
        formal_fence_seq=4,
        scratch_fence_seq=4,
    )
    controller.execute(first, formal_fence_seq=4, scratch_fence_seq=4)

    second = controller.propose(
        _draft("https://example.org/c", "https://example.org/d"),
        proposal_index=1,
        work_order=work_order,
        source_call_seq=2,
        formal_fence_seq=4,
        scratch_fence_seq=4,
    )
    package = controller.execute(
        second, formal_fence_seq=4, scratch_fence_seq=4
    )
    # 3-request budget: a+b spent 2, c spent the third, d is the typed
    # exhaustion attempt carrying count and limit (the grounded shape).
    receipts = sorted(
        (
            r
            for r in harness.capability_state.receipts.values()
            if isinstance(r, ResearchExecutionReceiptV1)
        ),
        key=lambda r: r.requests_used_total,
    )
    assert [r.requests_used_total for r in receipts] == [2, 3]
    last = receipts[-1]
    assert last.outcome == "budget_exhausted"
    exhausted = [
        a for a in last.attempts if a.outcome == "RESEARCH_BUDGET_EXHAUSTED"
    ]
    assert len(exhausted) == 1 and exhausted[0].requests_used == 3
    assert last.requests_limit == 3
    assert len(package.items) == 1  # c still landed
    assert "https://example.org/d" not in transport.calls

    # A third proposal is denied outright: nothing left to spend.
    third = controller.propose(
        _draft("https://example.org/a"),
        proposal_index=2,
        work_order=work_order,
        source_call_seq=3,
        formal_fence_seq=4,
        scratch_fence_seq=4,
    )
    assert (
        controller.execute(third, formal_fence_seq=4, scratch_fence_seq=4)
        is None
    )


def test_source_consumption_is_capped_by_the_frozen_policy(tmp_path):
    transport = _transport(
        {
            "https://example.org/a": (200, "text/plain", None, b"alpha"),
            "https://example.org/b": (200, "text/plain", None, b"beta"),
            "https://example.org/c": (200, "text/plain", None, b"gamma"),
        }
    )
    harness, problem, controller = _controller(
        tmp_path, _policy(maximum_requests=10), transport
    )
    work_order = _work_order()
    proposal = controller.propose(
        _draft(
            "https://example.org/a",
            "https://example.org/b",
            "https://example.org/c",
        ),
        proposal_index=0,
        work_order=work_order,
        source_call_seq=1,
        formal_fence_seq=4,
        scratch_fence_seq=4,
    )
    package = controller.execute(
        proposal, formal_fence_seq=4, scratch_fence_seq=4
    )
    assert len(package.items) == 3
    evidence_refs = controller.consume(
        proposal, package, problem, formal_fence_seq=4, scratch_fence_seq=4
    )
    assert len(evidence_refs) == 2  # maximum_sources caps the run


def test_receipt_arithmetic_is_model_enforced():
    attempt = ResearchFetchAttemptV1(
        seq=1,
        url="https://example.org/a",
        outcome="FETCHED",
        requests_used=4,
        content_sha256="d" * 64,
    )
    with pytest.raises(ValueError, match="beyond its frozen limit"):
        ResearchExecutionReceiptV1.create(
            proposal_ref="sha256:" + "e" * 64,
            run_input_digest="b" * 64,
            research_work_order_ref="sha256:" + "f" * 64,
            compiled_specification_ref="sha256:" + "a" * 64,
            attempts=(attempt,),
            requests_used_total=4,
            requests_limit=3,
            outcome="fetched",
        )


def test_work_order_without_research_grant_cannot_propose(tmp_path):
    harness, _problem, controller = _controller(
        tmp_path, _policy(), _transport({})
    )
    bare = SimpleNamespace(
        id="sha256:" + "c" * 64,
        problem_ref="pi-research",
        capability_grant=SimpleNamespace(
            allowed_outcomes=(CapabilityOutcome.SIMULATION_REQUEST,)
        ),
    )
    with pytest.raises(ValueError, match="does not permit a research proposal"):
        controller.propose(
            _draft(),
            proposal_index=0,
            work_order=bare,
            source_call_seq=1,
            formal_fence_seq=4,
            scratch_fence_seq=4,
        )


def test_v6_manifest_gate_accepts_only_the_contained_backend():
    """The compile gate lifts exactly for web.contained.v1 (the implemented
    runtime); every other research backend identity stays refused."""

    from deepreason.run_manifest import _validate_v6_capability_policy
    from tests.test_cli_production_doctor_v6 import _manifest as v6_manifest

    manifest = v6_manifest()
    contained = manifest.model_copy(
        update={
            "inquiry_capability_policy": (
                manifest.inquiry_capability_policy.model_copy(
                    update={"research": _policy()}
                )
            )
        }
    )
    _validate_v6_capability_policy(contained)  # must not raise

    foreign = manifest.model_copy(
        update={
            "inquiry_capability_policy": (
                manifest.inquiry_capability_policy.model_copy(
                    update={
                        "research": _policy(backend_identity="search@future")
                    }
                )
            )
        }
    )
    with pytest.raises(ValueError, match="V6_RESEARCH_UNAVAILABLE"):
        _validate_v6_capability_policy(foreign)


def test_consumed_fetches_become_citable_byte_checked_blocks(tmp_path):
    """Increment C: fetched material is segmented by the canonical admission
    parser, its block ids surface on the attackable reliability node, and
    the §4 citation checker byte-verifies quotes against the exact fetched
    text — same discipline as an attached dossier."""

    from deepreason.capabilities.research import consumed_research_blocks
    from deepreason.evidence.citations import (
        EVIDENCE_CITATION_VERIFIED,
        EVIDENCE_QUOTE_MISMATCH,
        check_candidate_citations,
    )
    from deepreason.llm.contracts import EvidenceRefClaimV1

    transport = _transport(
        {"https://example.org/tides": (200, "text/html", None, PAGE)}
    )
    harness, problem, controller = _controller(tmp_path, _policy(), transport)
    proposal = controller.propose(
        _draft(),
        proposal_index=0,
        work_order=_work_order(),
        source_call_seq=1,
        formal_fence_seq=4,
        scratch_fence_seq=4,
    )
    package = controller.execute(
        proposal, formal_fence_seq=4, scratch_fence_seq=4
    )
    evidence_refs = controller.consume(
        proposal, package, problem, formal_fence_seq=4, scratch_fence_seq=4
    )

    blocks = consumed_research_blocks(harness)
    assert blocks, "consumed fetches must mint citable blocks"
    block = blocks[0]

    # The reliability node advertises the citable block ids in packs.
    evidence = harness.state.artifacts[evidence_refs[0]]
    reliability_ref = next(
        ref.target for ref in evidence.interface.refs if ref.role == "dependence"
    )
    reliability = harness.state.artifacts[reliability_ref]
    assert block.id[:16] in reliability.content_ref

    # Quote byte-checks resolve through the content-addressed text blob.
    canonical = harness.blobs.get(block.source_sha256).decode("utf-8")[
        block.span_start : block.span_end
    ]
    verified = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id, quote=canonical),),
        None,
        harness.blobs,
        extra_blocks=blocks,
    )
    assert [c.code for c in verified] == [EVIDENCE_CITATION_VERIFIED]

    reworded = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id, quote=canonical + " reworded"),),
        None,
        harness.blobs,
        extra_blocks=blocks,
    )
    assert [c.code for c in reworded] == [EVIDENCE_QUOTE_MISMATCH]

    # Determinism: re-derivation from a fresh replay mints identical ids.
    reloaded = Harness(tmp_path / "run")
    assert [b.id for b in consumed_research_blocks(reloaded)] == [
        b.id for b in blocks
    ]
