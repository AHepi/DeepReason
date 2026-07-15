"""C12: MiniReason reuses the canonical scratch and bridge protocol."""

from __future__ import annotations

import json

import pytest

from deepreason.bridge import BridgeAction, ClaimClass, RenderingMode
from deepreason.bridge.validate import validate_bridge_output, validate_claim_ledger
from deepreason.cli.main import main as cli_main
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
from deepreason.scratch.models import ScratchProvenanceV1
from minireason.advisory import MiniAdvisoryError, MiniAdvisorySession
from minireason.compat import initialize


_STAMP = "2026-07-16T00:00:00Z"
_ENDPOINT = "mock://mini-advisory"
_MODEL = "mini-scripted"


def _route() -> dict:
    return {
        "endpoint_id": "mini-scripted-seat",
        "endpoint": _ENDPOINT,
        "model": _MODEL,
        "provider": "mock",
        "family": "mini-scripted",
        "output_mechanism": "json_text",
    }


def _manifest(*, scratch: bool = True, grounded: bool = True):
    roles = {"summarizer": _route(), "thesis": _route()} if grounded else {}
    return compile_run_manifest(
        Config(
            engine_profile="mini",
            model_profile="compact",
            scratchpad={
                "enabled": scratch,
                "max_blocks_per_pack": 4,
                "max_guides_per_pack": 0,
                "semantic_retrieval": False,
                "coverage_slot_every_n_packs": 8,
            },
            bridge={
                "mode": "grounded_two_stage" if grounded else "legacy_thesis",
                "grounding_review": False,
                "max_schema_repair_attempts": 1,
                "max_grounding_repair_attempts": 0,
                "output_section_limit": 4,
            },
            roles=roles,
        ),
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=_STAMP,
    )


def _bound_session(tmp_path, **manifest_options) -> MiniAdvisorySession:
    root = tmp_path / "mini-v3-run"
    root.mkdir()
    bind_run_manifest(_manifest(**manifest_options), root)
    return MiniAdvisorySession.open(root)


def _adapter(session: MiniAdvisorySession, *, blob_store=None) -> LLMAdapter:
    scratch_fact = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": "The scratch idea is an established fact.",
                    "scratch_handles": ["B1"],
                }
            ]
        }
    )
    safe_unknown = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "unknown",
                    "claim": "The requested conclusion is not established.",
                    "scratch_handles": ["B1"],
                }
            ],
            "uncovered_requirements": [
                {
                    "requirement": "Grounded evidence for the requested conclusion.",
                    "reason": "Scratch provenance is advisory, not evidence.",
                    "scratch_handles": ["B1"],
                }
            ],
        }
    )
    unresolved_output = json.dumps(
        {
            "sections": [
                {
                    "span_id": "S1",
                    "text": "The requested conclusion remains unknown.",
                    "rendering_mode": "unknown",
                    "ledger_entry_handles": ["E1"],
                }
            ],
            "resolution": "insufficient_evidence",
            "resolution_reason": "The bounded record supplies no grounding.",
        }
    )
    return LLMAdapter(
        {
            "summarizer": MockEndpoint(
                [scratch_fact, safe_unknown], name=_ENDPOINT, model=_MODEL
            ),
            "thesis": MockEndpoint(
                [unresolved_output], name=_ENDPOINT, model=_MODEL
            ),
        },
        blob_store or session.harness.blobs,
        retry_max=1,
        model_profile="compact",
        output_mechanism="json_text",
        leases=leases_from_manifest(session.manifest),
    )


