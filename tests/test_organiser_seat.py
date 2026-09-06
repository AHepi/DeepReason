"""The organiser seat: a writer's room carried onto the full harness.

Implements S12 (R12) of experiments/2026-09-06-change-writers-room-organiser-
testing/: the organiser is a REGISTERED PAIRING -- the conjecturer's seat, a
brief that shows the room as frozen evidence and asks it to organise rather
than invent, and the form the managed conjecturer already fills -- and this
file proves, against the record and never a local variable, that

  * its candidates admit through the ORDINARY path, with no code path named
    "organiser" on the way in (assertions a, b);
  * their counterconditions become the commitments the artifact carries (b);
  * a citation to a block the pack did not show, or to no block at all, is a
    TYPED MEASURE on the record and never a status -- the record, not the
    seat, catches invention (c, d);
  * the brief is the organiser's, and unbinding the shell restores the legacy
    brief byte for byte (e, f, and the mutation companion);
  * the critic beside it reads no evidence (S14), and the wording template
    moves the conjecturer's prose alone (A11).

The room is the committed attachment the tranche's converter wrote from the
live room root `shallow-0b47bc7b090854078ddf7559` (12 conjectures, 46
proposals, 36 objections), read from the tranche directory and pinned here
by sha256 so the bytes a live arm would bind are the bytes this file proves. Offline throughout: a mock
endpoint, no key.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from deepreason.llm.role_prompts import ROLE_PROMPT_TEMPLATE_ENV
from deepreason.llm.seat_sections import SEAT_SHELL_ENV

# The committed attachment itself, not a copy: `git ls-files` knows it, the
# sha256 pins below hold it to the bytes the converter wrote, and a second
# copy under tests/ would be 365 lines of data the diff-budget gate counts
# as code (CHECKLIST step 7).
FIXTURES = (
    pathlib.Path(__file__).resolve().parents[1]
    / "experiments"
    / "2026-09-06-change-writers-room-organiser-testing"
    / "attachment"
)
PINNED = {
    "01-conjectures.txt": "feb1dc480421d1cdb26260223a82ea82d88d9e14ff761ad63ec9662acd4088bb",
    "02-proposals.txt": "cf7a4a2edcc19307e7be923623676cd7db80f8722d58f584fda30fad65062452",
    "03-objections.txt": "87163fb464c30da6e06e4daf475245637aad04de8a7f92d6e482b1cb734e0ded",
}
ORGANISER_SHELL = "seat.conjecturer.organiser-v1"
BLIND_CRITIC_SHELL = "seat.critic.evidence-blind-v1"
ORGANISER_WORDING = "role-prompt.organiser-v1"
QUESTION = (
    "Popper held that corroboration is not probability. Is the preference for "
    "the better-corroborated theory defensible on Popper's own terms?"
)
# The managed attached-evidence envelope, byte for byte
# (src/deepreason/v6_policy.py::engaged_attached_evidence_policy).
MANAGED_POLICY = dict(
    enabled=True,
    maximum_sources=16,
    maximum_total_bytes=8 * 1024 * 1024,
    maximum_excerpt_bytes_per_source=262_144,
    maximum_sources_per_pack=8,
)


@pytest.fixture(autouse=True)
def seeded():
    from deepreason.llm.seat_plugins import ensure_seeded

    ensure_seeded()


def _files() -> list[tuple[str, bytes]]:
    return [(name, (FIXTURES / name).read_bytes()) for name in sorted(PINNED)]


def _config():
    from deepreason.config import Config

    config = Config(
        roles={
            "conjecturer": {
                "endpoint_id": "offline-organiser",
                "endpoint": "mock://offline-organiser",
                "model": "offline-model",
                "provider": "mock",
                "family": "offline",
                "max_tokens": 4096,
                "context_window_tokens": 262_144,
            }
        }
    )
    # The tranche's launch config (runs/config.yaml): the room is ~53 000
    # characters and both evidence sections are exact in the organiser layout.
    config.PACK_TOKEN_BUDGET = 24_000
    return config


def _room_root(tmp_path):
    """A v6 root with the room bound as its dossier and one seed problem."""

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
    from deepreason.ontology import Commitment, Problem
    from deepreason.ontology.commitment import Budget
    from deepreason.ontology.problem import ProblemProvenance
    from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
    from deepreason.storage.blobs import BlobStore

    from tests.test_amendment_epochs import STAMP, _problem_id
    from tests.test_run_input_v6_commitments import (
        _commitment,
        _control,
        _write_qualification,
    )

    root = tmp_path / "organiser-root"
    commitment = _commitment()
    seed_id = _problem_id(QUESTION)
    dossier, report = admit_sources(
        [AdmissionInput(locator=name, data=data) for name, data in _files()],
        problem_ref=seed_id,
        provenance=AttachedSourceProvenanceV1(
            supplied_by="organiser fixture", acquisition_method="offline construction"
        ),
    )
    assert report.refusals == [], report.refusals
    store = BlobStore(root / "blobs")
    for _name, data in _files():
        store.put(data)
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=seed_id, description=QUESTION, criteria=(commitment,)
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
            attached_evidence=AttachedEvidencePolicyV1(**MANAGED_POLICY),
        ),
        run_input_digest=run_input.run_input_digest,
    )
    bind_run_manifest(manifest, root)
    _write_qualification(root, manifest)
    harness = Harness(root)
    harness.register_commitment(commitment)
    # Every public text run seeds this criterion (`workloads/text.py::
    # seed_reasoning_workload`); it is what makes the conjecturer's turn the
    # REASONING form -- claim, mechanism, counterconditions -- rather than
    # the plain-content one. Seeded here the same way, so the stub fills the
    # form a live arm fills.
    wf = Commitment(
        id="reasoning-envelope-wf",
        eval="program:reasoning-envelope-wf",
        budget=Budget(steps=10_000, time_ms=2_000, extra={"max_chars": 64_000}),
    )
    harness.register_commitment(wf)
    harness.register_problem(
        Problem(
            id=seed_id,
            description=QUESTION,
            criteria=[wf.id, commitment.id],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    return harness, manifest, config, dossier, seed_id


def _bind_organiser(monkeypatch):
    monkeypatch.setenv(
        SEAT_SHELL_ENV,
        f"conjecturer={ORGANISER_SHELL},argumentative_critic={BLIND_CRITIC_SHELL}",
    )
    monkeypatch.setenv(ROLE_PROMPT_TEMPLATE_ENV, ORGANISER_WORDING)


def _blocks_of(dossier, name: str) -> list:
    digest = hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()
    return [block for block in dossier.blocks if block.source_sha256 == digest]


def _dispatch(harness, manifest, config, seed_id, response):
    from tests.test_p4_citable_evidence import _conjecture_on

    return _conjecture_on(harness, manifest, config, seed_id, response)


def _candidate(claim, mechanism, counterconditions, refs):
    return {
        "claim": claim,
        "mechanism": mechanism,
        "counterconditions": list(counterconditions),
        "typicality": 0.5,
        "evidence_refs": [{"block": ref} for ref in refs],
    }


def _citation_measures(harness) -> list[tuple[str, str]]:
    return [
        (event.inputs[0].split(":", 1)[1], event.inputs[1])
        for event in harness.log.read()
        if event.rule.value == "Measure"
        and event.inputs
        and event.inputs[0].startswith("evidence-citation:")
    ]


def _artifact_ids(registered) -> list[str]:
    return [item if isinstance(item, str) else item.id for item in registered]


# --- the fixture is the attachment ------------------------------------------


def test_the_fixture_is_the_committed_attachment_byte_for_byte():
    for name, digest in PINNED.items():
        assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == digest, name


def test_admission_mints_one_block_per_room_record():
    """S3's whole design: a record is a paragraph is a block."""
    from deepreason.admission.parse import AdmissionInput, admit_sources
    from deepreason.evidence import AttachedSourceProvenanceV1

    dossier, report = admit_sources(
        [AdmissionInput(locator=name, data=data) for name, data in _files()],
        problem_ref="question-x",
        provenance=AttachedSourceProvenanceV1(
            supplied_by="organiser fixture", acquisition_method="offline construction"
        ),
    )
    assert report.refusals == []
    assert len(_blocks_of(dossier, "01-conjectures.txt")) == 12
    assert len(_blocks_of(dossier, "02-proposals.txt")) == 46
    assert len(_blocks_of(dossier, "03-objections.txt")) == 36
    assert all(block.kind == "paragraph" and block.tier == "evidence" for block in dossier.blocks)


