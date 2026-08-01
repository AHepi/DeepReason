"""Citation contract (admission §4): block refs on the wire, byte-checked quotes."""

from __future__ import annotations

import hashlib
import json

import pytest
from pydantic import ValidationError

from deepreason.admission import AdmissionInput, admit_sources
from deepreason.evidence.citations import (
    EVIDENCE_BLOCK_UNRECOVERABLE,
    EVIDENCE_CITATION_VERIFIED,
    EVIDENCE_QUOTE_MISMATCH,
    EVIDENCE_REF_TIER_INELIGIBLE,
    EVIDENCE_REF_UNKNOWN_BLOCK,
    EVIDENCE_REFS_UNBOUND,
    CitationIntegrityError,
    canonical_block_text,
    check_candidate_citations,
)
from deepreason.evidence.models import (
    AdmissionBlockV1,
    AttachedSourceProvenanceV1,
    EvidenceDossierV2,
)
from deepreason.llm.contracts import ConjecturerOutput, EvidenceRefClaimV1
from deepreason.llm.wire import AliasTable, ConjecturerWireContract
from deepreason.storage.blobs import BlobStore


PROVENANCE = AttachedSourceProvenanceV1(
    supplied_by="tests",
    acquisition_method="fixture",
    note=None,
)

MARKDOWN = (
    "# Study of Widgets\n"
    "\n"
    "Widgets are made of parts. This paragraph describes them at length.\n"
    "It continues on a second line.\n"
    "\n"
    "## Results\n"
    "\n"
    "The results paragraph interprets the table.\n"
).encode("utf-8")


def _dossier():
    dossier, _report = admit_sources(
        [AdmissionInput(locator="input-0", data=MARKDOWN)],
        problem_ref="question-" + "0" * 32,
        provenance=PROVENANCE,
    )
    return dossier


def _blobs(tmp_path):
    store = BlobStore(tmp_path / "blobs")
    assert store.put(MARKDOWN) == hashlib.sha256(MARKDOWN).hexdigest()
    return store


def _span_block(dossier):
    return next(block for block in dossier.blocks if block.text is None)


class _WrongBytes:
    def get(self, _ref):
        return b"entirely different source bytes"


def test_exact_quote_verifies_and_mismatch_is_a_typed_finding(tmp_path):
    dossier = _dossier()
    blobs = _blobs(tmp_path)
    block = _span_block(dossier)
    canonical = MARKDOWN[block.span_start : block.span_end].decode("utf-8")

    verified = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id, quote=canonical),),
        dossier,
        blobs,
    )
    assert [c.code for c in verified] == [EVIDENCE_CITATION_VERIFIED]
    assert verified[0].block_id == block.id and verified[0].quoted

    reworded = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id, quote=canonical.replace("Widgets", "Gadgets")),),
        dossier,
        blobs,
    )
    assert [c.code for c in reworded] == [EVIDENCE_QUOTE_MISMATCH]


WRAPPED = (
    "# Open challenge\n"
    "\n"
    "23 has stood since 1976 despite: decades of hand construction;\n"
    "numerical alternating-least-squares searches; SAT attacks; and a\n"
    "large reinforcement-learning search that rediscovered 23.\n"
    "\n"
    "1. **Symmetry obstruction.** The tensor has a large symmetry\n"
    "   group. If every rank-22 decomposition breaks it, 22 is out.\n"
    "\n"
    "    sum_k  U_k[i,j]  ==  T[(i,j),(l,m)]\n"
).encode("utf-8")


def _wrapped_case(tmp_path):
    dossier, _report = admit_sources(
        [AdmissionInput(locator="challenge.md", data=WRAPPED)],
        problem_ref="question-" + "0" * 32,
        provenance=PROVENANCE,
    )
    store = BlobStore(tmp_path / "blobs")
    store.put(WRAPPED)

    def block_containing(needle):
        for block in dossier.blocks:
            text = WRAPPED[block.span_start : block.span_end].decode("utf-8")
            if needle in text:
                return block, text
        raise AssertionError(f"no admitted block contains {needle!r}")

    def code(block, quote):
        checks = check_candidate_citations(
            (EvidenceRefClaimV1(block=block.id, quote=quote),), dossier, store
        )
        assert len(checks) == 1
        return checks[0]

    return block_containing, code


