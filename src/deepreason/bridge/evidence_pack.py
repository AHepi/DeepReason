"""Deterministic, fixed-sequence evidence packs for final-output views.

This module extracts the formal record into two representations from one
read-only pass:

* a structured, frozen pack used by the grounded bridge; and
* the historical thesis text/citation catalog, byte-compatible with the
  original :mod:`deepreason.views.thesis` implementation.

Every canonical reference in the structured catalog comes from the supplied
harness.  Model-facing Stage A rendering is delegated to the existing claim
ledger catalog, which exposes only call-local handles and bounded excerpts.
No object, blob, event, status, or graph relation is written here.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from typing import Literal

from pydantic import Field, StrictFloat, StrictInt, field_validator, model_validator

from deepreason.bridge.ledger import (
    MAX_CATALOG_EXCERPT,
    MAX_CATALOG_ITEMS,
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV1,
)
from deepreason.bridge.models import CanonicalBridgeRecord, BridgeRecord
from deepreason.frozen import FrozenList
from deepreason.informal.skeleton import parse_skeleton
from deepreason.ontology.artifact import RefRole
from deepreason.ontology.state import Status
from deepreason.programs import content_text
from deepreason.scratch.models import AdvisoryContextV1


DEFAULT_EVIDENCE_PACK_BUDGET = 24_000
MAX_EVIDENCE_PACK_BUDGET = 262_144
MAX_EVIDENCE_PACK_RENDERED = 327_680
MAX_EVIDENCE_PACK_ITEMS = 10_000
MAX_LINEAGE_REFS = 2_048
MAX_OVERTURN_CONDITIONS = 128
MAX_STRUCTURED_TEXT = 16_384

_ITEM_ACCEPTED_CAP = 900
_ITEM_CLAIM_CAP = 240
_ITEM_CASE_CAP = 420
_ITEM_QUOTE_CAP = 200

_FOOTER = (
    "\nDIRECTIVE: from this record ONLY, produce the committed thesis "
    "(rules in your role brief). Cite bracketed ids exactly."
)


def _freeze(value):
    return FrozenList(value)


class EvidenceLineageV1(BridgeRecord):
    """Harness-owned grounding and provenance reachable from one item."""

    warrant_refs: list[str] = Field(default_factory=FrozenList, max_length=MAX_LINEAGE_REFS)
    trace_refs: list[str] = Field(default_factory=FrozenList, max_length=MAX_LINEAGE_REFS)
    evidence_refs: list[str] = Field(default_factory=FrozenList, max_length=MAX_LINEAGE_REFS)
    source_refs: list[str] = Field(default_factory=FrozenList, max_length=MAX_LINEAGE_REFS)
    dependence_refs: list[str] = Field(default_factory=FrozenList, max_length=MAX_LINEAGE_REFS)
    mention_refs: list[str] = Field(default_factory=FrozenList, max_length=MAX_LINEAGE_REFS)

    @field_validator(
        "warrant_refs",
        "trace_refs",
        "evidence_refs",
        "source_refs",
        "dependence_refs",
        "mention_refs",
        mode="after",
    )
    @classmethod
    def _freeze_unique_refs(cls, value, info):
        if len(value) != len(set(value)):
            raise ValueError(f"{info.field_name} must not contain duplicates")
        if any(not ref.strip() for ref in value):
            raise ValueError(f"{info.field_name} must not contain blank references")
        return _freeze(value)


class SurvivorEvidenceV1(BridgeRecord):
    artifact_ref: str = Field(min_length=1, max_length=512)
    citation_id: str = Field(min_length=1, max_length=64)
    addressed_problem_refs: list[str] = Field(
        default_factory=FrozenList, max_length=MAX_LINEAGE_REFS
    )
    claim: str = Field(min_length=1, max_length=MAX_STRUCTURED_TEXT)
    mechanism: str | None = Field(default=None, max_length=MAX_STRUCTURED_TEXT)
    overturn_conditions: list[str] = Field(
        default_factory=FrozenList, max_length=MAX_OVERTURN_CONDITIONS
    )
    school: str | None = Field(default=None, max_length=512)
    heuristic_value: StrictFloat | None = None
    lineage: EvidenceLineageV1
    rendered_text: str = Field(min_length=1, max_length=_ITEM_ACCEPTED_CAP)

    @field_validator("addressed_problem_refs", "overturn_conditions", mode="after")
    @classmethod
    def _freeze_sequences(cls, value, info):
        if info.field_name == "addressed_problem_refs" and len(value) != len(set(value)):
            raise ValueError("addressed_problem_refs must not contain duplicates")
        return _freeze(value)


class ArguedRefutationV1(BridgeRecord):
    artifact_ref: str = Field(min_length=1, max_length=512)
    citation_id: str = Field(min_length=1, max_length=64)
    claim: str = Field(min_length=1, max_length=_ITEM_CLAIM_CAP)
    attacker_ref: str | None = Field(default=None, min_length=1, max_length=512)
    attacker_citation_id: str | None = Field(default=None, min_length=1, max_length=64)
    argued_case: str | None = Field(default=None, max_length=_ITEM_CASE_CAP)
    decisive_point: str | None = Field(default=None, max_length=_ITEM_QUOTE_CAP)
    decisive_warrant_ref: str | None = Field(default=None, min_length=1, max_length=512)
    decisive_trace_ref: str | None = Field(default=None, min_length=1, max_length=512)
    lineage: EvidenceLineageV1
    rendered_text: str = Field(min_length=1, max_length=2_048)


class PairwiseRulingV1(BridgeRecord):
    ruling_artifact_ref: str = Field(min_length=1, max_length=512)
    winner_ref: str = Field(min_length=1, max_length=512)
    loser_ref: str = Field(min_length=1, max_length=512)
    decisive_point: str = Field(max_length=_ITEM_QUOTE_CAP)
    rendered_text: str = Field(min_length=1, max_length=768)


class OpenRivalryV1(BridgeRecord):
    problem_ref: str = Field(min_length=1, max_length=512)
    rival_refs: list[str] = Field(min_length=2, max_length=MAX_LINEAGE_REFS)
    rendered_text: str = Field(min_length=1, max_length=MAX_STRUCTURED_TEXT)

    @field_validator("rival_refs", mode="after")
    @classmethod
    def _freeze_unique_rivals(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("rival_refs must not contain duplicates")
        return _freeze(value)


class EvidencePackOmissionsV1(BridgeRecord):
    survivors: StrictInt = Field(ge=0)
    pairwise_rulings: StrictInt = Field(ge=0)
    open_rivals: StrictInt = Field(ge=0)
    argued_refutations: StrictInt = Field(ge=0)
    catalog_items: StrictInt = Field(ge=0)


class EvidencePackV1(CanonicalBridgeRecord):
    """One immutable evidence view pinned to a materialized formal sequence."""

    schema_: Literal["bridge.evidence-pack.v1"] = Field(
        "bridge.evidence-pack.v1", alias="schema"
    )
    ID_DOMAIN = "bridge.evidence-pack.v1"

    problem_ref: str = Field(min_length=1, max_length=512)
    formal_seq: StrictInt = Field(ge=0)
    # Present only for an explicit dual-root derived view.  The digest binds
    # this canonical pack to a path-independent source event prefix while the
    # formal sequence records the exact source fence.  Same-root packs omit it
    # so their historical canonical identities remain unchanged.
    source_run_digest: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    problem_text: str = Field(min_length=1, max_length=262_144)
    problem_family_refs: list[str] = Field(
        min_length=1, max_length=MAX_EVIDENCE_PACK_ITEMS
    )
    survivors: list[SurvivorEvidenceV1] = Field(max_length=MAX_EVIDENCE_PACK_ITEMS)
    argued_refutations: list[ArguedRefutationV1] = Field(
        max_length=MAX_EVIDENCE_PACK_ITEMS
    )
    pairwise_rulings: list[PairwiseRulingV1] = Field(
        max_length=MAX_EVIDENCE_PACK_ITEMS
    )
    open_rivals: list[OpenRivalryV1] = Field(max_length=MAX_EVIDENCE_PACK_ITEMS)
    catalog_items: list[ClaimLedgerCatalogItemV1] = Field(max_length=MAX_CATALOG_ITEMS)
    legacy_text: str = Field(min_length=1, max_length=MAX_EVIDENCE_PACK_RENDERED)
    legacy_citable_ids: list[str] = Field(max_length=MAX_EVIDENCE_PACK_ITEMS)
    omissions: EvidencePackOmissionsV1

    @field_validator(
        "problem_family_refs",
        "survivors",
        "argued_refutations",
        "pairwise_rulings",
        "open_rivals",
        "catalog_items",
        "legacy_citable_ids",
        mode="after",
    )
    @classmethod
    def _freeze_sequences(cls, value, info):
        if info.field_name in {"problem_family_refs", "legacy_citable_ids"}:
            keys = list(value)
        elif info.field_name == "catalog_items":
            keys = [item.handle for item in value]
        elif info.field_name == "survivors":
            keys = [item.artifact_ref for item in value]
        elif info.field_name == "argued_refutations":
            keys = [item.artifact_ref for item in value]
        elif info.field_name == "pairwise_rulings":
            keys = [item.ruling_artifact_ref for item in value]
        else:
            keys = [item.problem_ref for item in value]
        if len(keys) != len(set(keys)):
            raise ValueError(f"{info.field_name} must not contain duplicate identities")
        return _freeze(value)

    @model_validator(mode="after")
    def _problem_is_in_family(self):
        if self.problem_ref not in self.problem_family_refs:
            raise ValueError("problem_ref must belong to problem_family_refs")
        return self

    def claim_ledger_catalog(
        self,
        output_target: str,
        *,
        advisory_context: AdvisoryContextV1 | None = None,
        advisory_context_ref: str | None = None,
        retrieval_receipt_ref: str | None = None,
    ) -> ClaimLedgerInputCatalogV1:
        """Compile the existing closed Stage A catalog from this fixed view."""

        items, advisory_context_ref, retrieval_receipt_ref = _advisory_catalog_inputs(
            self.catalog_items,
            advisory_context=advisory_context,
            advisory_context_ref=advisory_context_ref,
            retrieval_receipt_ref=retrieval_receipt_ref,
        )
        return ClaimLedgerInputCatalogV1.create(
            problem_ref=self.problem_ref,
            formal_seq=self.formal_seq,
            problem_text=self.problem_text,
            output_target=output_target,
            items=items,
            advisory_context_ref=advisory_context_ref,
            retrieval_receipt_ref=retrieval_receipt_ref,
        )


def problem_family(state, problem_id: str) -> list[str]:
    """Return one problem and all provenance-spawned successors in order."""

    if problem_id not in state.problems:
        return []
    addressed_by: dict[str, set[str]] = {}
    for aid, pid in state.addr:
        addressed_by.setdefault(aid, set()).add(pid)
    family = {problem_id}
    changed = True
    while changed:
        changed = False
        for pid, problem in state.problems.items():
            if pid in family:
                continue
            for fid in problem.provenance.from_:
                parents = {fid} if fid in family else addressed_by.get(fid, set())
                if fid in family or parents & family:
                    family.add(pid)
                    changed = True
                    break
    return [pid for pid in state.problems if pid in family]


def _claim_line(text: str) -> str:
    skeleton = parse_skeleton(text)
    return skeleton.claim if skeleton is not None else text


def _append_unique(values: list[str], value: str | None) -> None:
    if value and value not in values:
        values.append(value)


def _is_source_artifact(harness, artifact_id: str) -> bool:
    artifact = harness.state.artifacts.get(artifact_id)
    if artifact is None or not _artifact_content_available(harness, artifact_id):
        return False
    return content_text(artifact, harness.blobs).startswith("source-reliability:")


def _artifact_content_available(harness, artifact_id: str) -> bool:
    artifact = harness.state.artifacts.get(artifact_id)
    if artifact is None:
        return False
    if artifact.content_ref.startswith("inline:"):
        return True
    checker = getattr(harness.blobs, "is_grounding_available", None)
    return True if checker is None else bool(checker(artifact.content_ref))


def _is_evidence_artifact(harness, artifact_id: str) -> bool:
    artifact = harness.state.artifacts.get(artifact_id)
    return bool(
        artifact is not None
        and _artifact_content_available(harness, artifact_id)
        and artifact.provenance.role.value in {"import", "user"}
        and not _is_source_artifact(harness, artifact_id)
    )


def _evidence_sources(harness, evidence_ref: str) -> list[str]:
    """Registered dependence closure below one evidence artifact."""

    artifacts = harness.state.artifacts
    seen: set[str] = set()
    sources: list[str] = []
    stack = [evidence_ref]
    while stack:
        current = stack.pop()
        if (
            current in seen
            or current not in artifacts
            or not _artifact_content_available(harness, current)
        ):
            continue
        seen.add(current)
        dependencies = [
            ref.target
            for ref in artifacts[current].interface.refs
            if ref.role == RefRole.DEPENDENCE
            and ref.target in artifacts
            and _artifact_content_available(harness, ref.target)
        ]
        for dependency in dependencies:
            _append_unique(sources, dependency)
        stack.extend(reversed(dependencies))
    return sources


def _lineage(harness, artifact_ref: str) -> EvidenceLineageV1:
    state = harness.state
    warrants: list[str] = []
    traces: list[str] = []
    evidence: list[str] = []
    sources: list[str] = []
    dependencies: list[str] = []
    mentions: list[str] = []

    inspected = [artifact_ref]
    for warrant_ref in harness.carried_warrant_ids(artifact_ref):
        warrant = harness.warrants.get(warrant_ref)
        if warrant is None:
            continue
        _append_unique(warrants, warrant_ref)
        _append_unique(traces, warrant.trace_ref)
        if warrant.validity_node in state.artifacts:
            _append_unique(inspected, warrant.validity_node)

    for current in inspected:
        artifact = state.artifacts.get(current)
        if artifact is None:
            continue
        if _is_evidence_artifact(harness, current):
            _append_unique(evidence, current)
        if _is_source_artifact(harness, current):
            _append_unique(sources, current)
        for ref in artifact.interface.refs:
            if ref.role == RefRole.EVIDENCE:
                if _artifact_content_available(harness, ref.target):
                    _append_unique(evidence, ref.target)
            elif ref.role == RefRole.DEPENDENCE:
                if not _artifact_content_available(harness, ref.target):
                    continue
                _append_unique(dependencies, ref.target)
                if _is_source_artifact(harness, ref.target):
                    _append_unique(sources, ref.target)
                elif _is_evidence_artifact(harness, ref.target):
                    _append_unique(evidence, ref.target)
            elif ref.role == RefRole.MENTION:
                _append_unique(mentions, ref.target)

    for evidence_ref in evidence:
        for source_ref in _evidence_sources(harness, evidence_ref):
            _append_unique(sources, source_ref)

    return EvidenceLineageV1(
        warrant_refs=warrants[:MAX_LINEAGE_REFS],
        trace_refs=traces[:MAX_LINEAGE_REFS],
        evidence_refs=evidence[:MAX_LINEAGE_REFS],
        source_refs=sources[:MAX_LINEAGE_REFS],
        dependence_refs=dependencies[:MAX_LINEAGE_REFS],
        mention_refs=mentions[:MAX_LINEAGE_REFS],
    )


def _decisive_from_warrants(harness, attacker) -> tuple[str, str | None, str | None]:
    """Legacy decisive text plus its exact warrant/trace lineage."""

    for warrant_ref in harness.carried_warrant_ids(attacker.id):
        warrant = harness.warrants.get(warrant_ref)
        if warrant is None or not warrant.trace_ref:
            continue
        try:
            trace = json.loads(harness.blobs.get(warrant.trace_ref))
        except (KeyError, ValueError):
            continue
        if not isinstance(trace, dict):
            continue
        ruling = trace.get("ruling") or {}
        if isinstance(ruling, Mapping) and ruling.get("decisive_point"):
            return str(ruling["decisive_point"]), warrant_ref, warrant.trace_ref
        if trace.get("error"):
            return str(trace["error"]), warrant_ref, warrant.trace_ref
    return "", None, None


def _bounded_structured_text(value: str, maximum: int = MAX_STRUCTURED_TEXT) -> str:
    value = value[:maximum]
    return value if value.strip() else "(empty recorded content)"


def _advisory_catalog_inputs(
    base_items: Sequence[ClaimLedgerCatalogItemV1],
    *,
    advisory_context: AdvisoryContextV1 | None,
    advisory_context_ref: str | None,
    retrieval_receipt_ref: str | None,
) -> tuple[list[ClaimLedgerCatalogItemV1], str | None, str | None]:
    """Append only blocks from one verified advisory context as scratch items."""

    items = list(base_items)
    if advisory_context is None:
        return items, advisory_context_ref, retrieval_receipt_ref

    context = AdvisoryContextV1.model_validate(advisory_context)
    if advisory_context_ref is not None and advisory_context_ref != context.id:
        raise ValueError("advisory_context_ref does not match advisory_context.id")
    if (
        retrieval_receipt_ref is not None
        and retrieval_receipt_ref != context.retrieval_receipt
    ):
        raise ValueError(
            "retrieval_receipt_ref does not match advisory context receipt"
        )
    available = max(0, MAX_CATALOG_ITEMS - len(items))
    for index, block in enumerate(context.blocks[:available], 1):
        parts = [block.body.content]
        if block.body.why_keep_this is not None:
            parts.append(f"why keep: {block.body.why_keep_this}")
        if block.body.unfinished is not None:
            parts.append(f"unfinished: {block.body.unfinished}")
        if block.body.possible_next_move is not None:
            parts.append(f"possible next move: {block.body.possible_next_move}")
        items.append(
            ClaimLedgerCatalogItemV1(
                handle=f"B{index}",
                kind="scratch",
                ref=block.id,
                excerpt=_bounded_structured_text(
                    "\n".join(parts), MAX_CATALOG_EXCERPT
                ),
            )
        )
    return items, context.id, context.retrieval_receipt


def _catalog_excerpt(harness, ref: str, fallback: str) -> str:
    artifact = harness.state.artifacts.get(ref)
    if artifact is None:
        return _bounded_structured_text(fallback, MAX_CATALOG_EXCERPT)
    if not _artifact_content_available(harness, ref):
        raise RuntimeError("unavailable artifact reached grounding catalog")
    text = content_text(artifact, harness.blobs)[:MAX_CATALOG_EXCERPT]
    return text if text.strip() else _bounded_structured_text(fallback, MAX_CATALOG_EXCERPT)


def _catalog_items(
    harness,
    *,
    formal_seq: int,
    family: set[str],
    survivors: Sequence[SurvivorEvidenceV1],
    refutations: Sequence[ArguedRefutationV1],
    rulings: Sequence[PairwiseRulingV1],
    rivalries: Sequence[OpenRivalryV1],
) -> tuple[list[ClaimLedgerCatalogItemV1], int]:
    """Build a closed, priority-ordered catalog of harness-owned references."""

    candidates: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, ref: str, excerpt: str) -> None:
        key = (kind, ref)
        if key in seen:
            return
        seen.add(key)
        candidates.append((kind, ref, _bounded_structured_text(excerpt, MAX_CATALOG_EXCERPT)))

    for survivor in survivors:
        add("formal_artifact", survivor.artifact_ref, survivor.rendered_text)
        add(
            "formal_observation",
            survivor.artifact_ref,
            f"At formal sequence {formal_seq}, this position is accepted after criticism: "
            f"{survivor.claim}",
        )
    for refutation in refutations:
        add("formal_observation", refutation.artifact_ref, refutation.rendered_text)
        if refutation.attacker_ref:
            add(
                "formal_observation",
                refutation.attacker_ref,
                refutation.argued_case or "Recorded formal attack.",
            )
    for ruling in rulings:
        add("formal_observation", ruling.ruling_artifact_ref, ruling.rendered_text)
    for rivalry in rivalries:
        add("formal_observation", rivalry.problem_ref, rivalry.rendered_text)

    # Accepted import/user artifacts addressing the family are the record's
    # explicit evidence candidates. Their dependence closure supplies source
    # lineage; neither role nor a reference silently upgrades their status.
    for artifact_ref, problem_ref in harness.state.addr:
        if problem_ref not in family:
            continue
        if not _is_evidence_artifact(harness, artifact_ref):
            continue
        if harness.state.status.get(artifact_ref) != Status.ACCEPTED:
            continue
        add(
            "evidence",
            artifact_ref,
            _catalog_excerpt(harness, artifact_ref, "Recorded accepted evidence."),
        )
        for source_ref in _evidence_sources(harness, artifact_ref):
            add(
                "source",
                source_ref,
                _catalog_excerpt(harness, source_ref, "Recorded evidence source."),
            )

    for item in [*survivors, *refutations]:
        for evidence_ref in item.lineage.evidence_refs:
            add(
                "evidence",
                evidence_ref,
                _catalog_excerpt(harness, evidence_ref, "Recorded evidence lineage."),
            )
        for source_ref in item.lineage.source_refs:
            add(
                "source",
                source_ref,
                _catalog_excerpt(harness, source_ref, "Recorded source lineage."),
            )
        for trace_ref in item.lineage.trace_refs:
            try:
                trace_excerpt = harness.blobs.get(trace_ref).decode(
                    "utf-8", errors="replace"
                )
            except KeyError:
                continue
            add("trace", trace_ref, trace_excerpt)

    prefix = {
        "formal_artifact": "A",
        "formal_observation": "O",
        "evidence": "E",
        "source": "S",
        "trace": "T",
    }
    counts = {kind: 0 for kind in prefix}
    selected = candidates[:MAX_CATALOG_ITEMS]
    items: list[ClaimLedgerCatalogItemV1] = []
    for kind, ref, excerpt in selected:
        counts[kind] += 1
        items.append(
            ClaimLedgerCatalogItemV1(
                handle=f"{prefix[kind]}{counts[kind]}",
                kind=kind,
                ref=ref,
                excerpt=excerpt,
            )
        )
    return items, len(candidates) - len(selected)


def _validate_formal_seq(harness, formal_seq: int | None) -> int:
    current = harness._next_seq - 1
    if current < 0:
        raise ValueError("cannot build an evidence pack before the first formal event")
    if formal_seq is None:
        return current
    if isinstance(formal_seq, bool) or not isinstance(formal_seq, int) or formal_seq < 0:
        raise ValueError("formal_seq must be a non-negative integer")
    if formal_seq != current:
        raise ValueError(
            f"formal_seq {formal_seq} does not match supplied harness fence {current}; "
            "open the run with Harness.at(root, formal_seq) first"
        )
    return formal_seq


def assemble_evidence_pack(
    harness,
    problem_id: str,
    *,
    budget_chars: int = DEFAULT_EVIDENCE_PACK_BUDGET,
    formal_seq: int | None = None,
    source_run_digest: str | None = None,
) -> EvidencePackV1:
    """Extract a bounded structured/legacy pack at one exact formal fence."""

    if isinstance(budget_chars, bool) or not isinstance(budget_chars, int):
        raise TypeError("budget_chars must be an integer")
    if not 0 <= budget_chars <= MAX_EVIDENCE_PACK_BUDGET:
        raise ValueError(
            f"budget_chars must be between 0 and {MAX_EVIDENCE_PACK_BUDGET}"
        )
    seq = _validate_formal_seq(harness, formal_seq)
    state = harness.state
    if problem_id not in state.problems:
        raise KeyError(f"problem not registered: {problem_id}")
    problem = state.problems[problem_id]
    if not problem.description.strip():
        raise ValueError("problem description must contain non-whitespace text")

    family_order = problem_family(state, problem_id)
    if len(family_order) > MAX_EVIDENCE_PACK_ITEMS:
        raise ValueError("problem family exceeds the bounded evidence-pack limit")
    family = set(family_order)
    rank = {aid: index for index, aid in enumerate(state.artifacts)}
    addressed = [aid for aid, pid in state.addr if pid in family]
    attackers_of: dict[str, list[str]] = {}
    for attacker, target in state.att:
        attackers_of.setdefault(target, []).append(attacker)

    accepted: list[str] = []
    refuted: list[str] = []
    for artifact_ref in dict.fromkeys(addressed):
        artifact = state.artifacts[artifact_ref]
        if not _artifact_content_available(harness, artifact_ref):
            continue
        if artifact.provenance.role.value not in ("conjecturer", "synthesizer"):
            continue
        status = state.status.get(artifact_ref)
        if status == Status.ACCEPTED:
            accepted.append(artifact_ref)
        elif status == Status.REFUTED:
            refuted.append(artifact_ref)
    accepted.sort(key=lambda ref: (-(state.hv.get(ref, -1.0)), rank[ref]))
    refuted.sort(key=lambda ref: -rank[ref])

    addressed_by_artifact: dict[str, list[str]] = {}
    for artifact_ref, pid in state.addr:
        if pid in family:
            addressed_by_artifact.setdefault(artifact_ref, []).append(pid)

    survivor_candidates: list[SurvivorEvidenceV1] = []
    for artifact_ref in accepted[:MAX_EVIDENCE_PACK_ITEMS]:
        artifact = state.artifacts[artifact_ref]
        text = content_text(artifact, harness.blobs)
        skeleton = parse_skeleton(text)
        hv = state.hv.get(artifact_ref)
        head = f"[{artifact_ref[:12]}] (school: {artifact.provenance.school or '-'}" + (
            f", hv {hv:.2f})" if hv is not None else ")"
        )
        if skeleton is not None:
            body = f"CLAIM: {skeleton.claim}\nMECHANISM: {skeleton.mechanism}"
            for case in skeleton.forbidden[:2]:
                body += f"\nFORBIDS: {case.case}"
            claim = _bounded_structured_text(skeleton.claim)
            mechanism = _bounded_structured_text(skeleton.mechanism)
            overturn = [
                _bounded_structured_text(case.case)
                for case in skeleton.forbidden[:MAX_OVERTURN_CONDITIONS]
            ]
        else:
            body = text
            claim = _bounded_structured_text(text)
            mechanism = None
            overturn = []
        survivor_candidates.append(
            SurvivorEvidenceV1(
                artifact_ref=artifact_ref,
                citation_id=artifact_ref[:12],
                addressed_problem_refs=addressed_by_artifact.get(artifact_ref, []),
                claim=claim,
                mechanism=mechanism,
                overturn_conditions=overturn,
                school=artifact.provenance.school,
                heuristic_value=(
                    float(hv) if hv is not None and math.isfinite(hv) else None
                ),
                lineage=_lineage(harness, artifact_ref),
                rendered_text=f"{head}\n{body}"[:_ITEM_ACCEPTED_CAP],
            )
        )

    pairwise_candidates: list[PairwiseRulingV1] = []
    for artifact_ref, artifact in state.artifacts.items():
        if not _artifact_content_available(harness, artifact_ref):
            continue
        text = content_text(artifact, harness.blobs)
        if not text.startswith('{"pairwise"'):
            continue
        try:
            body = json.loads(text)["pairwise"]
            winner = str(body["winner"])
            loser = str(body["loser"])
        except (ValueError, KeyError, TypeError):
            continue
        if body.get("problem") not in family:
            continue
        decisive = str(body.get("decisive_point", ""))[:_ITEM_QUOTE_CAP]
        rendered = f"[{winner[:12]}] beat [{loser[:12]}]: {decisive}"
        pairwise_candidates.append(
            PairwiseRulingV1(
                ruling_artifact_ref=artifact_ref,
                winner_ref=winner,
                loser_ref=loser,
                decisive_point=decisive,
                rendered_text=rendered,
            )
        )

    rivalry_candidates: list[OpenRivalryV1] = []
    accepted_set = set(accepted)
    for pid in family_order:
        rivals = [ref for ref, addressed_pid in state.addr if addressed_pid == pid and ref in accepted_set]
        if len(rivals) >= 2:
            rivalry_candidates.append(
                OpenRivalryV1(
                    problem_ref=pid,
                    rival_refs=rivals,
                    rendered_text=(
                        f"{pid}: " + ", ".join(f"[{ref[:12]}]" for ref in rivals)
                    )[:MAX_STRUCTURED_TEXT],
                )
            )

    refutation_candidates: list[ArguedRefutationV1] = []
    for artifact_ref in refuted[:MAX_EVIDENCE_PACK_ITEMS]:
        artifact = state.artifacts[artifact_ref]
        claim = _claim_line(content_text(artifact, harness.blobs))[:_ITEM_CLAIM_CAP]
        entry = f"[{artifact_ref[:12]}] REFUTED: {claim}"
        attacker_ref = None
        attacker_citation_id = None
        argued_case = None
        decisive = ""
        decisive_warrant = None
        decisive_trace = None
        attacker_lineage = EvidenceLineageV1()
        for candidate in sorted(attackers_of.get(artifact_ref, []), key=lambda ref: rank[ref]):
            if not _artifact_content_available(harness, candidate):
                continue
            attacker = state.artifacts[candidate]
            attacker_ref = candidate
            attacker_citation_id = candidate[:12]
            argued_case = content_text(attacker, harness.blobs)[:_ITEM_CASE_CAP]
            entry += f"\n  FELLED BY [{candidate[:12]}]: {argued_case}"
            decisive, decisive_warrant, decisive_trace = _decisive_from_warrants(
                harness, attacker
            )
            if decisive:
                entry += f"\n  DECISIVE: {decisive[:_ITEM_QUOTE_CAP]}"
            attacker_lineage = _lineage(harness, candidate)
            break
        refutation_candidates.append(
            ArguedRefutationV1(
                artifact_ref=artifact_ref,
                citation_id=artifact_ref[:12],
                claim=claim or "(empty recorded claim)",
                attacker_ref=attacker_ref,
                attacker_citation_id=attacker_citation_id,
                argued_case=argued_case,
                decisive_point=decisive[:_ITEM_QUOTE_CAP] or None,
                decisive_warrant_ref=decisive_warrant,
                decisive_trace_ref=decisive_trace,
                lineage=attacker_lineage,
                rendered_text=entry,
            )
        )

    lines = [
        f"PROBLEM {problem_id}: {problem.description}",
        f"(family: {len(family)} problems including spawned successors)",
        "",
    ]
    used = sum(len(line) + 1 for line in lines) + len(_FOOTER)
    citable_ids: list[str] = []

    def emit(section: str, candidates, ids_for):
        nonlocal used
        header = f"== {section} =="
        lines.append(header)
        used += len(header) + 1
        included = []
        for index, item in enumerate(candidates):
            text = item.rendered_text
            if used + len(text) + 1 > budget_chars:
                marker = f"(+{len(candidates) - index} more omitted for budget)"
                lines.append(marker)
                used += len(marker) + 1
                break
            lines.append(text)
            used += len(text) + 1
            included.append(item)
            for citation in ids_for(item):
                _append_unique(citable_ids, citation)
        lines.append("")
        used += 1
        return included

    survivors = emit(
        "SURVIVING POSITIONS (accepted after criticism)",
        survivor_candidates,
        lambda item: [item.citation_id],
    )
    rulings = emit(
        "PAIRWISE RULINGS",
        pairwise_candidates,
        lambda item: [item.winner_ref[:12], item.loser_ref[:12]],
    )
    rivalries = emit(
        "UNRESOLVED RIVALRIES (multiple survivors, undecided)",
        rivalry_candidates,
        lambda _item: [],
    )
    refutations = emit(
        "REFUTED POSITIONS (with the arguments that felled them)",
        refutation_candidates,
        lambda item: [
            item.citation_id,
            *([item.attacker_citation_id] if item.attacker_citation_id else []),
        ],
    )
    lines.append(_FOOTER)
    legacy_text = "\n".join(lines)

    if harness._next_seq - 1 != seq:
        raise RuntimeError("formal harness advanced while evidence pack was assembled")

    catalog, catalog_omitted = _catalog_items(
        harness,
        formal_seq=seq,
        family=family,
        survivors=survivors,
        refutations=refutations,
        rulings=rulings,
        rivalries=rivalries,
    )
    if harness._next_seq - 1 != seq:
        raise RuntimeError("formal harness advanced while evidence catalog was assembled")

    return EvidencePackV1.create(
        problem_ref=problem_id,
        formal_seq=seq,
        source_run_digest=source_run_digest,
        problem_text=problem.description,
        problem_family_refs=family_order,
        survivors=survivors,
        argued_refutations=refutations,
        pairwise_rulings=rulings,
        open_rivals=rivalries,
        catalog_items=catalog,
        legacy_text=legacy_text,
        legacy_citable_ids=citable_ids,
        omissions=EvidencePackOmissionsV1(
            survivors=len(survivor_candidates) - len(survivors),
            pairwise_rulings=len(pairwise_candidates) - len(rulings),
            open_rivals=len(rivalry_candidates) - len(rivalries),
            argued_refutations=len(refutation_candidates) - len(refutations),
            catalog_items=catalog_omitted,
        ),
    )


def build_claim_ledger_catalog(
    pack: EvidencePackV1,
    output_target: str,
    *,
    advisory_context: AdvisoryContextV1 | None = None,
    advisory_context_ref: str | None = None,
    retrieval_receipt_ref: str | None = None,
) -> ClaimLedgerInputCatalogV1:
    """Public functional spelling for bridge workflow integration."""

    pack = EvidencePackV1.model_validate(pack)
    return pack.claim_ledger_catalog(
        output_target,
        advisory_context=advisory_context,
        advisory_context_ref=advisory_context_ref,
        retrieval_receipt_ref=retrieval_receipt_ref,
    )


def legacy_pack(
    harness,
    problem_id: str,
    budget_chars: int = DEFAULT_EVIDENCE_PACK_BUDGET,
) -> tuple[str, set[str]]:
    """Historical thesis pack/citation tuple, generated by the shared extractor."""

    pack = assemble_evidence_pack(
        harness,
        problem_id,
        budget_chars=budget_chars,
    )
    return pack.legacy_text, set(pack.legacy_citable_ids)


__all__ = [
    "DEFAULT_EVIDENCE_PACK_BUDGET",
    "EvidenceLineageV1",
    "EvidencePackOmissionsV1",
    "EvidencePackV1",
    "OpenRivalryV1",
    "PairwiseRulingV1",
    "SurvivorEvidenceV1",
    "ArguedRefutationV1",
    "assemble_evidence_pack",
    "build_claim_ledger_catalog",
    "legacy_pack",
    "problem_family",
]
