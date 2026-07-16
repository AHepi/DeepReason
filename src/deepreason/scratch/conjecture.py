"""Pure planning and just-in-time commit for ordinary Conj scratch context."""

from __future__ import annotations

import hashlib

from pydantic import Field, model_validator

from deepreason.canonical import canonical_json
from deepreason.ontology.event import ConjectureContextCallReceiptV1
from deepreason.ontology.problem import Problem
from deepreason.run_manifest import ConjectureContextPolicyV1, ScratchPolicy
from deepreason.scratch.attention import (
    AttentionPackV1,
    AttentionPlanner,
    AttentionPolicyV1,
    AttentionRequestV1,
)
from deepreason.scratch.contracts import SCRATCH_CONTRACT_INSTRUCTIONS
from deepreason.scratch.errors import ScratchReadOnly
from deepreason.scratch.models import (
    AdvisoryContextV1,
    RetrievalChannel,
    ScratchRecord,
    domain_hash,
)
from deepreason.scratch.render import RenderedScratchPackV1, ScratchRenderer
from deepreason.scratch.service import ScratchService


class ConjectureContextStale(RuntimeError):
    """The append-only state advanced after a context plan was prepared."""

    code = "CONJECTURE_CONTEXT_STALE"

    def __init__(self) -> None:
        super().__init__(f"{self.code}: rebuild the advisory context plan")


class PlannedConjectureContextV1(ScratchRecord):
    """Immutable pure result; no receipt is durable until commit."""

    formal_fence_seq: int = Field(ge=0)
    scratch_fence_seq: int = Field(ge=0)
    problem_id: str = Field(min_length=1, max_length=512)
    school_id: str | None = Field(
        default=None, pattern=r"^school-(0|[1-9][0-9]*)$"
    )
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    attention_policy_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    attention_policy: AttentionPolicyV1
    attention_pack: AttentionPackV1
    advisory_context: AdvisoryContextV1
    rendered_context: RenderedScratchPackV1

    @model_validator(mode="after")
    def _parts_share_one_fence_and_selection(self):
        if self.formal_fence_seq != self.scratch_fence_seq:
            raise ValueError("formal and scratch context fences must name one event prefix")
        if self.attention_pack.state_seq != self.scratch_fence_seq:
            raise ValueError("attention pack does not match the scratch fence")
        selection = self.attention_pack.selection_receipt
        if self.advisory_context.retrieval_receipt != selection.id:
            raise ValueError("advisory context does not name the selection receipt")
        if self.rendered_context.receipt.attention_receipt != selection.id:
            raise ValueError("render receipt does not name the selection receipt")
        expected_policy = domain_hash(
            "conjecture.attention.policy.v1", self.attention_policy
        )
        if self.attention_policy_hash != expected_policy:
            raise ValueError("attention policy hash does not match the planned policy")
        return self


def _bounded_attention_policy(
    scratch_policy: ScratchPolicy,
    context_policy: ConjectureContextPolicyV1,
) -> AttentionPolicyV1:
    base = scratch_policy.attention_policy()
    maximum_blocks = min(
        base.max_blocks_per_pack,
        context_policy.initial_max_blocks,
    )
    values = base.model_dump(mode="json", by_alias=True)
    values["max_blocks_per_pack"] = maximum_blocks
    values["max_guides_per_pack"] = min(
        base.max_guides_per_pack,
        context_policy.initial_max_guides,
    )
    permitted = set(context_policy.permitted_retrieval_channels)
    values["coverage_enabled"] = bool(
        base.coverage_enabled and "coverage" in permitted
    )
    if (
        context_policy.exploration_slot_mandatory
        and "exploratory" in permitted
        and maximum_blocks
    ):
        values["exploratory_fraction"] = max(
            base.exploratory_fraction,
            1 / maximum_blocks,
        )
    return AttentionPolicyV1.model_validate(values)


def _focus_blocks(
    service: ScratchService,
    problem: Problem,
    *,
    limit: int,
) -> list[str]:
    formal_targets = {
        problem.id,
        *(
            artifact_id
            for artifact_id, problem_id in service.harness.state.addr
            if problem_id == problem.id
        ),
    }
    explicit = [
        block.id
        for block in sorted(
            service.state.blocks.values(),
            key=lambda item: (item.instance.seq, item.id),
        )
        if formal_targets.intersection(block.provenance.formal_artifact_refs)
    ]
    literal = [
        block.id
        for block in service.search_phrase(problem.description, max(1, limit * 4))
    ]
    return list(dict.fromkeys([*explicit, *literal]))[:limit]


