"""C7 end-to-end proof that new semantics return through Stage A."""

from __future__ import annotations

import json

from deepreason.bridge.compose import (
    BridgeComposer,
    CompositionRequestV1,
    CompositionStatus,
)
from deepreason.bridge.ledger import (
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV1,
    amend_claim_ledger_stage_a,
    build_claim_ledger_stage_a,
)
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.storage.blobs import BlobStore


def _adapter(tmp_path, role, responses):
    return LLMAdapter(
        {role: MockEndpoint(responses)},
        BlobStore(tmp_path / role),
        retry_max=2,
    )


def test_stage_b_new_inference_requires_explicit_additions_only_stage_a_amendment(
    tmp_path,
):
    catalog = ClaimLedgerInputCatalogV1.create(
        problem_ref="problem-1",
        formal_seq=4,
        problem_text="What follows from the measured increase?",
        output_target="answer",
        items=[
            ClaimLedgerCatalogItemV1(
                handle="S1",
                kind="source",
                ref="source-1",
                excerpt="The measured input increased.",
            )
        ],
    )
    initial = build_claim_ledger_stage_a(
        _adapter(
            tmp_path / "initial",
            "summarizer",
            [
                json.dumps(
                    {
                        "entries": [
                            {
                                "entry_key": "K1",
                                "claim_class": "source_fact",
                                "claim": "The measured input increased.",
                                "source_handles": ["S1"],
                            }
                        ]
                    }
                )
            ],
        ),
        catalog,
    )
    request = CompositionRequestV1(
        output_target="answer",
        formatting_profile="plain",
        desired_length_chars=4_096,
        maximum_sections=4,
    )
    composition = BridgeComposer(
        _adapter(
            tmp_path / "compose",
            "thesis",
            [
                json.dumps(
                    {
                        "sections": [],
                        "resolution": "underdetermined",
                        "resolution_reason": "The inference is not in the ledger.",
                        "ledger_amendment_request": {
                            "requested_class": "supported_inference",
                            "proposed_claim": "The response follows from the increase.",
                            "reason": "The requested conclusion needs an explicit premise.",
                        },
                    }
                )
            ],
        )
    ).compose(initial.ledger, request)

    assert composition.status == CompositionStatus.LEDGER_AMENDMENT_NEEDED
    assert composition.output is None
    prior_bytes = initial.ledger.model_dump_json()
    amended = amend_claim_ledger_stage_a(
        _adapter(
            tmp_path / "amend",
            "summarizer",
            [
                json.dumps(
                    {
                        "entries": [
                            {
                                "entry_key": "K2",
                                "claim_class": "supported_inference",
                                "claim": "The response follows from the increase.",
                                "premise_keys": ["P1"],
                            }
                        ]
                    }
                )
            ],
        ),
        initial,
        request=composition.amendment_needed,
    )

    assert initial.ledger.model_dump_json() == prior_bytes
    assert amended.amended
    inference = amended.ledger.entries[-1]
    assert inference.premise_refs == [initial.ledger.entries[0].id]

    final = BridgeComposer(
        _adapter(
            tmp_path / "final",
            "thesis",
            [
                json.dumps(
                    {
                        "sections": [
                            {
                                "span_id": "S1",
                                "text": "From the increase, the response follows.",
                                "rendering_mode": "inference",
                                "ledger_entry_handles": ["E2"],
                            }
                        ],
                        "resolution": "answered",
                    }
                )
            ],
        )
    ).compose(amended.ledger, request)

    assert final.status == CompositionStatus.COMPOSED
    assert final.output.sections[0].ledger_entry_ids == [inference.id]
