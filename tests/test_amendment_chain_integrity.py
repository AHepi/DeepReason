"""Amendment-chain tamper detection: the detectors must actually fire.

Every case in `test_amendment_epochs.py` asserts a clean root. These assert
the opposite: take a legitimately amended root, corrupt exactly one thing,
and require `verify_root` to name it. A validator nobody has watched fire is
a validator nobody knows works — and in a harness whose whole claim is that
the record is the only admissible evidence, that gap is the expensive kind.
"""

from __future__ import annotations

import json
import shutil

import pytest

from deepreason.amendment import RunAmendmentV1, amend_run, load_amendments
from deepreason.amendment.state import (
    AMENDMENT_CHAIN_NAME,
    AMENDMENT_RECORD_NAME,
    AmendmentError,
    epoch_directory,
    load_amendments as load_chain,
    record_bytes,
    staged_amendment,
)
from deepreason.canonical import canonical_json
from deepreason.evidence import load_evidence_dossier
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.run_manifest import MANIFEST_NAME
from tests.test_amendment_epochs import (
    RESHAPED_QUESTION,
    _evidence_manifest,
    SUPPLEMENT_TEXT,
    _converged_root,
    _supplement_file,
)


def _bridge_capable_manifest(digest: str):
    """The amendment fixture's manifest with concrete bridge seats.

    `_config()` names only a conjecturer, so summarizer/thesis/judge compile
    to empty route tuples and no bridge can dispatch. These are the same
    offline mock seats, one per bridge function.
    """

    from deepreason.capabilities.policy import (
        AttachedEvidencePolicyV1,
        InquiryCapabilityPolicyV1,
    )
    from deepreason.config import Config
    from deepreason.run_manifest import compile_run_manifest
    from tests.test_amendment_epochs import STAMP
    from tests.test_run_input_v6_commitments import _control

    def seat(name: str) -> dict:
        return {
            "endpoint_id": f"amend-bridge-{name}",
            "endpoint": f"mock://amend-bridge-{name}",
            "model": "offline-model",
            "provider": "mock",
            "family": "offline",
            "max_tokens": 512,
            "context_window_tokens": 262_144,
        }

    return compile_run_manifest(
        Config(
            roles={
                role: [seat(role)]
                for role in ("conjecturer", "summarizer", "thesis", "judge")
            }
        ),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(6),
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2",
            attached_evidence=AttachedEvidencePolicyV1(
                enabled=True,
                maximum_sources=8,
                maximum_total_bytes=64 * 1024,
                maximum_excerpt_bytes_per_source=4 * 1024,
                maximum_sources_per_pack=4,
            ),
        ),
        run_input_digest=digest,
    )


def _amended(tmp_path, monkeypatch, *, reshape=True):
    """A legitimately amended root that verifies clean before tampering."""

    root, manifest, _service, parent = _converged_root(tmp_path, monkeypatch)
    amend_run(
        root,
        attach=(str(_supplement_file(tmp_path)),),
        reshape_question=RESHAPED_QUESTION if reshape else None,
    )
    assert verify_root(root)["violations"] == []
    return root, manifest, parent


def _checks(root) -> list[str]:
    return [item["check"] for item in verify_root(root)["violations"]]


def _details(root) -> str:
    return " | ".join(item["detail"] for item in verify_root(root)["violations"])


def _rewrite_chain(root, record: RunAmendmentV1) -> None:
    (root / AMENDMENT_CHAIN_NAME).write_bytes(record_bytes(record) + b"\n")


def _reissue(record: RunAmendmentV1, **changes) -> RunAmendmentV1:
    """Mint a structurally valid record with one field changed.

    Re-derived through ``create`` so its own digest is correct: the point is
    to defeat the cheap check and reach the cross-document ones.
    """

    values = record.model_dump(
        mode="python", by_alias=True, exclude={"amendment_digest"}, exclude_none=True
    )
    values.pop("schema", None)
    values.update(changes)
    return RunAmendmentV1.create(**values)


