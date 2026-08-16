"""P4 — three-layer citable evidence (v2 calculus program, R62).

The acceptance condition R62 adopts binds four layers, and each one is only
worth anything because the next one reads what it wrote:

    block bytes appear in the recorded context-exposure receipt
    model returns block ID plus exact quote
    semantic admission byte-checks quote against those same recorded bytes
    claim interface depends on the admitted evidence record

These tests are written against the RECORD at each layer, never against the
local variable that produced it — a receipt and a checker that agree only
because one author wrote both on one afternoon is the failure mode the
requirement exists to prevent.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deepreason.workflow.transaction import (
    ContextNamespace,
    ContextPackPlanV1,
    VisibleContextItemV1,
)


_DIGEST = "b" * 64


def _item(namespace, alias):
    return VisibleContextItemV1(
        namespace=namespace,
        alias=alias,
        object_ref="a" * 64,
        content_sha256=_DIGEST,
        planned_bytes=17,
    )


# --- A1: the record ---------------------------------------------------------


def test_the_evidence_namespace_owns_its_own_alias_prefix():
    """A1 — an evidence item is EVD_, and no other namespace may borrow it."""

    item = _item(ContextNamespace.EVIDENCE, "EVD_001")
    assert item.namespace is ContextNamespace.EVIDENCE

    for namespace in (
        ContextNamespace.SOURCE,
        ContextNamespace.SIMULATION,
        ContextNamespace.SCRATCH,
    ):
        with pytest.raises(ValidationError):
            _item(namespace, "EVD_001")

    for alias in ("SRC_001", "SIM_001", "SCR_001"):
        with pytest.raises(ValidationError):
            _item(ContextNamespace.EVIDENCE, alias)


def test_a_citable_plan_is_a_declarable_plan_kind():
    """A1 — the plan kind exists and carries evidence-namespace items."""

    plan = ContextPackPlanV1.create(
        work_id="sha256:" + "c" * 64,
        attempt_index=0,
        plan_kind="citable",
        items=(_item(ContextNamespace.EVIDENCE, "EVD_001"),),
        maximum_bytes=17,
        rendered_bytes=17,
    )
    assert plan.plan_kind == "citable"
    assert plan.items[0].alias == "EVD_001"


# --- A2: the render split ---------------------------------------------------


class _Blobs:
    def __init__(self, mapping):
        self._mapping = mapping

    def get(self, digest):
        return self._mapping[digest]


def _span_block(text, *, tier="evidence"):
    """An evidence-tier block. Evidence blocks are ALWAYS span blocks — the
    model refuses an inlined one — so the bytes live in the store and the
    renderer has to recover them, which is what makes the drop case real."""

    import hashlib

    from deepreason.evidence.models import AdmissionBlockV1

    body = text.encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()
    block = AdmissionBlockV1.model_validate(
        {
            "schema": "admission-block.v1",
            "id": hashlib.sha256(b"id:" + body).hexdigest(),
            "source_sha256": digest,
            "kind": "paragraph",
            "tier": tier,
            "span_start": 0,
            "span_end": len(body),
            "text_sha256": digest,
        }
    )
    return block, digest, body


def test_the_legend_reports_exactly_the_blocks_whose_bytes_it_rendered():
    """A2 — `shown` is the receipt's source of truth, not the input list.

    A block past the cap is in the input and not in the text; the receipt must
    follow the text, because that is what the model could see.
    """

    from deepreason.evidence import citable_legend

    made = [_span_block(f"paragraph number {index}") for index in range(4)]
    blocks = tuple(block for block, _digest, _body in made)
    store = _Blobs({digest: body for _block, digest, body in made})
    legend = citable_legend(blocks, store, maximum_blocks=2)

    assert legend is not None
    assert len(legend.shown) == 2
    assert legend.shown == blocks[:2]
    for block in legend.shown:
        assert f"[{block.id[:16]}]" in legend.text
    for block in blocks[2:]:
        assert block.id[:16] not in legend.text
    assert "(+2 further citable blocks not shown)" in legend.text


def test_an_unrenderable_block_is_in_neither_the_text_nor_the_receipt():
    """A2 — the silent drop is the reason the two fields exist."""

    from deepreason.evidence import citable_legend

    good, good_digest, good_body = _span_block("a recoverable paragraph")
    # The renderer fetches a span block's bytes by digest; this one's source is
    # not in the store, and presentation swallows the failure rather than
    # failing the pack.
    broken, _digest, _body = _span_block("bytes that are not in the store")

    legend = citable_legend((good, broken), _Blobs({good_digest: good_body}))

    assert legend is not None
    assert legend.shown == (good,)
    assert broken.id[:16] not in legend.text


# --- A3, A4: the conjecturer half ------------------------------------------


DERIVED_PROBLEM_ID = "pi-p4-derived"


def _evidence_root(tmp_path):
    """A root with one bound dossier, a seed problem, and a DERIVED problem.

    The derived problem is the whole point: it is not an epoch problem, so
    before P4 its conjecturer saw no block ids at all.
    """

    from deepreason.admission.parse import AdmissionInput, admit_sources
    from deepreason.capabilities.policy import (
        AttachedEvidencePolicyV1,
        InquiryCapabilityPolicyV1,
    )
    from deepreason.evidence import (
        AttachedSourceProvenanceV1,
        RunInputManifestV2,
        RunInputProblemV2,
        bind_run_input,
    )
    from deepreason.harness import Harness
    from deepreason.ontology import Problem
    from deepreason.ontology.problem import ProblemProvenance
    from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
    from deepreason.storage.blobs import BlobStore

    from tests.test_amendment_epochs import (
        ORIGINAL_QUESTION,
        SOURCE_TEXT,
        STAMP,
        _problem_id,
    )
    from tests.test_run_input_v6_commitments import (
        _commitment,
        _config,
        _control,
        _write_qualification,
    )

    root = tmp_path / "p4-root"
    commitment = _commitment()
    seed_id = _problem_id(ORIGINAL_QUESTION)
    dossier, _report = admit_sources(
        [AdmissionInput(locator="delayed.md", data=SOURCE_TEXT.encode("utf-8"))],
        problem_ref=seed_id,
        provenance=AttachedSourceProvenanceV1(
            supplied_by="p4 fixture",
            acquisition_method="offline construction",
        ),
    )
    BlobStore(root / "blobs").put(SOURCE_TEXT.encode("utf-8"))
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=seed_id,
            description=ORIGINAL_QUESTION,
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    config = _config()
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(6),
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2",
            attached_evidence=AttachedEvidencePolicyV1(
                enabled=True,
                maximum_sources=8,
                maximum_total_bytes=64 * 1024,
                maximum_excerpt_bytes_per_source=4 * 1024,
                maximum_sources_per_pack=4,
            ),
        ),
        run_input_digest=run_input.run_input_digest,
    )
    bind_run_manifest(manifest, root)
    _write_qualification(root, manifest)

    harness = Harness(root)
    harness.register_commitment(commitment)
    harness.register_problem(
        Problem(
            id=seed_id,
            description=ORIGINAL_QUESTION,
            criteria=[commitment.id],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    harness.register_problem(
        Problem(
            id=DERIVED_PROBLEM_ID,
            description="Which sampling regime removes the oscillation?",
            criteria=[commitment.id],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "discrimination", "from": [seed_id]}
            ),
        )
    )
    return harness, manifest, config, dossier


def _conjecture_on(harness, manifest, config, problem_id, response):
    """One real `conj` dispatch against a mock endpoint."""

    import json

    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.budget import TokenMeter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.llm.firewall import leases_from_manifest
    from deepreason.rules.conj import conj

    from tests.test_v6_compact_recovery_transition import _bind_classification

    prompts: list[str] = []
    route = manifest.roles["conjecturer"][0]

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        return json.dumps(response)

    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(
                complete,
                name=route.base_url,
                model=route.model_id,
                max_tokens=route.max_tokens,
            )
        },
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    _bind_classification(harness, manifest)
    adapter.bind_v6_authority(harness, manifest)
    registered = conj(
        harness,
        problem_id,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    return prompts, registered


def _abstain():
    return {
        "abstention": {
            "search_signal": "stuck",
            "note": "no candidate this turn",
        }
    }


def test_a_derived_problem_sees_the_citable_block_ids(tmp_path):
    """A3 — the legend reaches a problem that is not an epoch problem."""

    harness, manifest, config, dossier = _evidence_root(tmp_path)
    citable = [block for block in dossier.blocks if block.tier == "evidence"]
    assert citable, "fixture admitted no citable evidence blocks"

    prompts, _registered = _conjecture_on(
        harness, manifest, config, DERIVED_PROBLEM_ID, _abstain()
    )

    (prompt,) = prompts
    assert "CITABLE EVIDENCE BLOCKS" in prompt
    assert any(f"[{block.id[:16]}]" in prompt for block in citable)


def test_the_exposure_receipt_records_the_blocks_the_prompt_carried(tmp_path):
    """A4 — layer 1, read from the RECORD.

    Every evidence-namespace item names a block by its full id and pins the
    block's own `text_sha256`; the set is exactly what the prompt showed.
    """

    harness, manifest, config, _dossier = _evidence_root(tmp_path)

    prompts, _registered = _conjecture_on(
        harness, manifest, config, DERIVED_PROBLEM_ID, _abstain()
    )
    (prompt,) = prompts

    (work,) = harness.workflow_state.transaction_work.values()
    exposed = [
        item
        for item in work.exposure.exposed_items
        if item.namespace.value == "evidence"
    ]
    assert exposed, "no citable block reached the exposure receipt"
    by_id = {block.id: block for block in _dossier.blocks}
    for item in exposed:
        assert item.alias.startswith("EVD_")
        block = by_id[item.object_ref]
        assert item.content_sha256 == block.text_sha256
        assert f"[{block.id[:16]}]" in prompt
    # And nothing the prompt did not carry.
    shown_ids = {
        block.id
        for block in _dossier.blocks
        if f"[{block.id[:16]}]" in prompt
    }
    assert {item.object_ref for item in exposed} == shown_ids


# --- A5, A6: layer 3, the admission binding ---------------------------------


def test_a_block_that_was_not_exposed_to_this_call_does_not_verify():
    """A5 — the id is real, the quote is exact, and it still does not pass.

    This is the whole of layer 3: a citation is a claim about bytes the model
    was shown, so a correct quote of a block nobody put in the prompt is a
    claim the record cannot support.
    """

    from deepreason.evidence.citations import (
        EVIDENCE_CITATION_VERIFIED,
        EVIDENCE_REF_NOT_EXPOSED,
        check_candidate_citations,
    )
    from deepreason.llm.contracts import EvidenceRefClaimV1

    shown, shown_digest, shown_body = _span_block("the loop gain exceeds unity")
    hidden, hidden_digest, hidden_body = _span_block("sampling removes the wobble")
    store = _Blobs({shown_digest: shown_body, hidden_digest: hidden_body})

    class _Dossier:
        blocks = (shown, hidden)

    refs = (
        EvidenceRefClaimV1(block=shown.id, quote="loop gain"),
        EvidenceRefClaimV1(block=hidden.id, quote="removes the wobble"),
    )

    checks = check_candidate_citations(
        refs,
        _Dossier(),
        store,
        exposed_block_ids=frozenset({shown.id}),
    )

    assert [check.code for check in checks] == [
        EVIDENCE_CITATION_VERIFIED,
        EVIDENCE_REF_NOT_EXPOSED,
    ]
    # The refusal still names the block it resolved, so criticism can attack it.
    assert checks[1].block_id == hidden.id
    assert checks[1].quoted is True


def test_omitting_the_exposure_binding_changes_no_outcome():
    """A6 — every caller that has not opted in keeps its exact behaviour."""

    from deepreason.evidence.citations import (
        EVIDENCE_CITATION_VERIFIED,
        check_candidate_citations,
    )
    from deepreason.llm.contracts import EvidenceRefClaimV1

    shown, shown_digest, shown_body = _span_block("the loop gain exceeds unity")
    hidden, hidden_digest, hidden_body = _span_block("sampling removes the wobble")
    store = _Blobs({shown_digest: shown_body, hidden_digest: hidden_body})

    class _Dossier:
        blocks = (shown, hidden)

    refs = (
        EvidenceRefClaimV1(block=shown.id, quote="loop gain"),
        EvidenceRefClaimV1(block=hidden.id, quote="removes the wobble"),
    )

    checks = check_candidate_citations(refs, _Dossier(), store)

    assert [check.code for check in checks] == [
        EVIDENCE_CITATION_VERIFIED,
        EVIDENCE_CITATION_VERIFIED,
    ]


def test_an_empty_exposure_set_is_not_the_same_as_no_binding():
    """A5 — a v6 call that exposed nothing refuses every citation, and that is
    a different state from a caller that never opted in."""

    from deepreason.evidence.citations import (
        EVIDENCE_REF_NOT_EXPOSED,
        check_candidate_citations,
    )
    from deepreason.llm.contracts import EvidenceRefClaimV1

    block, digest, body = _span_block("the loop gain exceeds unity")

    class _Dossier:
        blocks = (block,)

    checks = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id, quote="loop gain"),),
        _Dossier(),
        _Blobs({digest: body}),
        exposed_block_ids=frozenset(),
    )

    assert [check.code for check in checks] == [EVIDENCE_REF_NOT_EXPOSED]


# --- A7, A8: layer 2, the quoted subtype ------------------------------------


def test_the_quoted_subtype_cannot_be_built_without_its_quote():
    """A7 — the requirement is in the type, not in a prompt asking nicely."""

    from deepreason.llm.contracts import EvidenceRefClaimV1, QuotedEvidenceRefV1

    block = "a" * 64
    assert QuotedEvidenceRefV1(block=block, quote="x").quote == "x"

    for bad in (None, ""):
        with pytest.raises(ValidationError):
            QuotedEvidenceRefV1(block=block, quote=bad)
    with pytest.raises(ValidationError):
        QuotedEvidenceRefV1(block=block)

    # R62's "old V1 unmutated": the conjecturer channel still ships with an
    # optional quote, and this test is what would notice a global tightening.
    assert EvidenceRefClaimV1(block=block).quote is None


def test_the_critic_contracts_carry_quoted_evidence_and_keep_their_ids():
    """A8 — a new optional field is not a new contract."""

    from deepreason.llm.contracts import (
        ArgumentativeCriticOutput,
        BatchCase,
        QuotedEvidenceRefV1,
    )
    from deepreason.llm.packs import AliasTable
    from deepreason.llm.wire import AtomicCriticWireContractV1, BatchCriticWireContractV2

    ref = QuotedEvidenceRefV1(block="a" * 64, quote="x")
    assert ArgumentativeCriticOutput(
        attack=False, premise="p", premise_evidence=[ref]
    ).premise_evidence == [ref]
    assert BatchCase(
        target="t", attack=False, premise="p", premise_evidence=[ref]
    ).premise_evidence == [ref]

    aliases = AliasTable({"SRC_001": "target-1"})
    assert (
        AtomicCriticWireContractV1(aliases, expected_target="target-1").contract_id
        == "critic.atomic-target.v1"
    )
    assert (
        BatchCriticWireContractV2(aliases, expected_targets=("target-1",)).contract_id
        == "batch-critic.v2"
    )


# --- A9, A10, A11: layer 4, the claim's dependence ---------------------------


def _dossier_at(root):
    """Bind one real dossier to a root before its harness opens."""

    from deepreason.admission.parse import AdmissionInput, admit_sources
    from deepreason.evidence import (
        AttachedSourceProvenanceV1,
        RunInputManifestV2,
        RunInputProblemV2,
        bind_run_input,
    )
    from deepreason.ontology import Commitment
    from deepreason.storage.blobs import BlobStore

    text = (
        "# Sirens\n\n"
        "Emergency vehicles in this jurisdiction are painted red, and the "
        "colour is fixed by regulation rather than by preference.\n"
    )
    dossier, _report = admit_sources(
        [AdmissionInput(locator="sirens.md", data=text.encode("utf-8"))],
        problem_ref="colour-of-a-siren",
        provenance=AttachedSourceProvenanceV1(
            supplied_by="p4 fixture",
            acquisition_method="offline construction",
        ),
    )
    BlobStore(root / "blobs").put(text.encode("utf-8"))
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id="colour-of-a-siren",
            description="What colour is a siren?",
            criteria=(Commitment(id="k-colour", eval="predicate:'colour' in content"),),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    return dossier, text


def _citable_block_of(dossier):
    blocks = [
        block
        for block in dossier.blocks
        if block.tier == "evidence" and block.kind == "paragraph"
    ]
    assert blocks, "fixture admitted no citable evidence paragraph"
    return blocks[0]


def _premise_run_with_evidence(tmp_path, quote):
    """The Rung 2 siren loop, with one dossier bound and one quoted citation."""

    import json

    from deepreason.premises import standing_attributions
    from tests.test_premise_channel_loop import _PREMISE, _siren_run

    root = tmp_path / "run"
    root.mkdir(parents=True)
    dossier, _text = _dossier_at(root)
    block = _citable_block_of(dossier)

    harness, scheduler = _siren_run(
        tmp_path,
        [
            json.dumps({"attack": False, "case": ""}),
            json.dumps(
                {
                    "attack": False,
                    "case": "",
                    "premise": _PREMISE,
                    "premise_evidence": [{"block": block.id, "quote": quote}],
                }
            ),
        ],
    )
    scheduler.step()
    scheduler.step()
    return harness, block, standing_attributions(harness)


def _citation_codes(harness):
    return [
        event.inputs[0].split(":", 1)[1]
        for event in harness.log.read()
        if event.rule.value == "Measure"
        and event.inputs
        and event.inputs[0].startswith("premise-citation:")
    ]


def test_a_verified_quote_makes_the_attribution_depend_on_the_citation(tmp_path):
    """A9, A11 — the fourth layer, and the mention law surviving it."""

    from deepreason.premises import PREMISE_CITATION_SCHEMA

    harness, _block, attributions = _premise_run_with_evidence(
        tmp_path, "fixed by regulation"
    )

    assert _citation_codes(harness) == ["EVIDENCE_CITATION_VERIFIED"]
    assert len(attributions) == 1
    attribution_id, _problem_id, premise_id = attributions[0]
    attribution = harness.state.artifacts[attribution_id]

    depends = {
        ref.target for ref in attribution.interface.refs if ref.role.value == "dependence"
    }
    mentions = {
        ref.target for ref in attribution.interface.refs if ref.role.value == "mention"
    }
    assert len(depends) == 1
    # A11: the premise is mentioned and never depended on — layer 4 adds a
    # support edge onto the citation record, it does not touch the mention law.
    assert premise_id in mentions and premise_id not in depends

    citation = harness.state.artifacts[next(iter(depends))]
    body = citation.content_ref.removeprefix("inline:")
    assert PREMISE_CITATION_SCHEMA in body


def test_a_quote_that_is_not_in_the_bytes_grounds_nothing(tmp_path):
    """A10 — the failed check is recorded and the attribution stands alone.

    "Stands alone" is the point: the premise is still filed, because a bad
    citation is not a reason to lose the presupposition. What it does not get
    is a support edge onto evidence that was never verified.
    """

    harness, _block, attributions = _premise_run_with_evidence(
        tmp_path, "painted blue by ancient custom"
    )

    assert _citation_codes(harness) == ["EVIDENCE_QUOTE_MISMATCH"]
    assert len(attributions) == 1
    attribution = harness.state.artifacts[attributions[0][0]]
    assert not [
        ref for ref in attribution.interface.refs if ref.role.value == "dependence"
    ]


# --- A12: the recovery half -------------------------------------------------


def test_a_resumed_critic_tolerates_an_evidence_exposure_entry(tmp_path):
    """A12 — the recovery half moves with the dispatch half.

    `DR-SEAM-rules-x-workflow` names the forgotten-recovery failure explicitly:
    a field the live path writes and recovery does not understand makes a
    resumed run diverge from the run it resumed. Before the narrowing, recovery
    asserted EVERY critic exposure entry was in the source namespace and every
    alias was a target — so the first resumed call that had been shown citable
    evidence would have refused with an authority error.
    """

    import hashlib

    from deepreason.harness import Harness
    from deepreason.ontology import Provenance
    from deepreason.workflow.criticism import CriticismAssignmentV1
    from deepreason.workflow.models import WorkflowTaskKind
    from deepreason.workflow.transaction import (
        ContextNamespace,
        VisibleContextItemV1,
    )

    from tests.test_v6_nonconjecture_recovery import (
        _lease,
        _manifest,
        _provider_prefix,
        _recover,
    )

    _config_value, manifest = _manifest()
    root = tmp_path / "criticism-with-evidence"
    harness = Harness(root)
    target = harness.create_artifact(
        "one school-owned target",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    lease = _lease(manifest, "argumentative_critic", 1)
    assignment = CriticismAssignmentV1.create(
        manifest_digest=manifest.sha256,
        target_id=target.id,
        owner_school_id="school-0",
        critic_school_id="school-1",
        eligible_school_order=("school-1", "school-2"),
        order_index=0,
        seat=1,
        endpoint_id=lease.endpoint_id,
        route_sha256=lease.route_sha256,
        maximum_attempts=2,
    )
    harness.record_criticism_obligation(assignment)
    content = target.content_ref.removeprefix("inline:").encode("utf-8")
    block, _digest, _body = _span_block("a paragraph the critic was shown")

    _preparation, provider = _provider_prefix(
        harness,
        manifest,
        task_kind=WorkflowTaskKind.CRITICISM,
        role="argumentative_critic",
        seat=1,
        contract_id="batch-critic.v2",
        payload={
            "schema": "criticism.semantic-task.v1",
            "critic_school_id": "school-1",
            "target_ids": [target.id],
            "assignment_refs": [assignment.id],
            "coverage_attempt_index": 0,
            "phase": "qualification",
            "caller_trigger_ref": None,
        },
        trigger_prefix="criticism:",
        raw=b'{"cases":[{"target_alias":"SRC_001","attack":false,"case":""}]}',
        target_refs=(target.id,),
        input_refs=(assignment.id,),
        items=(
            VisibleContextItemV1(
                namespace=ContextNamespace.SOURCE,
                alias="SRC_001",
                object_ref=target.id,
                content_sha256=hashlib.sha256(content).hexdigest(),
                planned_bytes=64,
            ),
            VisibleContextItemV1(
                namespace=ContextNamespace.EVIDENCE,
                alias="EVD_001",
                object_ref=block.id,
                content_sha256=block.text_sha256,
                planned_bytes=0,
            ),
        ),
    )

    _reopened, item, admission = _recover(root, manifest, provider)

    assert admission is not None
    exposed = {entry.alias: entry.namespace.value for entry in item.exposure.exposed_items}
    assert exposed == {"SRC_001": "source", "EVD_001": "evidence"}