def _seed(
    manifest_digest: str,
    problem_id: str,
    school_id: str | None,
    formal_fence_seq: int,
    scratch_fence_seq: int,
) -> int:
    payload = canonical_json(
        {
            "manifest_digest": manifest_digest,
            "problem_id": problem_id,
            "school_id": school_id,
            "formal_fence_seq": formal_fence_seq,
            "scratch_fence_seq": scratch_fence_seq,
        }
    )
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def plan_conjecture_context(
    service: ScratchService,
    *,
    problem: Problem,
    school_id: str | None,
    manifest_digest: str,
    scratch_policy: ScratchPolicy,
    context_policy: ConjectureContextPolicyV1,
    formal_fence_seq: int,
    scratch_fence_seq: int,
) -> PlannedConjectureContextV1 | None:
    """Prepare exact advisory bytes without mutating any store or state."""

    if service.read_only:
        raise ScratchReadOnly("historical scratch views cannot plan future Conj work")
    problem = Problem.model_validate(problem)
    scratch_policy = ScratchPolicy.model_validate(scratch_policy)
    context_policy = ConjectureContextPolicyV1.model_validate(context_policy)
    current = service.harness._next_seq - 1
    if formal_fence_seq != current or scratch_fence_seq != current:
        raise ConjectureContextStale()
    if service.harness.state.problems.get(problem.id) != problem:
        raise ValueError("problem is not canonical at the supplied formal fence")
    if (
        context_policy.mode == "disabled"
        or not scratch_policy.enabled
        or context_policy.initial_max_blocks == 0
        or not service.state.blocks
    ):
        return None

    attention_policy = _bounded_attention_policy(scratch_policy, context_policy)
    permitted = tuple(
        RetrievalChannel(value)
        for value in context_policy.permitted_retrieval_channels
    )
    allowed = set(permitted)
    focus = (
        _focus_blocks(
            service,
            problem,
            limit=attention_policy.max_blocks_per_pack,
        )
        if RetrievalChannel.FOCUS in allowed
        else []
    )
    clusters = (
        sorted(
            {
                cluster_id
                for block_id in focus
                for cluster_id in service.state.clusters_by_block.get(block_id, set())
            }
        )
        if RetrievalChannel.CLUSTER in allowed
        else []
    )
    request = AttentionRequestV1(
        focus_blocks=focus or None,
        focus_clusters=clusters or None,
        permitted_channels=list(permitted),
        maximum_blocks=attention_policy.max_blocks_per_pack,
        maximum_cluster_guides=attention_policy.max_guides_per_pack,
        include_nearby=bool(
            allowed
            & {
                RetrievalChannel.LINK,
                RetrievalChannel.CLUSTER,
                RetrievalChannel.KEYWORD,
                RetrievalChannel.SEMANTIC,
            }
        ),
        include_recent=RetrievalChannel.RECENT in allowed,
        include_loose=RetrievalChannel.LOOSE in allowed,
        include_dormant=RetrievalChannel.DORMANT in allowed,
        include_underexposed=RetrievalChannel.UNDEREXPOSED in allowed,
        include_exploratory=RetrievalChannel.EXPLORATORY in allowed,
        deterministic_seed=_seed(
            manifest_digest,
            problem.id,
            school_id,
            formal_fence_seq,
            scratch_fence_seq,
        ),
    )
    pack = AttentionPlanner(service, attention_policy).plan(request)
    if not pack.blocks:
        return None
    context = service.prepare_advisory_context(
        pack,
        warning=SCRATCH_CONTRACT_INSTRUCTIONS,
    )
    rendered = ScratchRenderer(service).render_advisory_context(pack, context)
    return PlannedConjectureContextV1(
        formal_fence_seq=formal_fence_seq,
        scratch_fence_seq=scratch_fence_seq,
        problem_id=problem.id,
        school_id=school_id,
        manifest_digest=manifest_digest,
        attention_policy_hash=domain_hash(
            "conjecture.attention.policy.v1", attention_policy
        ),
        attention_policy=attention_policy,
        attention_pack=pack,
        advisory_context=context,
        rendered_context=rendered,
    )


def commit_conjecture_context(
    service: ScratchService,
    plan: PlannedConjectureContextV1,
    *,
    final_conjecture_pack: str,
    attention_policy: AttentionPolicyV1,
) -> ConjectureContextCallReceiptV1:
    """Commit a pure plan immediately before its exact model call."""

    if service.read_only:
        raise ScratchReadOnly("historical scratch views cannot commit Conj context")
    plan = PlannedConjectureContextV1.model_validate(plan)
    attention_policy = AttentionPolicyV1.model_validate(attention_policy)
    current = service.harness._next_seq - 1
    if current != plan.formal_fence_seq or current != plan.scratch_fence_seq:
        raise ConjectureContextStale()
    if domain_hash("conjecture.attention.policy.v1", attention_policy) != (
        plan.attention_policy_hash
    ):
        raise ValueError("attention policy differs from the planned policy")
    expected_context = service.prepare_advisory_context(
        plan.attention_pack,
        warning=SCRATCH_CONTRACT_INSTRUCTIONS,
    )
    if expected_context != plan.advisory_context:
        raise ValueError("prepared advisory context differs from the plan")
    renderer = ScratchRenderer(service)
    rendered = renderer.render_advisory_context(
        plan.attention_pack,
        expected_context,
    )
    if rendered != plan.rendered_context:
        raise ValueError("rendered advisory context differs from the plan")
    if final_conjecture_pack.count(rendered.text) != 1:
        raise ValueError("final Conj pack must contain the exact advisory context once")

    render_receipt_ref = renderer.persist_receipt(rendered.receipt)
    rendered_context_ref = service.harness.blobs.put(rendered.text.encode("utf-8"))
    committed = service.commit_prepared_advisory_context(
        plan.attention_pack,
        expected_context,
        context_ref=render_receipt_ref,
        coverage_policy=attention_policy,
    )
    return ConjectureContextCallReceiptV1(
        manifest_digest=plan.manifest_digest,
        problem_id=plan.problem_id,
        school_id=plan.school_id,
        formal_fence_seq=plan.formal_fence_seq,
        scratch_fence_seq=plan.scratch_fence_seq,
        selection_receipt_ref=plan.attention_pack.selection_receipt.id,
        advisory_context_ref=committed.id,
        render_receipt_ref=render_receipt_ref,
        rendered_context_ref=rendered_context_ref,
    )


ConjectureContextPlanV1 = PlannedConjectureContextV1


__all__ = [
    "ConjectureContextCallReceiptV1",
    "ConjectureContextPlanV1",
    "ConjectureContextStale",
    "PlannedConjectureContextV1",
    "commit_conjecture_context",
    "plan_conjecture_context",
]