# --- the brief (e, f) ------------------------------------------------------------


def test_the_organiser_brief_shows_the_whole_room_and_the_directive(tmp_path, monkeypatch):
    from tests.test_p4_citable_evidence import _abstain

    _bind_organiser(monkeypatch)
    harness, manifest, config, dossier, seed_id = _room_root(tmp_path)
    prompts, _registered = _dispatch(harness, manifest, config, seed_id, _abstain())
    (prompt,) = prompts

    # The wording and the directive are the organiser's; the legacy ones are gone.
    assert prompt.startswith("You are the organiser seat")
    assert "DIRECTIVE: ORGANISE, DO NOT INVENT." in prompt
    assert "refuted if not" in prompt and "uncertainties" in prompt and "0.5" in prompt
    assert "COMPLEMENT DIRECTIVE" not in prompt
    assert "DIVERSITY SPECIFICATIONS" not in prompt
    assert "Include atypical candidates" not in prompt
    assert "conjecture operator (gamma)" not in prompt

    # All three sources' bodies are in the frozen-evidence section, uncut.
    assert prompt.count("BEGIN UNTRUSTED SOURCE DATA") == 3
    assert "excluded_source_ids" not in prompt
    for name, data in _files():
        body = data.decode("utf-8")
        assert body.strip() in prompt, f"{name} was not rendered whole"

    # The legend shows the first 32 blocks of the dossier -- and the dossier
    # sorts its blocks by CONTENT ID (`admission/parse.py`, `sorted(blocks,
    # key=lambda block: block.id)`), not by file or by record order. So the
    # citable 32 are a hash-ordered sample of the 94, measured here on the
    # pinned bytes: 7 conjectures, 13 proposals, 12 objections. SPEC A3
    # assumed file order and was wrong; SPEC Amendment 1 records it, and
    # PARKED P2 carries both the cap and the order.
    assert "CITABLE EVIDENCE BLOCKS" in prompt
    shown = [b for b in dossier.blocks if f"[{b.id[:16]}]" in prompt]
    assert [b.id for b in shown] == [b.id for b in dossier.blocks[:32]]
    assert dossier.blocks == tuple(sorted(dossier.blocks, key=lambda b: b.id))
    by_file = {
        name: sum(1 for b in shown if b in _blocks_of(dossier, name)) for name in PINNED
    }
    assert by_file == {
        "01-conjectures.txt": 7, "02-proposals.txt": 13, "03-objections.txt": 12
    }, by_file
    assert "(+62 further citable blocks not shown)" in prompt


