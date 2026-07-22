from __future__ import annotations

import json

from deepreason.cli.main import main
from deepreason.harness import Harness
from deepreason.ontology import Commitment, Interface, Provenance
from deepreason.skills.models import SkillCapsule


def _capsule() -> SkillCapsule:
    return SkillCapsule.create(
        problem_signature="bounded partition",
        accepted_source_structure=("split at a stable boundary",),
        scope=("finite cases",),
        source_owned_counterconditions=("coverage remains exhaustive",),
        unresolved_conditions=(),
        overturn_conditions=("one valid input belongs to no partition",),
        source_artifact_id="source-a",
        source_event_seq=1,
        source_snapshot_digest="1" * 64,
        source_config_provenance=("run-manifest:none",),
        distiller_version="test-v1",
    )


def test_brain_cli_explicit_lifecycle(tmp_path, capsys) -> None:
    brain = tmp_path / "brain"
    source = tmp_path / "note.txt"
    source.write_text("bounded partition boundary coverage")
    assert main(["brain", "init", str(brain)]) == 0
    capsys.readouterr()
    assert main(["brain", "ingest", str(brain), str(source)]) == 0
    record_id = json.loads(capsys.readouterr().out)["record_ids"][0]
    assert main(["brain", "query", str(brain), "partition", "--day", "2026-01-01"]) == 0
    assert "deepreason-brain-retrieval-v1" in capsys.readouterr().out
    assert main(["brain", "pin", str(brain), record_id, "--floor", "1.5"]) == 0
    assert main(["brain", "reinforce", str(brain), record_id]) == 0
    assert main(["brain", "unpin", str(brain), record_id]) == 0
    assert main(["brain", "inspect", str(brain), record_id]) == 0
    assert main(["brain", "reindex", str(brain)]) == 0


def test_skills_cli_snapshots_and_emits_receipt(tmp_path, capsys) -> None:
    from tests.test_v6_only_cli_admission import _prepared_v6_root

    capsule_path = tmp_path / "capsule.json"
    capsule_path.write_text(_capsule().model_dump_json(by_alias=True))
    prepared = _prepared_v6_root(tmp_path / "run")
    assert main(
        [
            "--root",
            str(prepared.root),
            "skills",
            "--capsule",
            str(capsule_path),
            "--query",
            "partition coverage",
            "--school",
            "alpha",
            "--school",
            "blind",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "deepreason-skill-retrieval-v1"
    assert len([item for item in payload["school_slices"] if item["blind"]]) == 1


def test_distill_cli_requires_verified_accepted_source(tmp_path, capsys) -> None:
    from tests.test_v6_only_cli_admission import _prepared_v6_root

    prepared = _prepared_v6_root(tmp_path / "source-run")
    source = Harness(prepared.root)
    commitment = Commitment(id="k", eval="predicate:'stable' in content")
    source.register_commitment(commitment)
    accepted = source.create_artifact(
        "stable constructive partition",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer"),
    )
    draft = tmp_path / "draft.json"
    draft.write_text(
        json.dumps(
            {
                "problem_signature": "partition",
                "accepted_source_structure": ["split at a stable boundary"],
                "overturn_conditions": ["coverage counterexample"],
            }
        )
    )
    target = tmp_path / "capsule.json"
    assert main(
        [
            "distill",
            "--source",
            str(source.root),
            "--seq",
            str(source._next_seq - 1),
            "--artifact",
            accepted.id,
            "--draft",
            str(draft),
            "--out",
            str(target),
        ]
    ) == 0
    assert SkillCapsule.model_validate_json(target.read_bytes()).source_artifact_id == accepted.id
    assert "wrote" in capsys.readouterr().out

    brain = tmp_path / "brain"
    lesson = tmp_path / "lesson.json"
    lesson.write_text(
        json.dumps(
            {
                "claim": "A stable boundary can simplify a finite partition.",
                "conditions": ["the cases are enumerable"],
                "procedure": ["name the boundary", "check every case"],
                "checks": ["look for an uncovered case"],
                "limits": ["does not cover open-ended domains"],
                "overturn_conditions": ["a case crosses the boundary"],
                "source_refs": [accepted.id],
            }
        )
    )
    assert main(["brain", "init", str(brain)]) == 0
    capsys.readouterr()
    assert main(
        [
            "brain",
            "distill-run",
            str(brain),
            "--source",
            str(source.root),
            "--seq",
            str(source._next_seq - 1),
            "--artifact",
            accepted.id,
            "--lesson",
            str(lesson),
        ]
    ) == 0
    record_id = json.loads(capsys.readouterr().out)["record_id"]
    assert main(["brain", "inspect", str(brain), record_id]) == 0