def test_quote_is_checked_against_the_blocks_words_not_its_line_layout(tmp_path):
    """Regression (tensorrank run-27b80f26bd398c718360e97e2a403593).

    That run recorded 42 EVIDENCE_QUOTE_MISMATCH and 0 verified quoted
    citations against a dossier hard-wrapped at ~72 columns. All 15
    distinct quotes were present in the blocks they cited; each differed
    from the admitted bytes only where the source carried a line break or
    alignment padding. Line layout must not decide whether a grounding is
    established, and folding must not blunt the check against a quote
    whose words differ.
    """

    block_containing, code = _wrapped_case(tmp_path)

    # A hard newline inside a paragraph, rendered by the model as a space.
    wrapped, canonical = block_containing("alternating-least-squares")
    assert "\n" in canonical
    assert code(wrapped, canonical).code == EVIDENCE_CITATION_VERIFIED
    assert code(wrapped, canonical).detail == "citation resolved and quote byte-verified"

    folded = code(wrapped, canonical.replace("\n", " "))
    assert folded.code == EVIDENCE_CITATION_VERIFIED
    assert folded.quoted and "folding whitespace" in folded.detail

    # A newline plus a list continuation indent collapses to one space.
    listed, list_text = block_containing("Symmetry obstruction")
    assert "\n   " in list_text
    assert code(listed, list_text.replace("\n   ", " ")).code == EVIDENCE_CITATION_VERIFIED

    # Alignment padding inside one line of a preformatted block.
    aligned, aligned_text = block_containing("sum_k")
    assert "  ==  " in aligned_text
    assert (
        code(aligned, aligned_text.strip().replace("  ", " ")).code
        == EVIDENCE_CITATION_VERIFIED
    )

    # Folding tolerates a different rendering of whitespace, nothing else.
    assert code(wrapped, canonical.replace("1976", "1979")).code == EVIDENCE_QUOTE_MISMATCH
    assert (
        code(wrapped, canonical.replace("\n", "")).code == EVIDENCE_QUOTE_MISMATCH
    ), "deleting whitespace joins words the source separated"
    assert code(wrapped, "   \n\t ").code == EVIDENCE_QUOTE_MISMATCH, (
        "a quote that folds to nothing must not match every block"
    )


def test_block_prefix_resolves_and_unknown_block_is_typed(tmp_path):
    dossier = _dossier()
    blobs = _blobs(tmp_path)
    block = _span_block(dossier)

    by_prefix = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id[:16]),), dossier, blobs
    )
    assert [c.code for c in by_prefix] == [EVIDENCE_CITATION_VERIFIED]
    assert by_prefix[0].block_id == block.id and not by_prefix[0].quoted

    unknown = check_candidate_citations(
        (EvidenceRefClaimV1(block="f" * 64),), dossier, blobs
    )
    assert [c.code for c in unknown] == [EVIDENCE_REF_UNKNOWN_BLOCK]


def test_citing_without_a_bound_dossier_is_typed():
    checks = check_candidate_citations(
        (EvidenceRefClaimV1(block="a" * 12),), None, None
    )
    assert [c.code for c in checks] == [EVIDENCE_REFS_UNBOUND]


def test_non_evidence_tier_blocks_cannot_ground_citations(tmp_path):
    text = "adapter-extracted narration"
    block = AdmissionBlockV1.create(
        parser_version="admission-parser.v1",
        source_sha256=hashlib.sha256(MARKDOWN).hexdigest(),
        kind="extracted",
        tier="workshop",
        span_start=0,
        span_end=len(MARKDOWN),
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        text=text,
    )
    dossier = _dossier()
    workshop = EvidenceDossierV2.create(
        problem_ref=dossier.problem_ref,
        parser_version=dossier.parser_version,
        sources=dossier.sources,
        blocks=tuple(sorted((*dossier.blocks, block), key=lambda b: b.id)),
        refusals=dossier.refusals,
        adapters=dossier.adapters,
        total_byte_count=dossier.total_byte_count,
        creation_provenance=dossier.creation_provenance,
    )
    checks = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id),), workshop, _blobs(tmp_path)
    )
    assert [c.code for c in checks] == [EVIDENCE_REF_TIER_INELIGIBLE]


def test_unrecoverable_block_text_never_passes_silently(tmp_path):
    dossier = _dossier()
    block = _span_block(dossier)
    quote = MARKDOWN[block.span_start : block.span_end].decode("utf-8")

    missing = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id, quote=quote),),
        dossier,
        BlobStore(tmp_path / "empty"),
    )
    assert [c.code for c in missing] == [EVIDENCE_BLOCK_UNRECOVERABLE]

    tampered = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id, quote=quote),),
        dossier,
        _WrongBytes(),
    )
    assert [c.code for c in tampered] == [EVIDENCE_BLOCK_UNRECOVERABLE]

    with pytest.raises(CitationIntegrityError):
        canonical_block_text(block, b"entirely different source bytes")