def test_unbound_the_seat_renders_the_legacy_brief(tmp_path, monkeypatch):
    """The mutation companion: the organiser is configuration, not a default."""
    from tests.test_p4_citable_evidence import _abstain

    monkeypatch.delenv(SEAT_SHELL_ENV, raising=False)
    monkeypatch.delenv(ROLE_PROMPT_TEMPLATE_ENV, raising=False)
    harness, manifest, config, _dossier, seed_id = _room_root(tmp_path)
    prompts, _registered = _dispatch(harness, manifest, config, seed_id, _abstain())
    (prompt,) = prompts
    assert prompt.startswith("You are the conjecture operator (gamma)")
    assert "diverse candidates with typicality" in prompt
    assert "ORGANISE, DO NOT INVENT" not in prompt


# --- admission, commitments, citations (a, b, c, d) ------------------------------


def _shown_and_hidden(dossier):
    """What the legend shows (its first 32 blocks, id order) and what it
    withholds, split by kind -- computed from the dossier, never assumed."""
    shown, hidden = dossier.blocks[:32], dossier.blocks[32:]
    conj = set(b.id for b in _blocks_of(dossier, "01-conjectures.txt"))
    prop = set(b.id for b in _blocks_of(dossier, "02-proposals.txt"))
    pick = lambda pool, ids: [b for b in pool if b.id in ids]  # noqa: E731
    return {
        "conjectures_shown": pick(shown, conj),
        "proposals_shown": pick(shown, prop),
        "hidden": list(hidden),
    }


def _organised_pair(dossier):
    """Two organiser candidates.

    The first cites a conjecture block and a proposal block the legend SHOWS.
    The second cites a shown conjecture block AND a block the legend withheld
    (the 33rd block onward) -- exactly what a seat that read the frozen
    section, where every body is rendered whole, and cited from it would do.
    """
    parts = _shown_and_hidden(dossier)
    conjectures = parts["conjectures_shown"]
    proposals = parts["proposals_shown"]
    objections = parts["hidden"]
    assert len(conjectures) >= 2 and proposals and objections
    first = _candidate(
        "The preference is a pragmatic wager, not an epistemic probability claim.",
        "Choosing the theory that survived the severest tests is the only "
        "rational choice for an agent who must act, and it asserts nothing "
        "about the next instance.",
        [
            "The conjecture is refuted if preferring the better-corroborated "
            "theory logically entails an assumption that the future will "
            "resemble the past.",
            "The conjecture is refuted if any increased likelihood of future "
            "success is attributed to a theory solely on the basis of its "
            "survival of past tests.",
        ],
        [conjectures[0].id, proposals[0].id],
    )
    second = _candidate(
        "Verisimilitude is a regulative ideal: a corroborated theory is a "
        "better candidate for truth-likeness, not a more probable one.",
        "Selecting the highest-content unrefuted theory is the only move "
        "consistent with aiming at truth rather than certainty.",
        [
            "The conjecture is refuted if verisimilitude cannot be defined "
            "without implicitly relying on inductive probability.",
        ],
        [conjectures[1].id, objections[0].id],
    )
    return first, second, conjectures, proposals, objections


