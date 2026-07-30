"""Amendment epochs: reshape the question and inject evidence after a stop.

Regression coverage for docs/proposals/AMENDMENT_EPOCHS.md.  Every case runs
against a real converged v6 root amended offline, and asserts the four
guarantees the design turns on: replay stays valid across the fence, evidence
admitted before the amendment stays byte-checkably cited after it, the
reshaped question wins the continuation's first cycle, and a crash mid-amend
leaves a typed refusal with the parent epoch untouched.
"""

from __future__ import annotations

import json

import pytest

import deepreason.amendment.apply as apply_module
from deepreason.amendment import AmendmentError, amend_run, load_amendments
from deepreason.amendment.state import (
    AMENDMENT_CHAIN_NAME,
    AMENDMENT_RECORD_NAME,
    current_epoch,
    dossier_union,
    epoch_directory,
    epoch_problem_ids,
    staged_amendment,
    union_citable_blocks,
)
from deepreason.application import (
    ContinueTextRunIntentV1,
    InspectTextRunIntentV1,
    RunBudgetIntentV1,
    StartTextRunIntentV1,
)
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
)
from deepreason.capabilities.policy import (
    AttachedEvidencePolicyV1,
    InquiryCapabilityPolicyV1,
)
from deepreason.llm.contracts import EvidenceRefClaimV1
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
    check_candidate_citations,
    load_evidence_dossier,
    load_run_input,
)
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.ontology import Provenance
from deepreason.ontology.problem import SpawnTrigger
from deepreason.run_manifest import MANIFEST_NAME, bind_run_manifest
from deepreason.runtime.continuation import prepare_continuation
from deepreason.runtime.terminal_authority import derive_terminal_authority
from tests.test_run_input_v6_commitments import (
    _commitment,
    _config,
    _control,
    _write_qualification,
)
from tests.test_v6_resumed_terminal_revalidation import _record_converged_stop
from deepreason.admission.parse import AdmissionInput, admit_sources
from deepreason.run_manifest import compile_run_manifest
from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem


STAMP = "2026-07-17T00:00:00Z"
SOURCE_TEXT = (
    "# Delayed feedback\n\n"
    "A control loop that reports its error one interval late oscillates "
    "whenever the loop gain exceeds unity.\n"
)
SUPPLEMENT_TEXT = (
    "# Sampled control\n\n"
    "Sampling the same loop at twice the Nyquist rate removes the "
    "oscillation without changing the loop gain.\n"
)
ORIGINAL_QUESTION = "Why does the delayed-feedback loop oscillate?"
RESHAPED_QUESTION = (
    "Under what sampling regime does the delayed-feedback loop stay stable?"
)


def _problem_id(question: str) -> str:
    from deepreason.preparation import _question_digest

    return f"question-{_question_digest(question)[:32]}"


def _evidence_manifest(digest: str):
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
                maximum_sources=8,
                maximum_total_bytes=64 * 1024,
                maximum_excerpt_bytes_per_source=4 * 1024,
                maximum_sources_per_pack=4,
            ),
        ),
        run_input_digest=digest,
    )


def _admit(text: str, *, problem_ref: str, locator: str):
    dossier, _report = admit_sources(
        [AdmissionInput(locator=locator, data=text.encode("utf-8"))],
        problem_ref=problem_ref,
        provenance=AttachedSourceProvenanceV1(
            supplied_by="amendment fixture",
            acquisition_method="offline construction",
        ),
    )
    return dossier


