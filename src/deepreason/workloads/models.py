"""Shared workload process models.

These records compile model proposals into ordinary artifact interfaces.  They
are process metadata only and deliberately do not add an artifact or problem
type to the ontology.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from deepreason.ontology import Interface, Ref
from deepreason.ontology.artifact import RefRole


@dataclass(frozen=True)
class MandatoryInterface:
    """Harness-owned facts that a model is never required to repeat."""

    commitments: tuple[str, ...] = ()
    refs: tuple[str, ...] = ()


def _resolve_ref(target: str, artifacts: dict) -> str | None:
    if target in artifacts:
        return target
    matches = [artifact_id for artifact_id in artifacts if artifact_id.startswith(target)]
    return matches[0] if len(matches) == 1 else None


def compile_interface(
    harness,
    problem,
    content: str,
    *,
    mandatory: MandatoryInterface | None = None,
    optional_refs: Iterable[tuple[str, RefRole | str]] = (),
) -> Interface:
    """Compile criteria, safe content commitments, and refs before identity.

    Unknown model aliases are ignored at this boundary.  Missing mandatory
    facts are not a schema error because the harness owns and supplies them.
    """

    owned = mandatory or MandatoryInterface()
    commitments = [
        commitment_id
        for commitment_id in (*problem.criteria, *owned.commitments)
        if commitment_id in harness.commitments
    ]

    # Existing safe skeleton compilation remains the only route by which
    # model-authored counterconditions can add commitments.
    from deepreason.informal.skeleton import compile_forbidden_commitments, parse_skeleton

    skeleton = parse_skeleton(content)
    if skeleton is not None:
        for commitment_id in compile_forbidden_commitments(harness, skeleton):
            if commitment_id not in commitments:
                commitments.append(commitment_id)

    refs: list[Ref] = []
    seen: set[tuple[str, RefRole]] = set()
    for target in owned.refs:
        resolved = _resolve_ref(target, harness.state.artifacts)
        if resolved is None:
            raise ValueError(f"mandatory reference is not registered: {target}")
        key = (resolved, RefRole.DEPENDENCE)
        if key not in seen:
            refs.append(Ref(target=resolved, role=RefRole.DEPENDENCE))
            seen.add(key)
    for target, role in optional_refs:
        resolved = _resolve_ref(target, harness.state.artifacts)
        if resolved is None:
            continue
        normalized_role = RefRole(role)
        key = (resolved, normalized_role)
        if key not in seen:
            refs.append(Ref(target=resolved, role=normalized_role))
            seen.add(key)
    return Interface(commitments=list(dict.fromkeys(commitments)), refs=refs)
