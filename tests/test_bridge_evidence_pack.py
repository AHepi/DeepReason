"""C8 fixed-sequence evidence extraction and legacy thesis compatibility."""

from __future__ import annotations

import hashlib
import json

import pytest
from pydantic import ValidationError

from deepreason.bridge.evidence_pack import (
    EvidencePackV1,
    assemble_evidence_pack,
    build_claim_ledger_catalog,
    legacy_pack,
)
from deepreason.bridge.ledger import render_claim_ledger_stage_a_pack
from deepreason.harness import Harness
from deepreason.informal.trial import transcript_blob
from deepreason.ontology import (
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
    Warrant,
    WarrantType,
)
from deepreason.ontology.artifact import RefRole
from deepreason.scratch.models import (
    AdvisoryContextV1,
    InstanceRef,
    ScratchBlockV1,
    ScratchProvenanceV1,
)
from deepreason.views.thesis import evidence_pack as legacy_thesis_pack


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


def _skeleton(claim: str, mechanism: str) -> str:
    return json.dumps(
        {
            "claim": claim,
            "mechanism": mechanism,
            "forbidden": [
                {"case": f"counterexample to {claim}", "eval": "rubric:std"}
            ],
        }
    )


def _record(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_problem(
        Problem(
            id="pi-pack",
            description="Which explanation survives the bounded record?",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    alpha = harness.create_artifact(
        _skeleton("alpha explains the result", "alpha carries the effect"),
        provenance=Provenance(role="conjecturer", school="alpha-school"),
        problem_id="pi-pack",
    )
    beta = harness.create_artifact(
        _skeleton("beta explains the result", "beta mediates the effect"),
        provenance=Provenance(role="synthesizer", school="beta-school"),
        problem_id="pi-pack",
    )
    harness.record_measure(hv={alpha.id: 0.9, beta.id: 0.4})

    doomed = harness.create_artifact(
        _skeleton("mood explains the result", "mood is merely a label"),
        provenance=Provenance(role="conjecturer"),
        problem_id="pi-pack",
    )
    source = harness.create_artifact(
        "source-reliability: fixture S is reliable for this observation",
        provenance=Provenance(role="import"),
    )
    evidence = harness.create_artifact(
        "fixture observation: the measured carrier follows alpha",
        interface=Interface(
            refs=[Ref(target=source.id, role=RefRole.DEPENDENCE)]
        ),
        provenance=Provenance(role="import"),
        problem_id="pi-pack",
    )
    validity = harness.create_artifact(
        "nu: the observed carrier makes the criticism sound",
        interface=Interface(
            refs=[Ref(target=evidence.id, role=RefRole.EVIDENCE)]
        ),
        provenance=Provenance(role="critic"),
    )
    trace_ref = transcript_blob(
        harness,
        case="a mood names no mechanism",
        answer="the label is load-bearing",
        decisive_point="a mood names no mechanism",
    )
    attacker = harness.create_artifact(
        "critic: mood is a label and supplies no causal carrier",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w-evidence-pack",
                target=doomed.id,
                type=WarrantType.ARGUMENTATIVE,
                trace_ref=trace_ref,
                validity_node=validity.id,
            )
        ],
    )
    pairwise = harness.create_artifact(
        json.dumps(
            {
                "pairwise": {
                    "problem": "pi-pack",
                    "winner": alpha.id,
                    "loser": beta.id,
                    "decisive_point": "alpha names the measured carrier",
                }
            },
            sort_keys=True,
        ),
        codec="json",
        provenance=Provenance(role="critic"),
    )
    return harness, {
        "alpha": alpha.id,
        "beta": beta.id,
        "doomed": doomed.id,
        "source": source.id,
        "evidence": evidence.id,
        "validity": validity.id,
        "attacker": attacker.id,
        "trace": trace_ref,
        "pairwise": pairwise.id,
    }


def _root_digest(root) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_structured_pack_preserves_every_load_bearing_thesis_category(tmp_path):
    harness, ids = _record(tmp_path)

    pack = assemble_evidence_pack(
        harness,
        "pi-pack",
        formal_seq=harness._next_seq - 1,
    )

    assert pack.formal_seq == harness._next_seq - 1
    assert pack.problem_family_refs == ["pi-pack"]
    assert [item.artifact_ref for item in pack.survivors] == [
        ids["alpha"],
        ids["beta"],
    ]
    alpha = pack.survivors[0]
    assert alpha.claim == "alpha explains the result"
    assert alpha.mechanism == "alpha carries the effect"
    assert alpha.overturn_conditions == [
        "counterexample to alpha explains the result"
    ]

    assert len(pack.pairwise_rulings) == 1
    ruling = pack.pairwise_rulings[0]
    assert ruling.ruling_artifact_ref == ids["pairwise"]
    assert ruling.winner_ref == ids["alpha"]
    assert ruling.loser_ref == ids["beta"]
    assert ruling.decisive_point == "alpha names the measured carrier"

    assert len(pack.open_rivals) == 1
    assert pack.open_rivals[0].rival_refs == [ids["alpha"], ids["beta"]]

    assert len(pack.argued_refutations) == 1
    refutation = pack.argued_refutations[0]
    assert refutation.artifact_ref == ids["doomed"]
    assert refutation.attacker_ref == ids["attacker"]
    assert refutation.decisive_point == "a mood names no mechanism"
    assert refutation.decisive_warrant_ref == "w-evidence-pack"
    assert refutation.decisive_trace_ref == ids["trace"]
    assert refutation.lineage.warrant_refs == ["w-evidence-pack"]
    assert refutation.lineage.trace_refs == [ids["trace"]]
    assert refutation.lineage.evidence_refs == [ids["evidence"]]
    assert refutation.lineage.source_refs == [ids["source"]]


def test_pack_and_catalog_are_canonical_frozen_and_repeatable(tmp_path):
    harness, ids = _record(tmp_path)

    first = assemble_evidence_pack(harness, "pi-pack")
    second = assemble_evidence_pack(harness, "pi-pack")

    assert first == second
    assert first.id == second.id
    with pytest.raises(TypeError):
        first.survivors.append(first.survivors[0])
    with pytest.raises(ValidationError, match="canonical bridge.evidence-pack.v1"):
        EvidencePackV1.model_validate(
            {**first.model_dump(mode="json", by_alias=True), "id": _hash("f")}
        )

    catalog = build_claim_ledger_catalog(first, "a calibrated conclusion")
    assert catalog.formal_seq == first.formal_seq
    assert catalog.problem_ref == "pi-pack"
    assert catalog.items
    assert all(item.ref in {
        *harness.state.artifacts,
        ids["trace"],
        "pi-pack",
    } for item in catalog.items)

    rendered = render_claim_ledger_stage_a_pack(catalog)
    assert "A1" in rendered and "O1" in rendered
    assert "alpha explains the result" in rendered
    assert ids["alpha"] not in rendered
    assert ids["source"] not in rendered
    assert ids["evidence"] not in rendered
    assert ids["trace"] not in rendered
    assert catalog.id not in rendered


def test_canonical_advisory_context_adds_only_selected_scratch_blocks(tmp_path):
    harness, _ids = _record(tmp_path)
    pack = assemble_evidence_pack(harness, "pi-pack")
    instance = InstanceRef(run_id=_hash("a"), seq=pack.formal_seq)
    selected = ScratchBlockV1.create(
        body={"content": "A selected loose conjectural note."},
        instance=instance,
        provenance=ScratchProvenanceV1(actor="user"),
    )
    context = AdvisoryContextV1.create(
        warning="Scratch material is non-authoritative and may be wrong.",
        blocks=[selected],
        retrieval_receipt=_hash("b"),
        instance=instance,
    )

    catalog = build_claim_ledger_catalog(
        pack,
        "answer with calibrated categories",
        advisory_context=context,
    )

    scratch = [item for item in catalog.items if item.kind == "scratch"]
    assert [(item.handle, item.ref) for item in scratch] == [("B1", selected.id)]
    assert catalog.advisory_context_ref == context.id
    assert catalog.retrieval_receipt_ref == context.retrieval_receipt
    rendered = render_claim_ledger_stage_a_pack(catalog)
    assert "A selected loose conjectural note." in rendered
    assert selected.id not in rendered
    assert context.id not in rendered
    assert context.warning not in rendered

    with pytest.raises(ValueError, match="does not match"):
        build_claim_ledger_catalog(
            pack,
            "answer",
            advisory_context=context,
            retrieval_receipt_ref=_hash("c"),
        )


def test_formal_sequence_fence_and_historical_extraction_are_read_only(tmp_path):
    harness, _ids = _record(tmp_path)
    fence = harness._next_seq - 1
    before = _root_digest(harness.root)

    historical = Harness.at(harness.root, fence)
    pack = assemble_evidence_pack(historical, "pi-pack", formal_seq=fence)
    assert pack == assemble_evidence_pack(historical, "pi-pack", formal_seq=fence)
    assert _root_digest(harness.root) == before

    harness.record_measure(inputs=["after-fence"])
    with pytest.raises(ValueError, match="does not match supplied harness fence"):
        assemble_evidence_pack(harness, "pi-pack", formal_seq=fence)


def test_budgeted_catalog_and_legacy_view_share_the_exact_same_pack(tmp_path):
    harness, ids = _record(tmp_path)

    structured = assemble_evidence_pack(harness, "pi-pack", budget_chars=1_000)
    text, citable = legacy_pack(harness, "pi-pack", 1_000)

    assert text == structured.legacy_text
    assert citable == set(structured.legacy_citable_ids)
    assert legacy_thesis_pack(harness, "pi-pack", 1_000) == text
    assert text.endswith(
        "DIRECTIVE: from this record ONLY, produce the committed thesis "
        "(rules in your role brief). Cite bracketed ids exactly."
    )
    assert ids["alpha"][:12] in citable
    assert len(text) <= 1_400


@pytest.mark.parametrize("budget", [-1, 262_145])
def test_pack_budget_is_explicitly_bounded(tmp_path, budget):
    harness, _ids = _record(tmp_path)
    with pytest.raises(ValueError, match="budget_chars"):
        assemble_evidence_pack(harness, "pi-pack", budget_chars=budget)