def test_organised_candidates_admit_through_the_ordinary_path_and_carry_their_commitments(
    tmp_path, monkeypatch
):
    _bind_organiser(monkeypatch)
    harness, manifest, config, dossier, seed_id = _room_root(tmp_path)
    first, second, *_ = _organised_pair(dossier)
    _prompts, registered = _dispatch(
        harness, manifest, config, seed_id, {"candidates": [first, second]}
    )
    ids = _artifact_ids(registered)
    assert len(ids) == 2, registered
    from deepreason.ontology import Status

    for artifact_id, candidate in zip(ids, (first, second)):
        artifact = harness.state.artifacts[artifact_id]
        assert artifact.provenance.role.value == "conjecturer"
        assert harness.state.status[artifact_id] == Status.ACCEPTED
        # (b) every countercondition is a commitment the artifact carries, in
        # the shape draft_countercondition_commitments mints, registered on
        # admission and nowhere before it.
        counters = [c for c in artifact.interface.commitments if c.startswith("reason-counter@")]
        assert len(counters) == len(candidate["counterconditions"]), artifact.interface.commitments
        for commitment_id in counters:
            registered_commitment = harness.commitments[commitment_id]
            assert registered_commitment.eval == "program:reasoning_observation_pending"
            assert registered_commitment.observation_valued is True
        # The envelope the record holds is the candidate's, condensed by nothing.
        envelope = json.loads(artifact.content_ref.removeprefix("inline:"))
        assert envelope["claim"] == candidate["claim"]
        assert [c["case"] for c in envelope["counterconditions"]] == candidate["counterconditions"]


def test_a_citation_outside_the_legend_is_a_typed_measure_and_never_a_status(
    tmp_path, monkeypatch
):
    """(c) The record, not the seat, catches invention: the second candidate's
    withheld block is a real block whose body the frozen section rendered but
    the legend did not SHOW, so its citation is `EVIDENCE_REF_NOT_EXPOSED` --
    recorded, attackable, and no status moves."""
    _bind_organiser(monkeypatch)
    harness, manifest, config, dossier, seed_id = _room_root(tmp_path)
    first, second, conjectures, proposals, objections = _organised_pair(dossier)
    _prompts, registered = _dispatch(
        harness, manifest, config, seed_id, {"candidates": [first, second]}
    )
    measures = _citation_measures(harness)
    verified = {block for code, block in measures if code == "EVIDENCE_CITATION_VERIFIED"}
    not_exposed = {block for code, block in measures if code == "EVIDENCE_REF_NOT_EXPOSED"}
    assert verified == {conjectures[0].id, proposals[0].id, conjectures[1].id}, measures
    assert not_exposed == {objections[0].id}, measures
    assert objections[0].id not in {b.id for b in dossier.blocks[:32]}
    from deepreason.ontology import Status

    assert all(harness.state.status[a] == Status.ACCEPTED for a in _artifact_ids(registered))


def test_an_id_that_names_no_block_is_refused_by_the_record(tmp_path, monkeypatch):
    """(d) Invention proper: a well-formed id that resolves to nothing."""
    _bind_organiser(monkeypatch)
    harness, manifest, config, dossier, seed_id = _room_root(tmp_path)
    first, *_ = _organised_pair(dossier)
    first["evidence_refs"] = [{"block": "0" * 64}]
    _prompts, registered = _dispatch(harness, manifest, config, seed_id, {"candidates": [first]})
    assert len(_artifact_ids(registered)) == 1
    assert [code for code, _block in _citation_measures(harness)] == ["EVIDENCE_REF_UNKNOWN_BLOCK"]


# --- the pairing itself (S1, S7, S14, A11) -------------------------------------------


