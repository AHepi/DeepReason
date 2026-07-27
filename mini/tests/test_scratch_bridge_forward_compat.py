"""C12: MiniReason reuses the canonical scratch and bridge protocol.

The advisory session is a delegation-only facade over one bound v6 mini
manifest that enables the scratchpad and the grounded two-stage bridge.  The
forward-compat guarantees pinned here are protocol-level: scratch references
stay provenance-not-evidence, attention/similarity stays retrieval-only, an
unknown/partial bridge resolution is a valid success, and legacy pre-v6 mini
roots fail closed in the parent loader without migration.
"""

from __future__ import annotations

import json

import pytest

from deepreason.bridge import BridgeAction, ClaimClass, RenderingMode
from deepreason.bridge.validate import validate_bridge_output, validate_claim_ledger
from deepreason.cli.main import main as cli_main
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import MANIFEST_NAME, RunManifestError
from deepreason.scratch.models import ScratchProvenanceV1
from minireason.advisory import (
    MiniAdvisoryError,
    MiniAdvisorySession,
    bind_mini_advisory_root,
)
from minireason.compat import bind_mini_root


_ENDPOINT = "mock://mini-advisory"
_MODEL = "mini-scripted"


def _endpoint(responses=()) -> MockEndpoint:
    return MockEndpoint(list(responses), name=_ENDPOINT, model=_MODEL)


def _bound_session(tmp_path) -> MiniAdvisorySession:
    root = tmp_path / "mini-v6-run"
    root.mkdir()
    bind_mini_advisory_root(root, _endpoint())
    return MiniAdvisorySession.open(root)


def _adapter(session: MiniAdvisorySession, *, blob_store=None) -> LLMAdapter:
    # The manifest's V3 control plane selects the namespaced v2/v3 stage-A
    # wire dialect: catalog scratch items are SCR_* handles and entry keys are
    # CLM_*.  Scratch remains provenance-only in every dialect, so the first
    # scripted attempt (a "fact" grounded only in scratch) must fail wire
    # validation and be repaired into an honest unknown.
    scratch_fact = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "CLM_1",
                    "claim_class": "source_fact",
                    "claim": "The scratch idea is an established fact.",
                    "scratch_handles": ["SCR_1"],
                }
            ]
        }
    )
    safe_unknown = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "CLM_1",
                    "claim_class": "unknown",
                    "claim": "The requested conclusion is not established.",
                    "scratch_handles": ["SCR_1"],
                }
            ],
            "uncovered_requirements": [
                {
                    "requirement": "Grounded evidence for the requested conclusion.",
                    "reason": "Scratch provenance is advisory, not evidence.",
                    "scratch_handles": ["SCR_1"],
                }
            ],
        }
    )
    # The v2 composition dialect never lets the model author rendering_mode;
    # the compiler derives the weakest mode from the referenced ledger entry.
    unresolved_output = json.dumps(
        {
            "sections": [
                {
                    "span_id": "S1",
                    "text": "The requested conclusion remains unknown.",
                    "ledger_entry_handles": ["E1"],
                }
            ],
            "resolution": "insufficient_evidence",
            "resolution_reason": "The bounded record supplies no grounding.",
        }
    )
    return LLMAdapter(
        {
            "summarizer": _endpoint([scratch_fact, safe_unknown]),
            "thesis": _endpoint([unresolved_output]),
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


def test_mini_v6_scratch_bridge_replays_in_full_harness_without_migration(
    tmp_path, capsys
):
    session = _bound_session(tmp_path)
    assert session.manifest.schema_version == 6
    assert session.manifest.engine_profile == "mini"
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
            "summarizer": MockEndpoint([], name="mock://elsewhere", model="other"),
            "thesis": MockEndpoint([], name="mock://elsewhere", model="other"),
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


def test_feature_policies_are_enforced_at_the_feature_boundary(tmp_path):
    """The phase-1 default mini manifest keeps scratch and bridge switched off."""

    root = tmp_path / "mini-v6-default"
    manifest = bind_mini_root(root, _endpoint())
    assert manifest.scratch_policy is not None
    assert not manifest.scratch_policy.enabled
    assert manifest.bridge_policy is not None
    assert manifest.bridge_policy.mode != "grounded_two_stage"
    session = MiniAdvisorySession.open(root)

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

    # The advisory binder never upgrades an existing default root in place.
    tracked = _files(root)
    with pytest.raises(MiniAdvisoryError, match="MINI_ADVISORY_SCRATCH_DISABLED"):
        bind_mini_advisory_root(root, _endpoint())
    assert _files(root) == tracked


def test_legacy_pre_v6_advisory_root_fails_closed_without_migration(tmp_path):
    """A historical v3 advisory root is rejected by the loader, not adapted."""

    root = tmp_path / "legacy-mini"
    root.mkdir()
    (root / MANIFEST_NAME).write_text(
        json.dumps(
            {
                "schema_version": 3,
                "engine_profile": "mini",
                "roles": {"summarizer": [], "thesis": []},
            }
        ),
        encoding="utf-8",
    )
    tracked = _files(root)

    with pytest.raises(RunManifestError) as raised:
        MiniAdvisorySession.open(root)
    assert raised.value.code == "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert not isinstance(raised.value, MiniAdvisoryError)

    with pytest.raises(RunManifestError) as rebound:
        bind_mini_advisory_root(root, _endpoint())
    assert rebound.value.code == "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert _files(root) == tracked
