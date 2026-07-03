"""P5 acceptance (a)+(b) (spec §16): a forbid-nothing conjecture fails
skeleton-wf and is refuted by program; a Persephone-style skeleton fails
hv-floor under mu_struct with the substitution trace logged."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.informal.skeleton import (
    compile_forbidden_commitments,
    parse_skeleton,
    skeleton_wf_commitment,
)
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.measures.hv import hv_floor_commitment, run_hv_floor
from deepreason.ontology import Interface, Provenance, Status
from deepreason.programs import FAIL
from deepreason.rules.crit import crit_program
from deepreason.views.prose import prose


def _skeleton(claim, mechanism, forbidden_cases) -> str:
    return json.dumps(
        {
            "claim": claim,
            "mechanism": mechanism,
            "scope": {"covers": ["the target domain"], "excludes": []},
            "forbidden": [
                {"case": c, "eval": "rubric:std-1"} for c in forbidden_cases
            ],
        },
        sort_keys=True,
    )


def test_forbid_nothing_fails_skeleton_wf_refuted_by_program(harness):
    harness.register_commitment(skeleton_wf_commitment())
    vacuous = harness.create_artifact(
        _skeleton("winter happens", "the gods decree it", forbidden_cases=[]),
        codec="json",
        interface=Interface(commitments=["skeleton-wf"]),
        provenance=Provenance(role="conjecturer"),
    )
    crit_program(harness, vacuous.id)
    assert harness.state.status[vacuous.id] == Status.REFUTED
    warrant = next(w for w in harness.warrants.values() if w.target == vacuous.id)
    assert warrant.commitment == "skeleton-wf"
    trace = json.loads(harness.blobs.get(warrant.trace_ref))
    assert "forbids nothing" in trace["error"]


def test_forbidden_cases_compile_to_commitments(harness):
    skeleton = parse_skeleton(
        _skeleton("tides follow the moon", "differential gravity",
                  ["a tide with no lunar correlation", "a second daily bulge absent"])
    )
    ids = compile_forbidden_commitments(harness, skeleton)
    assert len(ids) == 2 and all(i.startswith("fc:") for i in ids)
    # Case text rides with the commitment for trial packs (§10.1).
    assert harness.commitments[ids[0]].budget.extra["case"]
    # Deterministic: recompiling yields the same ids.
    assert compile_forbidden_commitments(harness, skeleton) == ids


def test_persephone_skeleton_fails_hv_floor_under_mu_struct(tmp_path):
    """Any god and any crime slot in and the account still passes =>
    survivors abound => low HV (the Persephone test, §6/§10.7)."""
    root = tmp_path / "run"
    harness = Harness(root)
    config = Config(HV_K=3, HV_MIN=0.5)
    harness.register_commitment(skeleton_wf_commitment())
    floor = hv_floor_commitment(config)
    harness.register_commitment(floor)
    persephone = harness.create_artifact(
        _skeleton("winter happens", "Persephone must return to Hades",
                  ["winter fails to arrive at the appointed time"]),
        codec="json",
        interface=Interface(commitments=["skeleton-wf", floor.id]),
        provenance=Provenance(role="conjecturer"),
    )
    # mu_struct substitutions: swap the god, the crime, the mechanism —
    # every edit is still a valid forbidding skeleton, so all survive.
    edits = [
        _skeleton("winter happens", "Demeter mourns her daughter",
                  ["winter fails to arrive at the appointed time"]),
        _skeleton("winter happens", "Apollo withdraws his chariot",
                  ["winter fails to arrive at the appointed time"]),
        _skeleton("winter happens", "Loki's punishment chills the earth",
                  ["winter fails to arrive at the appointed time"]),
    ]
    adapter = LLMAdapter(
        {"variator": MockEndpoint([json.dumps({"edits": [{"content": e} for e in edits]})])},
        harness.blobs,
        retry_max=2,
    )
    verdict = run_hv_floor(harness, adapter, persephone.id, floor)
    assert verdict == FAIL
    assert harness.state.status[persephone.id] == Status.REFUTED
    # Substitution trace logged with the structural kernel tag.
    warrant = next(w for w in harness.warrants.values() if w.target == persephone.id)
    trace = json.loads(harness.blobs.get(warrant.trace_ref))
    assert trace["kernel"] == "mu_struct"
    assert len(trace["per_edit"]) == 3
    assert all(e["inequivalent"] for e in trace["per_edit"])
    # The variator was instructed to substitute at role level.
    prompt = harness.blobs.get(
        next(e.llm.prompt_ref for e in harness.log.read() if e.llm and e.llm.role == "variator")
    ).decode()
    assert "mu_struct" in prompt
    # Byte-for-byte replay.
    assert Harness(root).state.model_dump_json() == harness.state.model_dump_json()


def test_prose_is_a_view_not_the_content(harness):
    artifact = harness.create_artifact(
        _skeleton("tides follow the moon", "differential gravity",
                  ["a tide with no lunar correlation"]),
        codec="json",
        provenance=Provenance(role="conjecturer"),
    )
    rendered = prose(artifact.id, harness.state, harness.blobs)
    assert "tides follow the moon" in rendered
    assert "This account fails if" in rendered