def test_the_organiser_shell_pairs_the_form_the_managed_conjecturer_fills():
    """The brief named `reasoning.conjecturer.compact.v2`; the managed path
    dispatches `conjecturer.turn.v6`, whose candidate is the same proposal."""
    from deepreason.llm.seat_sections import resolve_seat_shell
    from deepreason.llm.wire import ReasoningConjecturerTurnWireV6
    from deepreason.workloads.text import ReasoningCandidateProposal

    shell = resolve_seat_shell("conjecturer", ORGANISER_SHELL)
    assert shell.form_id == "conjecturer.turn.v6"
    assert shell.layout_id == "seat-pack.conjecturer.organiser-v1"
    assert shell.role_prompt_template_id == ORGANISER_WORDING
    assert ReasoningConjecturerTurnWireV6.model_fields["candidates"].annotation == list[
        ReasoningCandidateProposal
    ]


def test_the_defaults_have_not_moved():
    from deepreason.llm.seat_layouts import CONJECTURER_LEGACY_SHELL, CRITIC_LEGACY_SHELL
    from deepreason.llm.seat_sections import resolve_seat_shell

    assert resolve_seat_shell("conjecturer") == CONJECTURER_LEGACY_SHELL
    assert resolve_seat_shell("argumentative_critic") == CRITIC_LEGACY_SHELL


def test_the_organiser_layout_keeps_the_record_side_sections_and_drops_the_inventive_ones():
    from deepreason.llm.seat_layouts import CONJECTURER_LEGACY_LAYOUT
    from deepreason.llm.seat_sections import resolve_seat_pack_layout

    layout = resolve_seat_pack_layout("conjecturer", "seat-pack.conjecturer.organiser-v1")
    ids = [entry.plugin_id for entry in layout.entries]
    for kept in ("dr.problem", "dr.criteria", "dr.open-criticisms", "dr.mandatory-interface",
                 "dr.neighbourhood", "dr.evidence.frozen", "dr.evidence.citable"):
        assert kept in ids, kept
    for dropped in ("dr.school-stance", "dr.crossover", "dr.complement-directive",
                    "dr.diversity-specifications", "dr.history.v1",
                    "dr.output-contract.conjecturer"):
        assert dropped not in ids, dropped
    assert ids[-1] == "dr.output-contract.organiser"
    by_id = {entry.plugin_id: entry for entry in layout.entries}
    for exact in ("dr.evidence.frozen", "dr.evidence.citable"):
        assert not by_id[exact].droppable and not by_id[exact].compressible
    legacy = {entry.plugin_id: entry for entry in CONJECTURER_LEGACY_LAYOUT.entries}
    for plugin_id, entry in by_id.items():
        if plugin_id in legacy and plugin_id not in ("dr.evidence.frozen", "dr.evidence.citable"):
            assert entry == legacy[plugin_id], plugin_id


def test_the_blind_critic_layout_is_the_legacy_layout_minus_the_evidence_pair():
    from deepreason.llm.seat_layouts import CRITIC_LEGACY_LAYOUT, CRITIC_LEGACY_SHELL
    from deepreason.llm.seat_sections import resolve_seat_pack_layout, resolve_seat_shell

    blind = resolve_seat_pack_layout("argumentative_critic", "seat-pack.critic.evidence-blind-v1")
    expected = [
        entry for entry in CRITIC_LEGACY_LAYOUT.entries
        if entry.plugin_id not in ("dr.premise-invitation", "dr.evidence.citable")
    ]
    assert list(blind.entries) == expected
    assert len(expected) == len(CRITIC_LEGACY_LAYOUT.entries) - 2
    shell = resolve_seat_shell("argumentative_critic", BLIND_CRITIC_SHELL)
    assert shell.form_id == CRITIC_LEGACY_SHELL.form_id
    assert shell.role_prompt_template_id == CRITIC_LEGACY_SHELL.role_prompt_template_id


def test_the_organiser_wording_moves_the_conjecturer_alone():
    from deepreason.llm.role_prompts import resolve_role_prompt_template

    organiser = resolve_role_prompt_template(ORGANISER_WORDING)
    legacy = resolve_role_prompt_template("role-prompt.legacy-v0")
    assert set(organiser.standard) == set(legacy.standard)
    assert organiser.standard["conjecturer"] != legacy.standard["conjecturer"]
    assert organiser.standard["conjecturer"].endswith(legacy.standard["conjecturer"][-60:])
    for role in legacy.standard:
        if role != "conjecturer":
            assert organiser.standard[role] == legacy.standard[role], role
    for role in legacy.compact_directive:
        if role != "conjecturer":
            assert organiser.compact_directive[role] == legacy.compact_directive[role], role