def _converged_root(tmp_path, monkeypatch, *, name="amend-root"):
    """One real v6 run that reaches a valid typed terminal stop offline."""

    root = tmp_path / name
    commitment = _commitment()
    problem_id = _problem_id(ORIGINAL_QUESTION)
    dossier = _admit(SOURCE_TEXT, problem_ref=problem_id, locator="delayed.md")
    from deepreason.storage.blobs import BlobStore

    BlobStore(root / "blobs").put(SOURCE_TEXT.encode("utf-8"))
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id,
            description=ORIGINAL_QUESTION,
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    manifest = _evidence_manifest(run_input.run_input_digest)
    bind_run_manifest(manifest, root)
    _write_qualification(root, manifest)

    def finish_without_provider(harness, _config, _cycles, token_budget, **_kwargs):
        # One surviving non-import candidate makes the original question
        # "solved" for scheduler ranking, which is exactly the state a
        # reshaped question has to out-rank.
        harness.create_artifact(
            "Loop gain above unity is what sustains the oscillation.",
            provenance=Provenance(role="conjecturer"),
            problem_id=problem_id,
        )
        stop = _record_converged_stop(root, manifest, harness)
        return (
            {"frontier": [], "survivors": [], "stop_reason": stop["reason"]},
            None,
            {
                "metered_tokens": None,
                "logged_tokens_this_run": 0,
                "delta": None,
                "note": "offline no-provider fixture",
            },
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", finish_without_provider)
    service = TextRunApplicationService(TextRunWorkerRegistry())
    spec = ReasoningWorkloadSpec(
        problem=WorkloadProblem(id=problem_id, description=ORIGINAL_QUESTION),
        criteria=(commitment,),
        allow_rubric=False,
    )
    started = service.start(
        StartTextRunIntentV1(
            root=str(root),
            workload=spec,
            run_manifest_ref=str(tmp_path / "unused-manifest.json"),
            budget={"cycles": 1, "token_budget": "unlimited"},
        ),
        manifest_override=manifest,
        credential_checker=lambda _manifest: [],
    )
    service.wait(started.root, timeout=30)
    service.result(InspectTextRunIntentV1(root=started.root))
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    return root, manifest, service, problem_id


def _supplement_file(tmp_path):
    path = tmp_path / "sampled.md"
    path.write_text(SUPPLEMENT_TEXT, encoding="utf-8")
    return path


def _bytes_of(root):
    return {
        name: (root / name).read_bytes()
        for name in (
            MANIFEST_NAME,
            "run-input.json",
            "evidence-dossier.json",
        )
    }


def test_amendment_appends_an_epoch_and_edits_nothing(tmp_path, monkeypatch):
    root, manifest, _service, problem_id = _converged_root(tmp_path, monkeypatch)
    before = _bytes_of(root)
    log_before = (root / "log.jsonl").read_bytes()

    result = amend_run(
        root,
        attach=(str(_supplement_file(tmp_path)),),
        reshape_question=RESHAPED_QUESTION,
    )

    assert result["epoch"] == 1
    assert result["problem_id"] == _problem_id(RESHAPED_QUESTION)
    assert result["superseded_problem_id"] == problem_id
    # Every epoch-0 document keeps its exact canonical bytes.
    assert _bytes_of(root) == before
    # The ledger only grew.
    assert (root / "log.jsonl").read_bytes().startswith(log_before)

    (record,) = load_amendments(root)
    assert record.parent_manifest_digest == manifest.sha256
    assert record.parent_run_input_digest == load_run_input(root).run_input_digest
    assert record.parent_dossier_digest == load_evidence_dossier(root).dossier_digest
    assert record.supplemental_dossier_digests == (
        result["evidence_dossier_digest"],
    )
    assert current_epoch(root) == 1

    # The reshaped question enters as a seed whose lineage names the question
    # it supersedes; the old problem is untouched.
    replayed = Harness(root, read_only=True)
    reshaped = replayed.state.problems[record.problem_id]
    assert reshaped.provenance.trigger == SpawnTrigger.SEED
    assert list(reshaped.provenance.from_) == [problem_id]
    assert replayed.state.problems[problem_id].description == ORIGINAL_QUESTION


def test_verify_root_stays_valid_across_the_amendment_fence(tmp_path, monkeypatch):
    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)

    baseline = verify_root(root)
    assert baseline["violations"] == []

    amend_run(
        root,
        attach=(str(_supplement_file(tmp_path)),),
        reshape_question=RESHAPED_QUESTION,
    )

    assert verify_root(root)["violations"] == []


