import pytest

from deepreason.llm.embedder import HashingEmbedder
from deepreason.skills.models import SkillCapsule
from deepreason.skills.retrieve import render_school_slice, replay_retrieval, retrieve_skills
from deepreason.skills.revoice import RevoiceOverlapError, revoice_capsule
from deepreason.skills.snapshot import snapshot_library
from deepreason.storage.blobs import BlobStore


def _capsule(index):
    return SkillCapsule.create(
        problem_signature=f"problem family {index}",
        accepted_source_structure=(f"construct bounded partition number {index}",),
        scope=(f"scope {index}",),
        source_owned_counterconditions=(f"boundary check {index}",),
        passed_commitments=(),
        toolchains=(),
        dependency_topology=(),
        unresolved_conditions=(f"unresolved {index}",),
        overturn_conditions=(f"counterexample outside partition {index}",),
        source_artifact_id=f"a-{index}",
        source_event_seq=index,
        source_snapshot_digest=f"{index + 1:064x}",
        source_config_provenance=("run-manifest:none",),
        distiller_version="v1",
    )


def test_snapshot_retrieval_receipt_blind_school_and_replay(tmp_path):
    blobs = BlobStore(tmp_path / "run-blobs")
    snapshot = snapshot_library((_capsule(i) for i in range(8)), blobs, library_id="skills")
    receipt = retrieve_skills(
        snapshot,
        "bounded partition boundary",
        ("school-c", "school-a", "school-b"),
        blobs,
        problem_id="pi-partition",
        top_k=8,
        per_school=3,
        embedder=HashingEmbedder(32),
        summarizer=lambda text: "Try a bounded split, then test coverage and named limits.",
        summarizer_version="summary-v1",
    )
    assert len([item for item in receipt.school_slices if item.blind]) == 1
    active = [set(item.capsule_ids) for item in receipt.school_slices if not item.blind]
    assert active[0].isdisjoint(active[1])
    assert replay_retrieval(receipt, blobs)
    blind = next(item for item in receipt.school_slices if item.blind)
    assert render_school_slice(receipt, blind.school_id, blobs) == ""
    visible = next(item for item in receipt.school_slices if not item.blind)
    assert "advisory only" in render_school_slice(receipt, visible.school_id, blobs)
    assert any(item.item_id == "query" for item in receipt.raw_embeddings)


def test_revoice_overlap_guard_blocks_generator_voice_reentry(tmp_path):
    blobs = BlobStore(tmp_path / "blobs")
    capsule = _capsule(2)
    with pytest.raises(RevoiceOverlapError):
        revoice_capsule(
            capsule,
            lambda source: source,
            blobs,
            summarizer_version="copy-v1",
        )