def _files(root):
    return {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_mini_v3_scratch_bridge_replays_in_full_harness_without_migration(
    tmp_path, capsys
):
    session = _bound_session(tmp_path)
    session.harness.register_problem(
        Problem(
            id="problem-mini-advisory",
            description="What conclusion is established by this record?",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    formal_before = session.harness.state.model_dump_json()
    commitments_before = dict(session.harness.commitments)
    warrants_before = dict(session.harness.warrants)

    focus = session.scratch.create_block(
        {"content": "A loose provisional idea with no evidential authority."},
        ScratchProvenanceV1(actor="user", origin="mini-forward-fixture"),
    )
    loose = session.scratch.create_block(
        {"content": "A second loose thought retained for exploration."},
        ScratchProvenanceV1(actor="user", origin="mini-forward-fixture"),
    )
    pack = session.plan_attention(
        {
            "focus_blocks": [focus.id],
            "maximum_blocks": 2,
            "maximum_cluster_guides": 0,
            "deterministic_seed": 17,
        }
    )

    assert {block.id for block in pack.blocks} == {focus.id, loose.id}
    assert len(pack.blocks) <= session.manifest.scratch_policy.max_blocks_per_pack
    adapter = _adapter(session)
    terminal = session.build_bridge(
        "problem-mini-advisory",
        "answer",
        stage_a_adapter=adapter,
        attention_pack=pack,
    )

    assert terminal.process_status == "success"
    assert terminal.resolution.value == "insufficient_evidence"
    ledger = session.harness.bridge_state.ledgers[terminal.claim_ledger_id]
    output = session.harness.bridge_state.outputs[terminal.bridge_output_id]
    assert validate_claim_ledger(ledger).valid
    assert validate_bridge_output(ledger, output).valid
    assert len(ledger.entries) == 1
    entry = ledger.entries[0]
    assert entry.claim_class == ClaimClass.UNKNOWN
    assert entry.scratch_refs == [focus.id]
    assert entry.source_refs is entry.evidence_refs is None
    assert output.sections[0].rendering_mode == RenderingMode.UNKNOWN
    assert output.sections[0].ledger_entry_ids == [entry.id]

    ledger_event = next(
        event
        for event in session.harness.log.read()
        if event.bridge is not None
        and event.bridge.action == BridgeAction.LEDGER_CREATED
    )
    assert [attempt.valid for attempt in ledger_event.llm.attempt_trace] == [
        False,
        True,
    ]
    assert session.harness.state.model_dump_json() == formal_before
    assert session.harness.commitments == commitments_before
    assert session.harness.warrants == warrants_before
    assert session.harness.state.artifacts == {}
    assert session.harness.state.att == session.harness.state.dep == []

    tracked = _files(session.root)
    full = Harness(session.root)
    assert full.scratch_state == session.harness.scratch_state
    assert full.bridge_state == session.harness.bridge_state
    assert full.state.model_dump_json() == formal_before
    assert full.objects.get(focus.id)[0] == "scratch-block"
    assert full.objects.get(terminal.claim_ledger_id)[0] == "bridge-claim-ledger"
    assert full.objects.get(terminal.bridge_output_id)[0] == "bridge-output"

    assert cli_main(
        ["--root", str(session.root), "bridge", "result"]
    ) == 0
    rendered = capsys.readouterr().out
    assert "Resolution: Insufficient evidence" in rendered
    assert "[Unknown" in rendered
    assert _files(session.root) == tracked


def test_advisory_facade_rejects_unbound_routes_and_blob_stores(tmp_path):
    session = _bound_session(tmp_path)
    session.harness.register_problem(
        Problem(
            id="problem-route-boundary",
            description="What is established?",
            provenance=ProblemProvenance(trigger="seed"),
        )
    )
    before_seq = session.harness._next_seq
    unbound = LLMAdapter(
        {
            "summarizer": MockEndpoint([], name=_ENDPOINT, model=_MODEL),
            "thesis": MockEndpoint([], name=_ENDPOINT, model=_MODEL),
        },
        session.harness.blobs,
        retry_max=1,
        model_profile="compact",
    )
    with pytest.raises(MiniAdvisoryError, match="MINI_ADVISORY_ROUTE_MISMATCH"):
        session.build_bridge(
            "problem-route-boundary", "answer", stage_a_adapter=unbound
        )

    wrong_repair_bound = _adapter(session)
    wrong_repair_bound.retry_max = 0
    with pytest.raises(
        MiniAdvisoryError, match="MINI_ADVISORY_REPAIR_POLICY_MISMATCH"
    ):
        session.build_bridge(
            "problem-route-boundary",
            "answer",
            stage_a_adapter=wrong_repair_bound,
        )

    wrong_profile = _adapter(session)
    wrong_profile.base_model_profile = "standard"
    with pytest.raises(
        MiniAdvisoryError, match="MINI_ADVISORY_MODEL_PROFILE_MISMATCH"
    ):
        session.build_bridge(
            "problem-route-boundary", "answer", stage_a_adapter=wrong_profile
        )

    missing_composer = _adapter(session)
    del missing_composer.endpoints["thesis"]
    with pytest.raises(MiniAdvisoryError, match="MINI_ADVISORY_ROLE_UNAVAILABLE"):
        session.build_bridge(
            "problem-route-boundary", "answer", stage_a_adapter=missing_composer
        )

    from deepreason.storage.blobs import BlobStore

    wrong_store = _adapter(session, blob_store=BlobStore(tmp_path / "other-blobs"))
    with pytest.raises(
        MiniAdvisoryError, match="MINI_ADVISORY_BLOB_STORE_MISMATCH"
    ):
        session.build_bridge(
            "problem-route-boundary", "answer", stage_a_adapter=wrong_store
        )
    assert session.harness._next_seq == before_seq


def test_v3_feature_policies_are_enforced_at_the_feature_boundary(tmp_path):
    session = _bound_session(tmp_path, scratch=False, grounded=False)

    with pytest.raises(MiniAdvisoryError, match="MINI_ADVISORY_SCRATCH_DISABLED"):
        _ = session.scratch
    with pytest.raises(MiniAdvisoryError, match="MINI_ADVISORY_SCRATCH_DISABLED"):
        session.plan_attention(
            {
                "maximum_blocks": 1,
                "maximum_cluster_guides": 0,
                "deterministic_seed": 1,
            }
        )
    with pytest.raises(MiniAdvisoryError, match="MINI_ADVISORY_BRIDGE_DISABLED"):
        session.build_bridge("missing", "answer", stage_a_adapter=object())


def test_legacy_mini_manifest_remains_v1_and_is_not_migrated(tmp_path):
    root = tmp_path / "legacy-mini"
    kernel = initialize(
        root,
        MockEndpoint([], name="mock://legacy-mini", model="legacy-mini"),
    )
    tracked = _files(root)

    assert kernel.manifest.schema_version == 1
    with pytest.raises(
        MiniAdvisoryError, match="MINI_ADVISORY_MANIFEST_V3_REQUIRED"
    ):
        MiniAdvisorySession.open(root)
    assert _files(root) == tracked