# --------------------------------------------------------------------- #
# Chain-level detectors                                                  #
# --------------------------------------------------------------------- #


def test_unreadable_chain_is_reported_not_ignored(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)

    (root / AMENDMENT_CHAIN_NAME).write_text("{not json at all\n", encoding="utf-8")

    assert "amendment-chain" in _checks(root)
    assert "unreadable" in _details(root)


def test_non_canonical_chain_bytes_are_rejected(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    (record,) = load_amendments(root)

    # Same record, re-serialized with pretty printing: the content is honest
    # but the bytes are not canonical, so the chain no longer reproduces.
    payload = record.model_dump(mode="json", by_alias=True, exclude_none=True)
    (root / AMENDMENT_CHAIN_NAME).write_text(
        json.dumps(payload, indent=2) .replace("\n", "") + "\n", encoding="utf-8"
    )

    assert "amendment-chain" in _checks(root)


def test_forged_amendment_digest_is_rejected(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    (record,) = load_amendments(root)

    payload = record.model_dump(mode="json", by_alias=True, exclude_none=True)
    payload["amendment_digest"] = "0" * 64
    (root / AMENDMENT_CHAIN_NAME).write_bytes(canonical_json(payload) + b"\n")

    with pytest.raises(AmendmentError) as error:
        load_chain(root)
    assert error.value.code == "AMENDMENT_RECORD_INVALID"
    assert "amendment-chain" in _checks(root)


def test_chain_anchored_to_another_manifest_is_reported(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    (record,) = load_amendments(root)

    _rewrite_chain(
        root,
        _reissue(
            record,
            parent_manifest_digest="a" * 64,
            successor_manifest_digest="a" * 64,
        ),
    )

    assert "amendment-chain" in _checks(root)
    assert "anchored to another manifest" in _details(root)


def test_a_second_epoch_that_does_not_chain_is_rejected(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    third = tmp_path / "third.md"
    third.write_text("# Margin\n\nPhase margin below 30 degrees.\n", encoding="utf-8")
    amend_run(root, attach=(str(third),))
    first, second = load_amendments(root)

    # Break only the link: epoch 2 now names a parent amendment that is not
    # epoch 1. Both records remain individually well formed.
    broken = _reissue(second, parent_amendment_digest="b" * 64)
    (root / AMENDMENT_CHAIN_NAME).write_bytes(
        record_bytes(first) + b"\n" + record_bytes(broken) + b"\n"
    )

    with pytest.raises(AmendmentError) as error:
        load_chain(root)
    assert error.value.code == "AMENDMENT_CHAIN_BROKEN"
    assert "amendment-chain" in _checks(root)


def test_a_fence_that_does_not_advance_is_rejected(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    third = tmp_path / "third.md"
    third.write_text("# Margin\n\nPhase margin below 30 degrees.\n", encoding="utf-8")
    amend_run(root, attach=(str(third),))
    first, second = load_amendments(root)

    stalled = _reissue(second, fence_seq=first.fence_seq)
    (root / AMENDMENT_CHAIN_NAME).write_bytes(
        record_bytes(first) + b"\n" + record_bytes(stalled) + b"\n"
    )

    with pytest.raises(AmendmentError) as error:
        load_chain(root)
    assert error.value.code == "AMENDMENT_CHAIN_BROKEN"


def test_out_of_order_sequence_numbers_are_rejected(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    (record,) = load_amendments(root)

    _rewrite_chain(root, _reissue(record, seq=2, parent_amendment_digest="c" * 64))

    with pytest.raises(AmendmentError) as error:
        load_chain(root)
    assert error.value.code == "AMENDMENT_CHAIN_INVALID"


def test_staged_but_uncommitted_epoch_is_named_by_verify_root(
    tmp_path, monkeypatch
):
    """Pins the check name, which the happy-path suite only asserted as
    'some violation'."""

    import deepreason.amendment.apply as apply_module

    root, _manifest, _parent = _converged_root(tmp_path, monkeypatch)[:3]

    def crash(_root, _record):
        raise RuntimeError("simulated crash before the chain line landed")

    with monkeypatch.context() as crashed:
        crashed.setattr(apply_module, "_commit_chain_line", crash)
        with pytest.raises(RuntimeError):
            amend_run(
                root,
                attach=(str(_supplement_file(tmp_path)),),
                reshape_question=RESHAPED_QUESTION,
            )

    assert staged_amendment(root) is not None
    assert "amendment-chain" in _checks(root)
    assert "staged but never committed" in _details(root)


# --------------------------------------------------------------------- #
# Epoch-document detectors                                               #
# --------------------------------------------------------------------- #


def test_missing_epoch_documents_are_reported(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)

    (epoch_directory(root, 1) / "run-input.json").unlink()

    assert "amendment-epoch" in _checks(root)
    assert "documents are unavailable" in _details(root)


def test_a_deleted_epoch_directory_is_reported(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)

    shutil.rmtree(epoch_directory(root, 1))

    assert "amendment-epoch" in _checks(root)
    assert "documents are unavailable" in _details(root)


def test_epoch_documents_that_differ_from_their_record_are_reported(
    tmp_path, monkeypatch
):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    (record,) = load_amendments(root)

    # A coherent record that nonetheless names a dossier the epoch directory
    # does not hold. (The model itself refuses the incoherent shorthand of
    # changing only one of these two fields — see the model rejection rules
    # below, "successor dossier is not the newest supplement".)
    _rewrite_chain(
        root,
        _reissue(
            record,
            successor_dossier_digest="d" * 64,
            supplemental_dossier_digests=("d" * 64,),
        ),
    )

    assert "amendment-epoch" in _checks(root)
    assert "differ from the record that binds them" in _details(root)


def test_an_epoch_naming_an_unregistered_question_is_reported(
    tmp_path, monkeypatch
):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    (record,) = load_amendments(root)

    ghost = "question-" + "e" * 32
    _rewrite_chain(root, _reissue(record, problem_id=ghost))

    checks = _checks(root)
    assert "amendment-epoch" in checks
    assert "names a question absent from the record" in _details(root)


def test_a_swapped_epoch_dossier_is_reported(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)

    # Put epoch 0's dossier where epoch 1's belongs: individually valid,
    # collectively a lie about what this epoch admitted.
    epoch = epoch_directory(root, 1)
    (epoch / "evidence-dossier.json").write_bytes(
        (root / "evidence-dossier.json").read_bytes()
    )
    (epoch / "evidence-dossier.sha256").write_text(
        load_evidence_dossier(root).dossier_digest + "\n", encoding="ascii"
    )

    assert "amendment-epoch" in _checks(root)


def test_a_source_blob_removed_after_admission_is_reported(
    tmp_path, monkeypatch
):
    """The epoch's own sources must still resolve byte for byte."""

    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    supplement_digest = None
    for source in load_evidence_dossier(epoch_directory(root, 1)).sources:
        if source.content_sha256 not in {
            item.content_sha256 for item in load_evidence_dossier(root).sources
        }:
            supplement_digest = source.content_sha256
    assert supplement_digest is not None

    blob = next(
        path
        for path in (root / "blobs").rglob("*")
        if path.is_file() and supplement_digest.endswith(path.stem[-8:])
    )
    blob.write_bytes(b"tampered bytes that are not what was admitted")

    checks = _checks(root)
    assert "amendment-epoch" in checks or "attached-evidence" in checks


def test_an_epoch_manifest_swapped_for_a_foreign_one_is_reported(
    tmp_path, monkeypatch
):
    root, manifest, _parent = _amended(tmp_path, monkeypatch)
    foreign = _evidence_manifest("9" * 64)
    assert foreign.sha256 != manifest.sha256

    epoch = epoch_directory(root, 1)
    (epoch / MANIFEST_NAME).write_bytes(foreign.canonical_bytes())
    (epoch / "run-manifest.sha256").write_text(
        foreign.sha256 + "\n", encoding="utf-8"
    )

    assert "amendment-epoch" in _checks(root)
    assert "differ from the record that binds them" in _details(root)


# --------------------------------------------------------------------- #
# The staged record must agree with what it claims to be                 #
# --------------------------------------------------------------------- #


def test_a_tampered_staged_record_is_refused_not_completed(
    tmp_path, monkeypatch
):
    import deepreason.amendment.apply as apply_module

    root, _manifest, _parent = _converged_root(tmp_path, monkeypatch)[:3]
    supplement = str(_supplement_file(tmp_path))

    def crash(_root, _record):
        raise RuntimeError("simulated crash")

    with monkeypatch.context() as crashed:
        crashed.setattr(apply_module, "_commit_chain_line", crash)
        with pytest.raises(RuntimeError):
            amend_run(
                root, attach=(supplement,), reshape_question=RESHAPED_QUESTION
            )

    staged = staged_amendment(root)
    assert staged is not None
    forged = _reissue(staged, problem_id="question-" + "f" * 32)
    (epoch_directory(root, 1) / AMENDMENT_RECORD_NAME).write_bytes(
        record_bytes(forged) + b"\n"
    )

    # Forging the staged record breaks the very authority that let its events
    # cross the terminal horizon, so the re-run fails closed rather than
    # completing someone else's epoch. The refusal names the staged epoch,
    # which is where the operator actually has to look.
    with pytest.raises(AmendmentError) as refusal:
        amend_run(root, attach=(supplement,), reshape_question=RESHAPED_QUESTION)
    assert refusal.value.code == "AMEND_NOT_AT_TERMINAL"
    assert "staged epoch 1" in str(refusal.value)
    assert load_chain(root) == ()


# --------------------------------------------------------------------- #
# Record-model rejection rules                                           #
# --------------------------------------------------------------------- #


def _valid_values(**changes) -> dict:
    values = {
        "seq": 1,
        "parent_amendment_digest": None,
        "parent_manifest_digest": "a" * 64,
        "successor_manifest_digest": "a" * 64,
        "parent_run_input_digest": "b" * 64,
        "successor_run_input_digest": "c" * 64,
        "parent_dossier_digest": "d" * 64,
        "successor_dossier_digest": "e" * 64,
        "supplemental_dossier_digests": ("e" * 64,),
        "superseded_problem_id": "q-old",
        "problem_id": "q-new",
        "fence_seq": 9,
        "created_at": "2026-07-30T00:00:00Z",
    }
    values.update(changes)
    return values


def test_a_well_formed_record_round_trips() -> None:
    record = RunAmendmentV1.create(**_valid_values())
    assert RunAmendmentV1.model_validate(
        json.loads(record_bytes(record))
    ) == record


@pytest.mark.parametrize(
    ("label", "changes"),
    [
        (
            "empty amendment",
            {
                "problem_id": None,
                "superseded_problem_id": None,
                "supplemental_dossier_digests": (),
                "successor_dossier_digest": "d" * 64,
            },
        ),
        ("one-sided supersession", {"superseded_problem_id": None}),
        ("self-superseding question", {"superseded_problem_id": "q-new"}),
        (
            "successor dossier is not the newest supplement",
            {"successor_dossier_digest": "f" * 64},
        ),
        (
            "no supplement but a changed dossier",
            {"supplemental_dossier_digests": (), "successor_dossier_digest": "e" * 64},
        ),
        ("run input unchanged", {"successor_run_input_digest": "b" * 64}),
        ("first epoch names a parent", {"parent_amendment_digest": "0" * 64}),
        ("later epoch names no parent", {"seq": 2, "parent_amendment_digest": None}),
        (
            "duplicate supplemental digests",
            {"supplemental_dossier_digests": ("e" * 64, "e" * 64)},
        ),
    ],
)
def test_the_record_model_refuses_incoherent_amendments(label, changes) -> None:
    with pytest.raises(ValueError):
        RunAmendmentV1.create(**_valid_values(**changes))


def test_a_record_whose_digest_does_not_cover_its_payload_is_refused() -> None:
    honest = RunAmendmentV1.create(**_valid_values())
    payload = honest.model_dump(mode="json", by_alias=True, exclude_none=True)
    payload["fence_seq"] = honest.fence_seq + 1
    with pytest.raises(ValueError):
        RunAmendmentV1.model_validate(payload)


# --------------------------------------------------------------------- #
# Three epochs, not two                                                  #
# --------------------------------------------------------------------- #


def test_three_chained_epochs_validate_and_window_correctly(
    tmp_path, monkeypatch
):
    root, _manifest, parent = _converged_root(tmp_path, monkeypatch)[:3]
    questions = [
        "Under what sampling regime does the loop stay stable?",
        "Which loop gain keeps the sampled loop stable?",
        "What phase margin does the stable sampled loop need?",
    ]
    files = []
    for index, body in enumerate(
        (SUPPLEMENT_TEXT, "# Gain\n\nLoop gain under 0.8 is stable.\n",
         "# Margin\n\nPhase margin under 30 degrees re-destabilises.\n")
    ):
        path = tmp_path / f"epoch-{index}.md"
        path.write_text(body, encoding="utf-8")
        files.append(str(path))

    for question, path in zip(questions, files, strict=True):
        amend_run(root, attach=(path,), reshape_question=question)

    chain = load_amendments(root)
    assert [record.seq for record in chain] == [1, 2, 3]
    assert chain[1].parent_amendment_digest == chain[0].amendment_digest
    assert chain[2].parent_amendment_digest == chain[1].amendment_digest
    assert (
        chain[0].fence_seq < chain[1].fence_seq < chain[2].fence_seq
    )
    # Each epoch chains its documents to the one before it.
    for earlier, later in zip(chain, chain[1:], strict=False):
        assert later.parent_run_input_digest == earlier.successor_run_input_digest
        assert later.parent_dossier_digest == earlier.successor_dossier_digest

    assert verify_root(root)["violations"] == []

    # Four dossiers bound, every source unique, every question on the frontier.
    from deepreason.amendment.state import dossier_union, epoch_problem_ids

    dossiers = dossier_union(root)
    assert len(dossiers) == 4
    source_ids = [
        source.id for dossier in dossiers for source in dossier.sources
    ]
    assert len(source_ids) == len(set(source_ids)) == 4
    problems = Harness(root, read_only=True).state.problems
    assert epoch_problem_ids(root) <= set(problems)
    assert len(epoch_problem_ids(root)) == 4

    # Corrupting the MIDDLE epoch is still caught, not masked by its
    # well-formed neighbours.
    (epoch_directory(root, 2) / "run-input.json").unlink()
    assert "amendment-epoch" in _checks(root)


# --------------------------------------------------------------------- #
# Amendment beside a commitment-bound bridge episode                     #
# --------------------------------------------------------------------- #


def test_amendment_and_a_bridge_episode_coexist_past_one_horizon(tmp_path):
    """Both post-terminal authorizations at once.

    `_validate_post_terminal_descendants` authorizes two kinds of event past
    a terminal horizon: commitment-bound bridge work, and an amendment's own
    application. Every other test exercises exactly one of them. A real
    campaign root composes a grounded answer and THEN gets amended, so the
    two have to hold simultaneously.

    Built on the bridge suite's own proven root rather than the amendment
    suite's, because what is under test here is the interaction, not the
    evidence path — so this is a question-only amendment.
    """

    from deepreason.bridge.events import BridgeAction
    from deepreason.bridge.retry import WorkflowRetryPolicyV1
    from deepreason.runtime.terminal_authority import derive_terminal_authority
    from deepreason.verification.report import verify_root_report
    from tests.test_v6_bridge_transactions import (
        _bind_recovery_manifest,
        _recovery_adapter,
        _recovery_policy,
        _recovery_responses,
        _seed_recovery_problem,
    )

    root = tmp_path / "bridged-then-amended"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)

    dispatches: list[str] = []
    adapter = _recovery_adapter(
        harness, manifest, _recovery_responses(), dispatches
    )
    terminal = harness.build_bridge(
        problem_id,
        "answer",
        _recovery_policy(manifest),
        run_manifest_digest=manifest.sha256,
        stage_a_adapter=adapter,
        composition_adapter=adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
    )
    assert terminal.process_status == "success", terminal.error_code
    assert dispatches, "the bridge must have really run, not been replayed"

    bridged = Harness(root, read_only=True)
    horizon = bridged.workflow_state.current_terminal_commitment
    assert horizon is not None
    bridge_seqs = [
        event.seq
        for event in bridged.log.read()
        if event.bridge is not None
        and event.seq > horizon.reasoning_event_horizon_seq
    ]
    assert bridge_seqs, "the episode must sit past the terminal horizon"
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    before = verify_root_report(root)
    assert before.integrity_valid and before.security_valid

    # Now amend the same root. Its events land past the same horizon, beside
    # the bridge episode's.
    reshaped = "Which surviving idea should be presented, given the review?"
    result = amend_run(root, reshape_question=reshaped)
    assert result["epoch"] == 1
    assert result["superseded_problem_id"] == problem_id
    assert result["fence_seq"] > max(bridge_seqs)

    amended = Harness(root, read_only=True)
    actions = [
        event.bridge.action
        for event in amended.log.read()
        if event.bridge is not None
    ]
    assert BridgeAction.COMPLETED in actions, "the bridge episode still stands"
    assert result["problem_id"] in amended.state.problems
    assert problem_id in amended.state.problems

    # Both authorizations hold together, and replay is still clean.
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    after = verify_root_report(root)
    assert after.integrity_valid and after.security_valid
    assert verify_root(root)["violations"] == []


def test_a_stray_post_horizon_event_is_still_refused_after_an_amendment(
    tmp_path, monkeypatch
):
    """The amendment authorization must not become a general licence.

    Widening `_validate_post_terminal_descendants` is only safe if it admits
    an amendment's own declared events and nothing else. This plants an
    ordinary conjecturer artifact past the fence and requires authority to
    collapse.
    """

    from deepreason.ontology import Provenance
    from deepreason.runtime.terminal_authority import derive_terminal_authority

    root, manifest, parent = _amended(tmp_path, monkeypatch)
    assert derive_terminal_authority(root, manifest=manifest).current_valid

    Harness(root).create_artifact(
        "An ordinary conjecture smuggled in past the terminal horizon.",
        provenance=Provenance(role="conjecturer"),
        problem_id=parent,
    )

    authority = derive_terminal_authority(root, manifest=manifest)
    assert not authority.current_valid
    assert authority.detail_code == "TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED"


# --------------------------------------------------------------------- #
# The operator-facing refusal surface                                    #
# --------------------------------------------------------------------- #


def test_amend_refuses_a_root_that_is_not_a_directory(tmp_path):
    missing = tmp_path / "no-such-root"
    with pytest.raises(AmendmentError) as refusal:
        amend_run(missing, reshape_question=RESHAPED_QUESTION)
    assert refusal.value.code == "AMEND_ROOT_UNAVAILABLE"


def test_amend_refuses_an_unreadable_attachment_path(tmp_path, monkeypatch):
    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    with pytest.raises(AmendmentError) as refusal:
        amend_run(root, attach=(str(tmp_path / "not-a-file.md"),))
    assert refusal.value.code == "ADMISSION_PATH_UNAVAILABLE"
    assert not (root / "run-epochs").exists()


def test_amend_refuses_when_the_manifest_does_not_enable_evidence(
    tmp_path, monkeypatch
):
    from deepreason.capabilities.policy import InquiryCapabilityPolicyV1
    from deepreason.run_manifest import compile_run_manifest
    from tests.test_amendment_epochs import STAMP
    from tests.test_run_input_v6_commitments import _config, _control

    def without_evidence(digest: str):
        return compile_run_manifest(
            _config(),
            schema_version=6,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
            control_plane_policy=_control(6),
            inquiry_capability_policy=InquiryCapabilityPolicyV1(
                capability_profile="inquiry-capabilities.v2"
            ),
            run_input_digest=digest,
        )

    root, _manifest, _service, _parent = _converged_root(
        tmp_path, monkeypatch, manifest_factory=without_evidence
    )
    with pytest.raises(AmendmentError) as refusal:
        amend_run(root, attach=(str(_supplement_file(tmp_path)),))
    assert refusal.value.code == "AMEND_EVIDENCE_NOT_AUTHORIZED"

    # This fixture binds a source its manifest does not authorize, so the root
    # is already non-conforming before any amendment. That is the useful
    # property to pin: amending an already-flawed root reports exactly the
    # flaws it had, and invents none.
    baseline = _checks(root)
    assert baseline == ["run-input"]

    # The question may still be reshaped: only the evidence path is closed.
    assert amend_run(root, reshape_question=RESHAPED_QUESTION)["epoch"] == 1
    assert _checks(root) == baseline


def test_amend_refuses_evidence_beyond_the_frozen_budget(
    tmp_path, monkeypatch
):
    from deepreason.capabilities.policy import (
        AttachedEvidencePolicyV1,
        InquiryCapabilityPolicyV1,
    )
    from deepreason.run_manifest import compile_run_manifest
    from tests.test_amendment_epochs import STAMP
    from tests.test_run_input_v6_commitments import _config, _control

    def one_source_only(digest: str):
        return compile_run_manifest(
            _config(),
            schema_version=6,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
            control_plane_policy=_control(6),
            inquiry_capability_policy=InquiryCapabilityPolicyV1(
                capability_profile="inquiry-capabilities.v2",
                attached_evidence=AttachedEvidencePolicyV1(
                    enabled=True,
                    maximum_sources=1,
                    maximum_total_bytes=64 * 1024,
                    maximum_excerpt_bytes_per_source=4 * 1024,
                    maximum_sources_per_pack=1,
                ),
            ),
            run_input_digest=digest,
        )

    root, _manifest, _service, _parent = _converged_root(
        tmp_path, monkeypatch, manifest_factory=one_source_only
    )
    # Epoch 0 already holds the one source the manifest authorizes, so the
    # budget binds the UNION and a second source is refused.
    with pytest.raises(AmendmentError) as refusal:
        amend_run(root, attach=(str(_supplement_file(tmp_path)),))
    assert refusal.value.code == "AMEND_EVIDENCE_BUDGET_EXCEEDED"
    assert "2 sources" in str(refusal.value)
    assert load_chain(root) == ()
    assert verify_root(root)["violations"] == []


def test_amend_refuses_while_an_operator_lock_is_live(tmp_path, monkeypatch):
    from deepreason.locking import operator_locks

    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    held = operator_locks(root, owner="test-holder", blocking=False)
    try:
        with pytest.raises(AmendmentError) as refusal:
            amend_run(root, reshape_question=RESHAPED_QUESTION)
        assert refusal.value.code == "AMEND_RUN_ACTIVE"
    finally:
        held.release()

    # Released: the same amendment now lands.
    assert amend_run(root, reshape_question=RESHAPED_QUESTION)["epoch"] == 1


def test_epoch_directory_refuses_an_out_of_range_epoch(tmp_path):
    with pytest.raises(AmendmentError) as low:
        epoch_directory(tmp_path, 0)
    assert low.value.code == "AMENDMENT_EPOCH_OUT_OF_RANGE"
    with pytest.raises(AmendmentError) as high:
        epoch_directory(tmp_path, 1000)
    assert high.value.code == "AMENDMENT_EPOCH_OUT_OF_RANGE"


def test_an_oversized_chain_file_is_refused(tmp_path, monkeypatch):
    root, _manifest, _parent = _amended(tmp_path, monkeypatch)
    from deepreason.amendment import state as state_module

    monkeypatch.setattr(state_module, "_MAX_CHAIN_BYTES", 8)
    with pytest.raises(AmendmentError) as refusal:
        load_chain(root)
    assert refusal.value.code == "AMENDMENT_CHAIN_INVALID"