def test_wire_contract_carries_bounded_evidence_refs():
    contract = ConjecturerWireContract(AliasTable({"A1": "a" * 64}))
    output = contract.parse_compile(
        json.dumps(
            {
                "candidates": [
                    {
                        "content": "widgets are modular",
                        "typicality": 0.4,
                        "neighbours": ["A1"],
                        "evidence_refs": [
                            {"block": "ab12" * 4, "quote": "made of parts"},
                            {"block": "cd34" * 16},
                        ],
                    }
                ]
            }
        )
    )
    assert isinstance(output, ConjecturerOutput)
    refs = output.candidates[0].evidence_refs
    assert [ref.block for ref in refs] == ["ab12" * 4, "cd34" * 16]
    assert refs[0].quote == "made of parts" and refs[1].quote is None

    with pytest.raises(Exception):
        contract.parse_compile(
            json.dumps(
                {
                    "candidates": [
                        {
                            "content": "x",
                            "typicality": 0.5,
                            "evidence_refs": [{"block": "NOT-HEX"}],
                        }
                    ]
                }
            )
        )


def test_atomic_and_reasoning_wire_paths_preserve_evidence_refs():
    from deepreason.llm.wire import AtomicConjectureWireContractV1

    compact = AtomicConjectureWireContractV1(AliasTable({}))
    turn = compact.parse_compile(
        json.dumps(
            {
                "candidate": {
                    "content": "widgets are modular",
                    "typicality": 0.4,
                    "neighbours": [],
                    "evidence_refs": [{"block": "ab12" * 4}],
                }
            }
        )
    )
    assert turn.candidates[0].evidence_refs[0].block == "ab12" * 4

    reasoning = AtomicConjectureWireContractV1(AliasTable({}), reasoning=True)
    turn = reasoning.parse_compile(
        json.dumps(
            {
                "candidate": {
                    "claim": "widgets are modular",
                    "mechanism": "parts compose",
                    "counterconditions": ["a monolithic widget"],
                    "typicality": 0.4,
                    "evidence_refs": [
                        {"block": "ab12" * 4, "quote": "made of parts"}
                    ],
                }
            }
        )
    )
    proposal = turn.candidates[0]
    assert proposal.evidence_refs[0].quote == "made of parts"


def test_rendered_pack_lists_citable_block_ids(tmp_path):
    from deepreason.evidence.models import RunInputManifestV2, RunInputProblemV2
    from deepreason.evidence.dossier import pack_dossier
    from deepreason.evidence.render import render_dossier_pack

    dossier = _dossier()
    blobs = _blobs(tmp_path)
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id=dossier.problem_ref,
            description="what are widgets made of?",
            criteria=(),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
        brain_snapshot_digest=None,
    )
    receipt = pack_dossier(
        root=tmp_path,
        run_input=run_input,
        dossier=dossier,
        work_order_ref="sha256:" + "a" * 64,
        query="widgets",
        state_fence="formal:0;scratch:0;workflow:0",
        maximum_sources=4,
        maximum_excerpt_bytes_per_source=4_096,
        maximum_total_excerpt_bytes=8_192,
    )
    rendered = render_dossier_pack(blobs=blobs, dossier=dossier, receipt=receipt)
    assert "citable_blocks:" in rendered
    for block in dossier.blocks:
        if block.tier == "evidence":
            assert f"block={block.id[:16]}" in rendered
    assert "evidence_refs" in rendered


def test_conj_records_one_durable_measure_per_citation_check(tmp_path):
    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.ontology import Commitment, Problem, ProblemProvenance
    from deepreason.rules.conj import conj

    harness = Harness(tmp_path / "run")
    commitment = Commitment(id="k-open", eval="predicate:True")
    harness.register_commitment(commitment)
    problem = harness.register_problem(
        Problem(
            id="pi-citations",
            description="What are widgets made of?",
            criteria=[commitment.id],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    response = json.dumps(
        {
            "candidates": [
                {
                    "content": "Widgets are made of parts.",
                    "typicality": 0.4,
                    "evidence_refs": [{"block": "ab12" * 4, "quote": "made of parts"}],
                }
            ]
        }
    )
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([response])},
        harness.blobs,
        model_profile="compact",
    )
    admitted = conj(
        harness,
        problem.id,
        adapter,
        Config(VS_K=1, model_profile="compact"),
    )
    assert len(admitted) == 1
    # No dossier is bound to this run, so the single claimed citation must
    # surface as exactly one typed, durable measure — never a silent pass.
    citation_events = [
        event
        for event in harness.log.read()
        if event.inputs and str(event.inputs[0]).startswith("evidence-citation:")
    ]
    assert len(citation_events) == 1
    assert citation_events[0].inputs[0] == (
        "evidence-citation:" + EVIDENCE_REFS_UNBOUND
    )
    assert citation_events[0].inputs[1] == "ab12" * 4
    assert citation_events[0].inputs[2] == admitted[0].id


def test_evidence_ref_claims_are_strict_and_bounded():
    with pytest.raises(ValidationError):
        EvidenceRefClaimV1(block="ab")  # below the 12-char prefix floor
    with pytest.raises(ValidationError):
        EvidenceRefClaimV1(block="a" * 64, quote="")
    with pytest.raises(ValidationError):
        EvidenceRefClaimV1(block="a" * 64, quote="q" * 2_001)
