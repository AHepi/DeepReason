"""Pure planning and just-in-time commit for ordinary Conj scratch context."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping

from pydantic import Field, model_validator

from deepreason.canonical import canonical_json
from deepreason.conjecture_turn import ContextRequestV1
from deepreason.ontology.event import ConjectureContextCallReceiptV1
from deepreason.ontology.problem import Problem
from deepreason.run_manifest import ConjectureContextPolicyV1, ScratchPolicy
from deepreason.scratch.attention import (
    AttentionPackV1,
    AttentionPlanner,
    AttentionPolicyV1,
    AttentionRequestV1,
    GuideSelectionV1,
)
from deepreason.scratch.contracts import SCRATCH_CONTRACT_INSTRUCTIONS
from deepreason.scratch.errors import ScratchReadOnly
from deepreason.scratch.models import (
    AdvisoryContextV1,
    RetrievalChannel,
    ScratchRecord,
    domain_hash,
)
from deepreason.scratch.render import (
    RenderedScratchPackV1,
    ScratchRenderer,
    ScratchRenderReceiptV1,
)
from deepreason.scratch.service import ScratchService


class ConjectureContextStale(RuntimeError):
    """The append-only state advanced after a context plan was prepared."""

    code = "CONJECTURE_CONTEXT_STALE"

    def __init__(self) -> None:
        super().__init__(f"{self.code}: rebuild the advisory context plan")


def _v6_aliases_for_render_receipt(
    receipt: ScratchRenderReceiptV1,
) -> tuple[dict[str, str], dict[str, str]]:
    aliases: dict[str, str] = {}
    replacements: dict[str, str] = {}
    for handle_map in (
        receipt.block_handles,
        receipt.cluster_handles,
        receipt.link_handles,
        receipt.guide_handles,
    ):
        for handle, target in handle_map.items():
            if target in aliases.values():
                raise ValueError("canonical scratch target has multiple render handles")
            alias = f"SCR_{len(aliases) + 1:03d}"
            aliases[alias] = target
            replacements[handle] = alias
    return aliases, replacements


def _replace_local_handles(text: str, replacements: Mapping[str, str]) -> str:
    for handle, alias in sorted(
        replacements.items(), key=lambda item: (-len(item[0]), item[0])
    ):
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(handle)}(?![A-Za-z0-9_])"
        text = re.sub(pattern, alias, text)
    return text


def render_v6_conjecture_context(
    plan: PlannedConjectureContextV1,
) -> tuple[str, dict[str, str]]:
    """Return the exact v6 model-facing render and canonical SCR aliases."""

    plan = PlannedConjectureContextV1.model_validate(plan)
    aliases, replacements = _v6_aliases_for_render_receipt(
        plan.rendered_context.receipt
    )
    return _replace_local_handles(plan.rendered_context.text, replacements), aliases


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
    expansion_decision_ref: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
        exclude_if=lambda value: value is None,
    )
    prior_selection_receipt_ref: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
        exclude_if=lambda value: value is None,
    )
    root_block_ids: tuple[str, ...] | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    expansion_request_hash: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
        exclude_if=lambda value: value is None,
    )
    expansion_index: int | None = Field(
        default=None,
        ge=1,
        le=8,
        exclude_if=lambda value: value is None,
    )
    added_block_refs: tuple[str, ...] | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

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
        if (
            self.prior_selection_receipt_ref is not None
            and self.expansion_decision_ref is None
        ):
            raise ValueError(
                "a prior selection requires its expansion decision"
            )
        if self.root_block_ids is not None:
            if len(self.root_block_ids) != len(set(self.root_block_ids)):
                raise ValueError("root context blocks must not contain duplicates")
            if not set(self.root_block_ids).issubset(
                self.attention_pack.selection_receipt.final_order
            ):
                raise ValueError("expanded context must retain every root block")
        lineage = (
            self.expansion_request_hash,
            self.expansion_index,
            self.added_block_refs,
        )
        if self.expansion_decision_ref is None and any(
            value is not None for value in lineage
        ):
            raise ValueError("expansion lineage requires a decision")
        if self.expansion_decision_ref is not None and any(
            value is None for value in lineage
        ):
            raise ValueError("expanded plans require complete lineage")
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


def _expanded_attention_policy(
    scratch_policy: ScratchPolicy,
    context_policy: ConjectureContextPolicyV1,
    *,
    maximum_blocks: int,
) -> AttentionPolicyV1:
    base = scratch_policy.attention_policy()
    values = base.model_dump(mode="json", by_alias=True)
    values["max_blocks_per_pack"] = maximum_blocks
    values["max_guides_per_pack"] = min(
        base.max_guides_per_pack,
        context_policy.initial_max_guides,
    )
    limits = dict(values["per_channel_limits"])
    limits[RetrievalChannel.FOCUS.value] = max(
        maximum_blocks,
        limits[RetrievalChannel.FOCUS.value],
    )
    values["per_channel_limits"] = limits
    permitted = set(context_policy.permitted_retrieval_channels)
    values["coverage_enabled"] = bool(
        base.coverage_enabled and "coverage" in permitted
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


def _expansion_seed(
    manifest_digest: str,
    problem_id: str,
    school_id: str | None,
    decision_ref: str,
    request_hash: str,
) -> int:
    payload = canonical_json(
        {
            "manifest_digest": manifest_digest,
            "problem_id": problem_id,
            "school_id": school_id,
            "decision_ref": decision_ref,
            "request_hash": request_hash,
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


def prepare_conjecture_context_call(
    service: ScratchService,
    plan: PlannedConjectureContextV1,
    *,
    final_conjecture_pack: str,
    attention_policy: AttentionPolicyV1,
    model_facing_rendered_context: str | None = None,
    model_facing_aliases: Mapping[str, str] | None = None,
    validate_call_receipt: Callable[[ConjectureContextCallReceiptV1], None]
    | None = None,
) -> ConjectureContextCallReceiptV1:
    """Seal and validate exact call context without recording consumption."""

    if service.read_only:
        raise ScratchReadOnly("historical scratch views cannot prepare Conj context")
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
    if (model_facing_rendered_context is None) != (model_facing_aliases is None):
        raise ValueError("model-facing context requires both rendered bytes and aliases")
    receipt_text = rendered.text
    if model_facing_rendered_context is not None:
        expected_text, expected_aliases = render_v6_conjecture_context(plan)
        if model_facing_rendered_context != expected_text:
            raise ValueError("model-facing scratch render differs from canonical v6 aliases")
        if dict(model_facing_aliases or {}) != expected_aliases:
            raise ValueError("model-facing scratch aliases differ from canonical selection")
        receipt_text = model_facing_rendered_context
    if final_conjecture_pack.count(receipt_text) != 1:
        raise ValueError("final Conj pack must contain the exact advisory context once")

    render_receipt_ref = renderer.persist_receipt(rendered.receipt)
    rendered_context_ref = service.harness.blobs.put(receipt_text.encode("utf-8"))
    call_receipt = ConjectureContextCallReceiptV1(
        manifest_digest=plan.manifest_digest,
        problem_id=plan.problem_id,
        school_id=plan.school_id,
        formal_fence_seq=plan.formal_fence_seq,
        scratch_fence_seq=plan.scratch_fence_seq,
        selection_receipt_ref=plan.attention_pack.selection_receipt.id,
        advisory_context_ref=expected_context.id,
        render_receipt_ref=render_receipt_ref,
        rendered_context_ref=rendered_context_ref,
        expansion_decision_ref=plan.expansion_decision_ref,
        prior_selection_receipt_ref=plan.prior_selection_receipt_ref,
        root_block_refs=(
            list(plan.root_block_ids)
            if plan.root_block_ids is not None
            else None
        ),
        expansion_request_hash=plan.expansion_request_hash,
        expansion_index=plan.expansion_index,
        added_block_refs=(
            list(plan.added_block_refs)
            if plan.added_block_refs is not None
            else None
        ),
    )
    if validate_call_receipt is not None:
        validate_call_receipt(call_receipt)
    return call_receipt


def commit_conjecture_context(
    service: ScratchService,
    plan: PlannedConjectureContextV1,
    *,
    final_conjecture_pack: str,
    attention_policy: AttentionPolicyV1,
    model_facing_rendered_context: str | None = None,
    model_facing_aliases: Mapping[str, str] | None = None,
    prepared_call_receipt: ConjectureContextCallReceiptV1 | None = None,
    validate_call_receipt: Callable[[ConjectureContextCallReceiptV1], None]
    | None = None,
) -> ConjectureContextCallReceiptV1:
    """Commit one already validated plan immediately before provider dispatch."""

    call_receipt = prepare_conjecture_context_call(
        service,
        plan,
        final_conjecture_pack=final_conjecture_pack,
        attention_policy=attention_policy,
        model_facing_rendered_context=model_facing_rendered_context,
        model_facing_aliases=model_facing_aliases,
        validate_call_receipt=(
            validate_call_receipt if prepared_call_receipt is None else None
        ),
    )
    if (
        prepared_call_receipt is not None
        and ConjectureContextCallReceiptV1.model_validate(prepared_call_receipt)
        != call_receipt
    ):
        raise ValueError("prepared conjecture context receipt changed before commit")
    plan = PlannedConjectureContextV1.model_validate(plan)
    committed = service.commit_prepared_advisory_context(
        plan.attention_pack,
        plan.advisory_context,
        context_ref=call_receipt.render_receipt_ref,
        coverage_policy=attention_policy,
    )
    if committed.id != call_receipt.advisory_context_ref:
        raise ValueError("committed advisory context differs from call receipt")
    return call_receipt


def validate_conjecture_context_call(
    service: ScratchService,
    receipt: ConjectureContextCallReceiptV1,
    *,
    manifest_digest: str,
    problem_id: str,
    school_id: str | None,
    scratch_aliases: Mapping[str, str],
    provider_prompt: bytes,
) -> None:
    """Validate one durable v6 context receipt against canonical replay state."""

    receipt = ConjectureContextCallReceiptV1.model_validate(receipt)
    if receipt.manifest_digest != manifest_digest:
        raise ValueError("conjecture context belongs to another manifest")
    if receipt.problem_id != problem_id:
        raise ValueError("conjecture context belongs to another problem")
    if receipt.school_id != school_id:
        raise ValueError("conjecture context belongs to another school")

    selection = service.state.attention_receipts.get(receipt.selection_receipt_ref)
    if selection is None:
        raise ValueError("conjecture context selection is not canonical")
    if selection.state_seq != receipt.scratch_fence_seq:
        raise ValueError("conjecture context selection differs from its scratch fence")
    advisory = service.state.advisory_contexts.get(receipt.advisory_context_ref)
    if advisory is None or advisory.retrieval_receipt != selection.id:
        raise ValueError("conjecture advisory context is not canonical")

    try:
        render_receipt = ScratchRenderReceiptV1.model_validate_json(
            service.harness.blobs.get(receipt.render_receipt_ref)
        )
        rendered_text = service.harness.blobs.get(
            receipt.rendered_context_ref
        ).decode("utf-8")
        prompt = provider_prompt.decode("utf-8")
    except (KeyError, UnicodeDecodeError, ValueError) as error:
        raise ValueError("conjecture context blobs are unavailable or invalid") from error
    if (
        render_receipt.attention_receipt != selection.id
        or render_receipt.state_seq != selection.state_seq
    ):
        raise ValueError("conjecture render receipt differs from canonical selection")
    if tuple(render_receipt.block_handles.values()) != tuple(selection.final_order):
        raise ValueError("conjecture render blocks differ from canonical attention order")
    historical = ScratchService(
        service.harness.root,
        upto_seq=receipt.scratch_fence_seq,
    )
    try:
        historical_pack = AttentionPackV1(
            state_seq=selection.state_seq,
            request_hash=selection.request_hash,
            current_focus=(),
            blocks=[historical.state.blocks[item] for item in selection.final_order],
            channel_blocks=selection.selected_by_channel,
            cluster_guides=[
                GuideSelectionV1(
                    guide=guide,
                    state=historical.state.guide_state(guide),
                )
                for guide in advisory.guides or ()
            ],
            selection_receipt=selection,
        )
        expected_advisory = historical.prepare_advisory_context(
            historical_pack,
            warning=SCRATCH_CONTRACT_INSTRUCTIONS,
        )
        canonical_render = ScratchRenderer(historical).render_advisory_context(
            historical_pack,
            expected_advisory,
        )
    except (KeyError, ValueError) as error:
        raise ValueError("conjecture context cannot be reconstructed at its fence") from error
    if advisory != expected_advisory or render_receipt != canonical_render.receipt:
        raise ValueError("conjecture context differs from canonical historical render")
    expected_aliases, replacements = _v6_aliases_for_render_receipt(render_receipt)
    if dict(scratch_aliases) != expected_aliases:
        raise ValueError("transaction scratch exposure differs from canonical render")
    if rendered_text != _replace_local_handles(canonical_render.text, replacements):
        raise ValueError("model-facing context differs from canonical aliased render")
    if prompt.count(rendered_text) != 1:
        raise ValueError("provider prompt must contain the exact advisory context once")


def plan_conjecture_context_expansion(
    service: ScratchService,
    *,
    problem: Problem,
    school_id: str | None,
    manifest_digest: str,
    scratch_policy: ScratchPolicy,
    context_policy: ConjectureContextPolicyV1,
    request: ContextRequestV1,
    prior_plan: PlannedConjectureContextV1 | None,
    expansion_decision_ref: str,
    expansion_index: int,
    formal_fence_seq: int,
    scratch_fence_seq: int,
) -> PlannedConjectureContextV1 | None:
    """Prepare one cumulative follow-up view within the frozen total cap."""

    if service.read_only:
        raise ScratchReadOnly(
            "historical scratch views cannot plan future Conj expansion"
        )
    problem = Problem.model_validate(problem)
    scratch_policy = ScratchPolicy.model_validate(scratch_policy)
    context_policy = ConjectureContextPolicyV1.model_validate(context_policy)
    request = ContextRequestV1.model_validate(request)
    if isinstance(expansion_index, bool) or not 1 <= expansion_index <= 8:
        raise ValueError("expansion_index must be from 1 through 8")
    prior = (
        PlannedConjectureContextV1.model_validate(prior_plan)
        if prior_plan is not None
        else None
    )
    current = service.harness._next_seq - 1
    if formal_fence_seq != current or scratch_fence_seq != current:
        raise ConjectureContextStale()
    if service.harness.state.problems.get(problem.id) != problem:
        raise ValueError("problem is not canonical at the supplied formal fence")
    if context_policy.mode != "harness_plus_model_request":
        return None
    if prior is not None and (
        prior.problem_id != problem.id
        or prior.school_id != school_id
        or prior.manifest_digest != manifest_digest
    ):
        raise ValueError("prior context belongs to another conjecture work item")

    base = scratch_policy.attention_policy()
    prior_ids = (
        list(prior.attention_pack.selection_receipt.final_order) if prior else []
    )
    root_ids = (
        list(
            prior.root_block_ids
            if prior.root_block_ids is not None
            else prior_ids
        )
        if prior is not None
        else []
    )
    total_cap = min(
        base.max_blocks_per_pack,
        len(root_ids) + context_policy.max_extra_blocks,
    )
    if total_cap <= len(prior_ids) or not service.state.blocks:
        return None

    permitted_values = tuple(context_policy.permitted_retrieval_channels)
    desired_values = tuple(
        channel.value for channel in request.desired_retrieval_channels
    )
    if set(desired_values) - set(permitted_values):
        raise ValueError("context request uses a retrieval channel outside policy")
    selected = set(desired_values or permitted_values)
    if RetrievalChannel.FOCUS.value in permitted_values:
        selected.add(RetrievalChannel.FOCUS.value)
    selected_values = tuple(
        value for value in permitted_values if value in selected
    )
    allowed = {RetrievalChannel(value) for value in selected_values}

    focus: list[str] = list(prior_ids)
    for reference in request.requested_refs:
        if reference in service.state.blocks:
            focus.append(reference)
            continue
        if reference in service.state.clusters:
            focus.extend(
                block.id for block in service.cluster_members(reference)
            )
            continue
        if reference in service.state.links:
            link = service.state.links[reference]
            focus.extend((link.body.from_, link.body.to))
            continue
        guide = next(
            (
                item
                for guides in service.state.guides_by_cluster.values()
                for item in guides
                if item.id == reference
            ),
            None,
        )
        if guide is not None:
            if guide.entry_points:
                focus.extend(guide.entry_points)
            else:
                focus.extend(
                    block.id for block in service.cluster_members(guide.cluster_id)
                )
            continue
        focus.extend(
            block.id
            for block in service.state.blocks.values()
            if reference in block.provenance.formal_artifact_refs
        )
    if request.query and RetrievalChannel.KEYWORD in allowed:
        focus.extend(
            block.id
            for block in service.search_phrase(
                request.query,
                max(1, context_policy.max_extra_blocks * 4),
            )
        )
    focus = list(dict.fromkeys(focus))[:total_cap]
    if focus and RetrievalChannel.FOCUS not in {
        RetrievalChannel(value) for value in permitted_values
    }:
        # A visible-alias request cannot silently acquire an ungranted channel.
        if any(reference in service.state.blocks for reference in request.requested_refs):
            return None
        focus = []

    attention_policy = _expanded_attention_policy(
        scratch_policy,
        context_policy,
        maximum_blocks=total_cap,
    )
    permitted = tuple(RetrievalChannel(value) for value in selected_values)
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
    attention_request = AttentionRequestV1(
        focus_blocks=focus or None,
        focus_clusters=clusters or None,
        permitted_channels=list(permitted),
        maximum_blocks=total_cap,
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
        deterministic_seed=_expansion_seed(
            manifest_digest,
            problem.id,
            school_id,
            expansion_decision_ref,
            request.request_hash,
        ),
    )
    pack = AttentionPlanner(service, attention_policy).plan(attention_request)
    final_ids = list(pack.selection_receipt.final_order)
    if not set(prior_ids).issubset(final_ids) or not (set(final_ids) - set(prior_ids)):
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
        expansion_decision_ref=expansion_decision_ref,
        prior_selection_receipt_ref=(
            prior.attention_pack.selection_receipt.id if prior else None
        ),
        root_block_ids=tuple(root_ids),
        expansion_request_hash=request.request_hash,
        expansion_index=expansion_index,
        added_block_refs=tuple(
            block_id for block_id in final_ids if block_id not in set(prior_ids)
        ),
    )


ConjectureContextPlanV1 = PlannedConjectureContextV1


__all__ = [
    "ConjectureContextCallReceiptV1",
    "ConjectureContextPlanV1",
    "ConjectureContextStale",
    "PlannedConjectureContextV1",
    "commit_conjecture_context",
    "plan_conjecture_context",
    "plan_conjecture_context_expansion",
]
