from __future__ import annotations

from datetime import date
from pathlib import Path

from deepreason.brain import BrainStore, ingest_file, retrieve, snapshot_retrieval
from deepreason.canonical import canonical_json
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.ontology import Interface, Provenance
from deepreason.run_manifest import (
    MANIFEST_NAME,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.skills.adoption import import_capsule
from deepreason.skills.models import SkillCapsule
from deepreason.skills.retrieve import retrieve_skills
from deepreason.skills.snapshot import snapshot_library
from deepreason.workloads.code import WorkspaceSpec, declared_root_digest, snapshot_workspace
from deepreason.workloads.formal import (
    FormalClaim,
    FormalMismatchTest,
    FormalWorkloadSpec,
    FormalizationRelation,
    PinnedLeanRequest,
    register_formal_workflow,
)
from deepreason.workloads.text import seed_reasoning_workload, spec_from_text


def _root(
    tmp_path, name: str, workload: str, manifests: dict[Path, object]
) -> Harness:
    route = {
        "endpoint": "https://example.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        schema_version=2,
        workload_profile=workload,
        compiled_at="2026-07-13T00:00:00Z",
    )
    root = tmp_path / name
    bind_run_manifest(manifest, root)
    manifests[(root / MANIFEST_NAME).resolve()] = manifest
    return Harness(root)


def _capsule() -> SkillCapsule:
    return SkillCapsule.create(
        problem_signature="bounded partitions",
        accepted_source_structure=("split at a stable boundary",),
        overturn_conditions=("a valid case crosses the boundary",),
        source_artifact_id="accepted-source",
        source_event_seq=1,
        source_snapshot_digest="1" * 64,
        source_config_provenance=("run-manifest:none",),
        distiller_version="test-v1",
    )


def test_verify_root_is_clean_for_text_code_formal_skills_and_brain(
    tmp_path, monkeypatch
) -> None:
    import deepreason.invariants as invariants_module
    import deepreason.run_manifest as run_manifest_module

    manifests: dict[Path, object] = {}
    public_loader = run_manifest_module.load_run_manifest
    invariant_loader = invariants_module.load_run_manifest

    def load_for_internal_harness(path, *args, **kwargs):
        target = Path(path).resolve()
        if target in manifests:
            return manifests[target]
        return public_loader(path, *args, **kwargs)

    def load_for_invariants(path, *args, **kwargs):
        target = Path(path).resolve()
        if target in manifests:
            return manifests[target]
        return invariant_loader(path, *args, **kwargs)

    monkeypatch.setattr(
        run_manifest_module, "load_run_manifest", load_for_internal_harness
    )
    monkeypatch.setattr(
        invariants_module, "load_run_manifest", load_for_invariants
    )
    roots: dict[str, Harness] = {}

    text = _root(tmp_path, "text", "text", manifests)
    seed_reasoning_workload(text, spec_from_text("Why can feedback oscillate?"))
    roots["text"] = text

    source = tmp_path / "code-source"
    source.mkdir()
    (source / "main.py").write_text("value = 1\n")
    spec = WorkspaceSpec(
        root=str(source.resolve()),
        root_digest=declared_root_digest(source, ("*.py",)),
        allowed_paths=("*.py",),
    )
    code = _root(tmp_path, "code", "code", manifests)
    snapshot = snapshot_workspace(spec, blobs=code.blobs)
    code.create_artifact(
        canonical_json(snapshot.model_dump(mode="json", by_alias=True)),
        codec="json",
        interface=Interface(),
        provenance=Provenance(role="import"),
    )
    roots["code"] = code

    formal = _root(tmp_path, "formal", "formal", manifests)
    statement = "The empty list has length zero."
    source_ref = formal.blobs.put(
        b"theorem empty_length : [].length = 0 := by rfl\n"
    )
    register_formal_workflow(
        formal,
        FormalWorkloadSpec(
            claim=FormalClaim(statement=statement),
            request=PinnedLeanRequest(
                toolchain_id="lean4@4.19.0",
                source_ref=source_ref,
                target_theorems=["empty_length"],
            ),
            relation=FormalizationRelation(
                informal_target=statement,
                theorem="empty_length",
                scope="Lean lists",
                counterconditions=("a nonstandard length is intended",),
                mismatch_tests=(
                    FormalMismatchTest(
                        id="custom-length",
                        case="replace List.length",
                        expected_informal="outside scope",
                        expected_formal="not represented",
                    ),
                ),
            ),
            explicit_formal_dependence=True,
        ),
    )
    roots["formal"] = formal

    skills = _root(tmp_path, "skills", "text", manifests)
    capsule = _capsule()
    import_capsule(skills, capsule)
    library = snapshot_library((capsule,), skills.blobs, library_id="test-skills")
    retrieve_skills(
        library,
        "bounded partition",
        ("school-a", "school-blind"),
        skills.blobs,
        problem_id="partition",
        harness=skills,
    )
    roots["skills"] = skills

    brain_run = _root(tmp_path, "brain-run", "text", manifests)
    external = BrainStore.init(tmp_path / "brain")
    note = tmp_path / "memory.txt"
    note.write_text("bounded partition coverage")
    ingest_file(external, note)
    retrieval = retrieve(
        external,
        "partition coverage",
        query_day=date(2026, 7, 13),
        record_access=False,
    )
    brain_snapshot = snapshot_retrieval(external, retrieval, brain_run.blobs)
    brain_run.record_measure(inputs=["brain-snapshot", brain_snapshot.receipt_ref])
    roots["brain"] = brain_run

    reports = {name: verify_root(harness.root) for name, harness in roots.items()}
    assert {name: report["violations"] for name, report in reports.items()} == {
        "text": [],
        "code": [],
        "formal": [],
        "skills": [],
        "brain": [],
    }
