"""Canonical skeleton commitments and deterministic program checks.

MiniReason owns no skeleton parser, commitment constructor, predicate guard,
or program registry. It retains only the reduced policy of immediately
executing model-visible program commitments and turning failures into the
shared fail-warrant plumbing in :mod:`minireason.loop`.
"""

from deepreason import programs
from deepreason.informal.skeleton import (
    SKELETON_WF_ID,
    ForbiddenCase,
    Scope,
    Skeleton,
    forbidden_commitment,
    parse_skeleton,
    skeleton_wf_commitment,
)
from deepreason.ontology import Artifact, Commitment, Interface, Provenance

# Historical Mini imports remain valid, but their implementations are the
# canonical ones. They are useful for direct trusted predicate diagnostics;
# model-authored Skeleton.forbidden values reject ``predicate:`` upstream.
UnsafePredicate = programs.UnsafePredicate
_validate_predicate = programs._validate_predicate
PROGRAMS = programs.PROGRAMS


def _artifact(text: str, commitments: list[str], codec: str = "utf8") -> Artifact:
    interface = Interface(commitments=commitments)
    content_ref = f"inline:{text}"
    return Artifact(
        id=Artifact.compute_id(content_ref, codec, interface),
        content_ref=content_ref,
        codec=codec,
        interface=interface,
        provenance=Provenance(role="user"),
    )


def evaluable(eval_spec: str) -> bool:
    """Compatibility wrapper around the canonical registry predicate."""
    return programs.evaluable(Commitment(id="mini-eval", eval=eval_spec))


def evaluate(eval_spec: str, text: str, codec: str = "utf8") -> tuple[str, dict]:
    """Evaluate through ``deepreason.programs`` while preserving Mini's API."""
    commitment = Commitment(id="mini-eval", eval=eval_spec)
    verdict, trace = programs.evaluate(
        commitment,
        _artifact(text, [commitment.id], codec),
        blobs=None,
    )
    detail = {
        key: value
        for key, value in trace.items()
        if key not in {"commitment", "eval", "verdict"}
    }
    return verdict, detail


def forbidden_commitment_id(case: ForbiddenCase) -> str:
    """Delegate deterministic identity to the canonical constructor."""
    return forbidden_commitment(case).id


def compile_checks(text: str) -> list[dict]:
    """Compile canonical commitments without registering them.

    Rubric cases remain in the returned records so Session can apply the
    manifest preflight and drop the complete candidate before registration.
    """
    commitments = [skeleton_wf_commitment()]
    skeleton = parse_skeleton(text)
    if skeleton is not None:
        commitments.extend(forbidden_commitment(case) for case in skeleton.forbidden)
    return [
        commitment.model_dump(mode="json", by_alias=True)
        for commitment in commitments
    ]


def run_checks(text: str, checks: list[dict], codec: str = "utf8") -> list[dict]:
    """Execute canonical program/predicate semantics and return fail traces."""
    commitments = [Commitment.model_validate(check) for check in checks]
    artifact = _artifact(text, [commitment.id for commitment in commitments], codec)
    failures: list[dict] = []
    for commitment in commitments:
        if not programs.evaluable(commitment):
            continue
        verdict, trace = programs.evaluate(commitment, artifact, blobs=None)
        if verdict == programs.FAIL:
            failures.append(trace)
    return failures


__all__ = [
    "ForbiddenCase",
    "PROGRAMS",
    "SKELETON_WF_ID",
    "Scope",
    "Skeleton",
    "UnsafePredicate",
    "compile_checks",
    "evaluable",
    "evaluate",
    "forbidden_commitment_id",
    "parse_skeleton",
    "run_checks",
]
