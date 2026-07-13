"""Support-inert capsule references and explicit current-run test adoption."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from deepreason import programs
from deepreason.canonical import canonical_json
from deepreason.ontology import Artifact, Interface, Provenance, Ref, Rule
from deepreason.ontology.artifact import RefRole
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
from deepreason.skills.models import (
    AdoptionEvaluation,
    AdoptionResult,
    SkillCapsule,
)


class CapsuleDependenceError(ValueError):
    """A capsule was incorrectly presented as support or evidence."""


def capsule_ref(capsule_artifact_id: str, role: RefRole | str = RefRole.MENTION) -> Ref:
    normalized = RefRole(role)
    if normalized != RefRole.MENTION:
        raise CapsuleDependenceError("skill capsules may only be mentioned, never depended on")
    return Ref(target=capsule_artifact_id, role=RefRole.MENTION)


def validate_capsule_refs(artifact_or_interface, capsule_artifact_ids: Iterable[str]) -> None:
    interface = (
        artifact_or_interface.interface
        if isinstance(artifact_or_interface, Artifact)
        else artifact_or_interface
    )
    capsule_ids = set(capsule_artifact_ids)
    for ref in interface.refs:
        if ref.target in capsule_ids and ref.role != RefRole.MENTION:
            raise CapsuleDependenceError(
                f"capsule {ref.target} has forbidden {ref.role.value} reference"
            )


def import_capsule(harness, capsule: SkillCapsule) -> Artifact:
    """Register prior material as a plain import artifact with no authority."""

    return harness.create_artifact(
        canonical_json(capsule.model_dump(mode="json", by_alias=True)),
        codec="json",
        interface=Interface(),
        provenance=Provenance(role="import", event_seq=harness._next_seq),
        rule=Rule.REGISTER,
    )


def _check_toolchain(harness, capsule: SkillCapsule, commitment) -> None:
    kind, _, program_name = commitment.eval.partition(":")
    spec = programs.PROGRAMS.get(program_name) if kind == "program" else None
    if spec is None or spec.external_toolchain is None:
        return
    manifest_path = harness.root / MANIFEST_NAME
    if not manifest_path.exists():
        raise ValueError("adopted external commitment requires a current pinned toolchain")
    current = {
        (item.id, item.executable, item.version_output_sha256, item.lock_digest)
        for item in load_run_manifest(manifest_path).toolchains
    }
    source = {
        (item.id, item.executable, item.version_output_sha256, item.lock_digest)
        for item in capsule.toolchains
    }
    if not current.intersection(source):
        raise ValueError("adopted commitment toolchain differs from the current pinned run")


def adopt_commitments(
    harness,
    candidate: Artifact,
    capsule: SkillCapsule,
    commitment_refs: Iterable[str],
    *,
    evaluator: Callable | None = None,
    register: bool = True,
) -> AdoptionResult:
    """Bind exact definitions to a new candidate identity and rerun them now.

    The old pass result is absent from both the capsule and this API.  Every
    returned evaluation is recomputed against the current candidate bytes and
    current pinned toolchain.  A caller may supply the current verifier runner
    for external/formal commitments; ordinary deterministic programs use the
    canonical program evaluator.
    """

    requested = tuple(dict.fromkeys(commitment_refs))
    if not requested:
        raise ValueError("commitment adoption must name at least one test")
    available = {item.id: item for item in capsule.passed_commitments}
    unknown = [item for item in requested if item not in available]
    if unknown:
        raise ValueError(f"commitments are absent from capsule: {unknown}")
    selected = [available[item] for item in requested]
    for record in selected:
        for closure_ref in record.closure_refs:
            if closure_ref not in harness.state.artifacts:
                raise ValueError(
                    f"adopted commitment closure is not imported in current run: {closure_ref}"
                )
        _check_toolchain(harness, capsule, record.definition)
        harness.register_commitment(record.definition)

    interface = Interface(
        commitments=list(dict.fromkeys((*candidate.interface.commitments, *requested))),
        refs=list(candidate.interface.refs),
    )
    adopted = Artifact(
        id=Artifact.compute_id(candidate.content_ref, candidate.codec, interface),
        content_ref=candidate.content_ref,
        codec=candidate.codec,
        interface=interface,
        provenance=Provenance(
            role=candidate.provenance.role,
            school=candidate.provenance.school,
            event_seq=harness._next_seq,
        ),
    )
    if register:
        harness.register_artifact(adopted, rule=Rule.REGISTER)

    evaluations: list[AdoptionEvaluation] = []
    for record in selected:
        commitment = record.definition
        if evaluator is None:
            verdict, trace = programs.evaluate(commitment, adopted, harness.blobs)
        else:
            verdict, trace = evaluator(commitment, adopted)
        if verdict not in {programs.PASS, programs.FAIL, programs.OVERRUN}:
            raise ValueError(f"current-run evaluator returned invalid verdict: {verdict}")
        trace_payload = {
            "schema": "deepreason-skill-adoption-trace-v1",
            "capsule_id": capsule.id,
            "source_candidate_id": candidate.id,
            "adopted_candidate_id": adopted.id,
            "commitment": commitment.model_dump(mode="json", by_alias=True),
            "verdict": verdict,
            "trace": trace,
        }
        trace_ref = harness.blobs.put(canonical_json(trace_payload))
        evaluations.append(
            AdoptionEvaluation(
                commitment_id=commitment.id,
                verdict=verdict,
                trace_ref=trace_ref,
            )
        )
        if register and verdict == programs.FAIL and commitment.eval.startswith(
            ("program:", "predicate:")
        ):
            from deepreason.rules.warrants import register_fail_warrant

            register_fail_warrant(
                harness,
                commitment_id=commitment.id,
                target_id=adopted.id,
                nu_content=(
                    f"nu: current-run adopted verdict of {commitment.id} on "
                    f"{adopted.id} is sound and relevant"
                ),
                critic_content=(
                    f"critic: adopted current-run commitment {commitment.id} "
                    f"failed on {adopted.id[:12]}"
                ),
                trace_ref=trace_ref,
                skip_if_on_record=True,
            )
    harness.record_measure(
        inputs=[
            "skills-adoption",
            capsule.id,
            candidate.id,
            adopted.id,
            *(f"{item.commitment_id}:{item.verdict}" for item in evaluations),
        ]
    )
    return AdoptionResult(
        source_capsule_id=capsule.id,
        source_candidate_id=candidate.id,
        adopted_candidate_id=adopted.id,
        commitment_ids=requested,
        evaluations=tuple(evaluations),
    )