def test_old_citations_verify_identically_after_the_amendment(
    tmp_path, monkeypatch
):
    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    harness = Harness(root, read_only=True)
    original = load_evidence_dossier(root)
    block = next(item for item in original.blocks if item.tier == "evidence")
    claim = EvidenceRefClaimV1(block=block.id, quote="loop gain")

    before = check_candidate_citations((claim,), original, harness.blobs)
    assert [check.code for check in before] == ["EVIDENCE_CITATION_VERIFIED"]

    amend_run(root, attach=(str(_supplement_file(tmp_path)),))

    dossiers = dossier_union(root)
    assert len(dossiers) == 2
    after = check_candidate_citations(
        (claim,), dossiers[0], harness.blobs, dossiers=dossiers
    )
    assert after == before

    # New evidence only adds citable blocks; both dossiers' blocks resolve.
    supplemental = next(
        item
        for item in dossiers[1].blocks
        if item.tier == "evidence" and item.source_sha256 not in {
            source.content_sha256 for source in original.sources
        }
    )
    fresh = check_candidate_citations(
        (EvidenceRefClaimV1(block=supplemental.id, quote="Nyquist"),),
        dossiers[0],
        harness.blobs,
        dossiers=dossiers,
    )
    assert [check.code for check in fresh] == ["EVIDENCE_CITATION_VERIFIED"]
    assert {item.id for item in union_citable_blocks(root)} >= {
        block.id,
        supplemental.id,
    }


def test_reshaped_question_wins_the_continuation_first_cycle(
    tmp_path, monkeypatch
):
    root, manifest, _service, problem_id = _converged_root(tmp_path, monkeypatch)
    amend_run(
        root,
        attach=(str(_supplement_file(tmp_path)),),
        reshape_question=RESHAPED_QUESTION,
    )
    reshaped_id = _problem_id(RESHAPED_QUESTION)

    prepare_continuation(root, cycles=1, tokens=32, check_operator_lock=False)

    from deepreason.config import Config
    from deepreason.scheduler.scheduler import Scheduler

    scheduler = Scheduler(
        Harness(root, read_only=True), None, Config(N_SCHOOLS=0)
    )
    selected = scheduler._select_problem()

    assert selected is not None
    assert selected.id == reshaped_id
    # The superseded question is still on the frontier, still attackable.
    assert problem_id in scheduler.harness.state.problems


def test_partial_amendment_refuses_continuation_and_completes_on_rerun(
    tmp_path, monkeypatch
):
    root, manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    supplement = str(_supplement_file(tmp_path))
    parent_bytes = _bytes_of(root)

    def crash_before_commit(_root, _record):
        raise RuntimeError("simulated crash before the chain line landed")

    with monkeypatch.context() as crashed:
        crashed.setattr(apply_module, "_commit_chain_line", crash_before_commit)
        with pytest.raises(RuntimeError, match="simulated crash"):
            amend_run(
                root, attach=(supplement,), reshape_question=RESHAPED_QUESTION
            )

    # A typed partial chain: staged, never committed, parent epoch intact.
    pending = staged_amendment(root)
    assert pending is not None and pending.seq == 1
    assert load_amendments(root) == ()
    assert not (root / AMENDMENT_CHAIN_NAME).exists()
    assert _bytes_of(root) == parent_bytes

    with pytest.raises(ValueError, match="CONTINUE_AMENDMENT_INCOMPLETE"):
        prepare_continuation(root, cycles=1, tokens=32, check_operator_lock=False)
    assert verify_root(root)["violations"] != []

    # A different amendment cannot silently replace the staged one.
    with pytest.raises(AmendmentError, match="AMEND_PENDING_CONFLICT"):
        amend_run(root, attach=(supplement,), reshape_question="A third question?")

    # The byte-identical re-run completes the same epoch.
    result = amend_run(
        root, attach=(supplement,), reshape_question=RESHAPED_QUESTION
    )
    assert result["amendment_digest"] == pending.amendment_digest
    assert result["fence_seq"] == pending.fence_seq
    assert staged_amendment(root) is None
    assert verify_root(root)["violations"] == []
    prepare_continuation(root, cycles=1, tokens=32, check_operator_lock=False)


def test_amendment_refuses_an_empty_or_unchanged_request(tmp_path, monkeypatch):
    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)

    with pytest.raises(AmendmentError, match="AMEND_EMPTY"):
        amend_run(root)
    with pytest.raises(AmendmentError, match="AMEND_QUESTION_EMPTY"):
        amend_run(root, reshape_question="   ")
    with pytest.raises(AmendmentError, match="AMEND_QUESTION_UNCHANGED"):
        amend_run(root, reshape_question=ORIGINAL_QUESTION)
    assert load_amendments(root) == ()
    assert staged_amendment(root) is None


def test_amendment_refuses_a_run_that_is_not_at_a_terminal_stop(tmp_path):
    root = tmp_path / "open-root"
    problem_id = _problem_id(ORIGINAL_QUESTION)
    dossier = _admit(SOURCE_TEXT, problem_ref=problem_id, locator="delayed.md")
    from deepreason.storage.blobs import BlobStore

    BlobStore(root / "blobs").put(SOURCE_TEXT.encode("utf-8"))
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id, description=ORIGINAL_QUESTION, criteria=(_commitment(),)
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    bind_run_manifest(_evidence_manifest(run_input.run_input_digest), root)

    with pytest.raises(AmendmentError, match="AMEND_NOT_AT_TERMINAL"):
        amend_run(root, reshape_question=RESHAPED_QUESTION)
    assert not (root / "run-epochs").exists()


def test_question_only_amendment_keeps_its_parent_dossier(tmp_path, monkeypatch):
    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    parent_dossier = load_evidence_dossier(root)

    result = amend_run(root, reshape_question=RESHAPED_QUESTION)

    (record,) = load_amendments(root)
    assert record.supplemental_dossier_digests == ()
    assert record.successor_dossier_digest == parent_dossier.dossier_digest
    assert result["evidence_dossier_digest"] == parent_dossier.dossier_digest
    # The epoch's own copy is byte-identical, and the union does not
    # double-count it.
    epoch = epoch_directory(root, 1)
    assert (epoch / "evidence-dossier.json").read_bytes() == (
        root / "evidence-dossier.json"
    ).read_bytes()
    assert len(dossier_union(root)) == 1
    # The superseded question keeps its claim on the dossier, and the
    # reshaped one inherits it, so a question-only amendment does not
    # silently cut the new question off from the evidence already admitted.
    assert epoch_problem_ids(root) == {
        _problem_id(ORIGINAL_QUESTION),
        _problem_id(RESHAPED_QUESTION),
    }
    assert verify_root(root)["violations"] == []


def test_second_amendment_chains_onto_the_first(tmp_path, monkeypatch):
    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    amend_run(root, attach=(str(_supplement_file(tmp_path)),))

    third = tmp_path / "third.md"
    third.write_text(
        "# Loop margin\n\nPhase margin below 30 degrees restores the "
        "oscillation at any sampling rate.\n",
        encoding="utf-8",
    )
    amend_run(root, attach=(str(third),), reshape_question=RESHAPED_QUESTION)

    first, second = load_amendments(root)
    assert second.seq == 2
    assert second.parent_amendment_digest == first.amendment_digest
    assert second.parent_dossier_digest == first.successor_dossier_digest
    assert second.fence_seq > first.fence_seq
    assert len(dossier_union(root)) == 3
    assert verify_root(root)["violations"] == []


def test_continuation_runs_the_reshaped_question_under_the_same_root(
    tmp_path, monkeypatch
):
    root, manifest, service, problem_id = _converged_root(tmp_path, monkeypatch)
    amend_run(
        root,
        attach=(str(_supplement_file(tmp_path)),),
        reshape_question=RESHAPED_QUESTION,
    )
    reshaped_id = _problem_id(RESHAPED_QUESTION)
    worked = []

    def finish_without_provider(harness, _config, _cycles, token_budget, **_kwargs):
        from deepreason.config import Config
        from deepreason.scheduler.scheduler import Scheduler

        worked.append(
            Scheduler(harness, None, Config(N_SCHOOLS=0))._select_problem().id
        )
        stop = _record_converged_stop(root, manifest, harness)
        return (
            {"frontier": [], "survivors": [], "stop_reason": stop["reason"]},
            None,
            {
                "metered_tokens": None,
                "logged_tokens_this_run": 0,
                "delta": None,
                "note": "offline no-provider fixture",
            },
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", finish_without_provider)
    continued = service.continue_run(
        ContinueTextRunIntentV1(
            root=str(root),
            budget=RunBudgetIntentV1(cycles=1, token_budget="unlimited"),
            expected_manifest_digest=manifest.sha256,
        ),
        credential_checker=lambda _manifest: [],
    )
    service.wait(continued.root, timeout=30)
    result = service.result(InspectTextRunIntentV1(root=continued.root)).payload

    assert worked == [reshaped_id]
    assert result["state"] == "completed"
    # Same root, same manifest, one epoch further on.
    assert continued.manifest_digest == manifest.sha256
    assert current_epoch(root) == 1
    assert Harness(root, read_only=True).state.problems.keys() >= {
        problem_id,
        reshaped_id,
    }
    assert verify_root(root)["violations"] == []


def test_staged_epoch_record_is_canonical_and_matches_the_chain_line(
    tmp_path, monkeypatch
):
    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    amend_run(root, attach=(str(_supplement_file(tmp_path)),))

    staged = (epoch_directory(root, 1) / AMENDMENT_RECORD_NAME).read_bytes()
    committed = (root / AMENDMENT_CHAIN_NAME).read_bytes()
    assert staged == committed
    assert json.loads(staged)["schema"] == "run-amendment.v1"


def test_cli_amend_reports_the_epoch_and_refuses_typed(
    tmp_path, monkeypatch, capsys
):
    from deepreason.cli.main import main

    root, _manifest, _service, problem_id = _converged_root(tmp_path, monkeypatch)
    argv = ["--root", str(root), "amend"]

    assert main([*argv]) == 1
    assert "AMEND_EMPTY" in capsys.readouterr().err

    assert (
        main(
            [
                *argv,
                "--attach",
                str(_supplement_file(tmp_path)),
                "--reshape-question",
                RESHAPED_QUESTION,
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["schema"] == "deepreason-amendment-result-v1"
    assert payload["epoch"] == 1
    assert payload["superseded_problem_id"] == problem_id
    assert payload["admission"]["sources_admitted"] == 1
    assert "deepreason" in captured.err
    assert current_epoch(root) == 1


def test_mcp_amend_run_is_exposed_and_hides_host_paths(tmp_path, monkeypatch):
    from deepreason import mcp_server

    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    tools = {tool["name"]: tool for tool in mcp_server._tools()}
    assert "amend_run" in tools
    assert tools["amend_run"]["inputSchema"]["required"] == ["run_id"]

    monkeypatch.setattr(mcp_server, "_resolve_managed_root", lambda _run_id: root)
    payload = json.loads(
        mcp_server.call_tool(
            "amend_run",
            {
                "run_id": "managed-run",
                "attachments": [str(_supplement_file(tmp_path))],
                "reshape_question": RESHAPED_QUESTION,
            },
        )
    )

    assert payload["run_id"] == "managed-run"
    assert "root" not in payload
    assert payload["epoch"] == 1
    assert load_amendments(root)[0].amendment_digest == payload["amendment_digest"]


def test_staged_epoch_that_never_reached_the_ledger_is_superseded(
    tmp_path, monkeypatch
):
    """R15a: nothing applied means nothing to orphan, so a different
    amendment replaces the staged one outright."""

    root, _manifest, _service, parent = _converged_root(tmp_path, monkeypatch)
    supplement = str(_supplement_file(tmp_path))
    log_before = (root / "log.jsonl").read_bytes()

    def crash_before_apply(_root, _record, *, supplement):
        raise RuntimeError("simulated crash before the ledger chain landed")

    with monkeypatch.context() as crashed:
        crashed.setattr(apply_module, "_apply_ledger_chain", crash_before_apply)
        with pytest.raises(RuntimeError, match="simulated crash"):
            amend_run(
                root, attach=(supplement,), reshape_question=RESHAPED_QUESTION
            )

    abandoned = staged_amendment(root)
    assert abandoned is not None
    assert abandoned.problem_id == _problem_id(RESHAPED_QUESTION)
    # Nothing reached the ledger: the staged fence is still the live head.
    assert (root / "log.jsonl").read_bytes() == log_before
    assert abandoned.fence_seq == Harness(root, read_only=True)._next_seq

    other = "Which loop gain keeps the delayed-feedback loop stable?"
    result = amend_run(root, attach=(supplement,), reshape_question=other)

    (record,) = load_amendments(root)
    assert record.amendment_digest == result["amendment_digest"]
    assert record.amendment_digest != abandoned.amendment_digest
    assert record.problem_id == _problem_id(other)
    assert record.superseded_problem_id == parent
    assert record.seq == 1
    assert staged_amendment(root) is None
    # The abandoned question never entered the record.
    replayed = Harness(root, read_only=True)
    assert _problem_id(RESHAPED_QUESTION) not in replayed.state.problems
    assert _problem_id(other) in replayed.state.problems
    assert verify_root(root)["violations"] == []
    prepare_continuation(root, cycles=1, tokens=32, check_operator_lock=False)


def test_staged_epoch_that_applied_events_refuses_and_names_the_route(
    tmp_path, monkeypatch
):
    """R15a: applied events belong to their epoch, so it is completed,
    never replaced — and the refusal says how to move forward."""

    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    supplement = str(_supplement_file(tmp_path))

    def crash_before_commit(_root, _record):
        raise RuntimeError("simulated crash before the chain line landed")

    with monkeypatch.context() as crashed:
        crashed.setattr(apply_module, "_commit_chain_line", crash_before_commit)
        with pytest.raises(RuntimeError, match="simulated crash"):
            amend_run(
                root, attach=(supplement,), reshape_question=RESHAPED_QUESTION
            )

    pending = staged_amendment(root)
    assert pending is not None
    assert pending.fence_seq < Harness(root, read_only=True)._next_seq

    with pytest.raises(AmendmentError) as refusal:
        amend_run(root, attach=(supplement,), reshape_question="A third question?")
    assert refusal.value.code == "AMEND_PENDING_CONFLICT"
    assert "complete it" in str(refusal.value)
    assert "next epoch" in str(refusal.value)

    # The named route works: complete this epoch, then open the next one.
    amend_run(root, attach=(supplement,), reshape_question=RESHAPED_QUESTION)
    third = tmp_path / "third.md"
    third.write_text("# Margin\n\nPhase margin below 30 degrees.\n", encoding="utf-8")
    second = amend_run(root, attach=(str(third),), reshape_question="A third question?")

    assert second["epoch"] == 2
    first, latest = load_amendments(root)
    assert latest.parent_amendment_digest == first.amendment_digest
    assert verify_root(root)["violations"] == []


def test_amend_refuses_a_source_already_admitted_to_this_run(
    tmp_path, monkeypatch
):
    """Regression (PARKED P2): re-attaching admitted content used to be
    accepted and then rejected by verify_root. It is refused up front now —
    before any parse, blob write, or staging."""

    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    duplicate = tmp_path / "same-again.md"
    duplicate.write_text(SOURCE_TEXT, encoding="utf-8")
    admitted = load_evidence_dossier(root)
    (bound_source,) = admitted.sources

    with pytest.raises(AmendmentError) as refusal:
        amend_run(
            root,
            attach=(str(duplicate),),
            reshape_question=RESHAPED_QUESTION,
        )

    assert refusal.value.code == "AMEND_SOURCE_ALREADY_ADMITTED"
    assert bound_source.id in str(refusal.value)
    assert "same-again.md" in str(refusal.value)
    # Refused before anything was staged or applied: no epoch, no chain, no
    # ledger growth, and the root stays valid.
    assert not (root / "run-epochs").exists()
    assert load_amendments(root) == ()
    assert staged_amendment(root) is None
    assert verify_root(root)["violations"] == []

    # A mixed batch is refused whole, not admitted minus the duplicate.
    fresh = tmp_path / "fresh.md"
    fresh.write_text(SUPPLEMENT_TEXT, encoding="utf-8")
    with pytest.raises(AmendmentError) as mixed:
        amend_run(root, attach=(str(fresh), str(duplicate)))
    assert mixed.value.code == "AMEND_SOURCE_ALREADY_ADMITTED"
    assert load_amendments(root) == ()

    # The same batch minus the duplicate is admitted normally.
    result = amend_run(root, attach=(str(fresh),))
    assert result["epoch"] == 1
    assert verify_root(root)["violations"] == []


def test_amend_refuses_content_admitted_by_an_earlier_amendment(
    tmp_path, monkeypatch
):
    """The uniqueness rule spans epochs, not just the original dossier."""

    root, _manifest, _service, _parent = _converged_root(tmp_path, monkeypatch)
    supplement = _supplement_file(tmp_path)
    amend_run(root, attach=(str(supplement),))

    again = tmp_path / "sampled-copy.md"
    again.write_text(SUPPLEMENT_TEXT, encoding="utf-8")
    with pytest.raises(AmendmentError) as refusal:
        amend_run(root, attach=(str(again),), reshape_question=RESHAPED_QUESTION)

    assert refusal.value.code == "AMEND_SOURCE_ALREADY_ADMITTED"
    assert len(load_amendments(root)) == 1
    assert verify_root(root)["violations"] == []
