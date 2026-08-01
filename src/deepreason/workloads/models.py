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
class MandatoryRef:
    """One harness-owned reference with an explicit epistemic role.

    Bare strings remain accepted by :class:`MandatoryInterface` as a legacy
    shorthand for a lineage dependence.  New contextual inputs must name
    their role so a memory mention can never silently become a dependency.
    """

    target: str
    role: RefRole | str = RefRole.DEPENDENCE

    def normalized_role(self) -> RefRole:
        return RefRole(self.role)


@dataclass(frozen=True)
class MandatoryInterface:
    """Harness-owned facts that a model is never required to repeat."""

    commitments: tuple[str, ...] = ()
    refs: tuple[MandatoryRef | str | tuple[str, RefRole | str], ...] = ()

    def role_refs(self) -> tuple[MandatoryRef, ...]:
        normalized: list[MandatoryRef] = []
        for value in self.refs:
            if isinstance(value, MandatoryRef):
                ref = value
            elif isinstance(value, str):
                # Compatibility with the original mandatory-interface API:
                # its only use was mechanically enforced lineage.
                ref = MandatoryRef(target=value, role=RefRole.DEPENDENCE)
            else:
                target, role = value
                ref = MandatoryRef(target=target, role=role)
            normalized.append(
                MandatoryRef(target=ref.target, role=ref.normalized_role())
            )
        return tuple(normalized)

    def domain_refs(self) -> tuple[str, ...]:
        """Role-qualified process identities for anti-relapse scoping."""
        return tuple(
            f"{ref.normalized_role().value}:{ref.target}"
            for ref in self.role_refs()
        )


def _resolve_ref(target: str, artifacts: dict) -> str | None:
    if target in artifacts:
        return target
    matches = [artifact_id for artifact_id in artifacts if artifact_id.startswith(target)]
    return matches[0] if len(matches) == 1 else None


def compile_interface_draft(
    harness,
    problem,
    content: str,
    *,
    mandatory: MandatoryInterface | None = None,
    optional_refs: Iterable[tuple[str, RefRole | str]] = (),
    draft_commitments: Iterable = (),
) -> tuple[Interface, list]:
    """Compile the prospective interface WITHOUT touching the registry.

    Returns (interface, unregistered Commitment objects). The interface is
    identical to what :func:`compile_interface` would produce; the caller
    registers the returned drafts only after gate admission (RC5: a blocked
    proposal must not mutate the commitment registry or emit Register
    events). ``draft_commitments`` lets a caller thread additional
    pre-compiled unregistered Commitments (e.g. reasoning counterconditions)
    through the same interface/identity path.

    Unknown model aliases are ignored at this boundary. Missing mandatory
    facts are not a schema error because the harness owns and supplies them.
    """

    owned = mandatory or MandatoryInterface()
    drafts: dict[str, object] = {}
    for commitment in draft_commitments:
        drafts.setdefault(commitment.id, commitment)
    commitments = [
        commitment_id
        for commitment_id in (*problem.criteria, *owned.commitments)
        if commitment_id in harness.commitments or commitment_id in drafts
    ]

    # Safe skeleton compilation remains the only route by which model-
    # authored counterconditions can add commitments. Drafted, not
    # registered: registration is the caller's post-admission step.
    from deepreason.informal.skeleton import draft_forbidden_commitments, parse_skeleton

    skeleton = parse_skeleton(content)
    if skeleton is not None:
        for commitment in draft_forbidden_commitments(skeleton):
            drafts.setdefault(commitment.id, commitment)
            if commitment.id not in commitments:
                commitments.append(commitment.id)

    refs: list[Ref] = []
    seen: set[tuple[str, RefRole]] = set()
    for mandatory_ref in owned.role_refs():
        resolved = _resolve_ref(mandatory_ref.target, harness.state.artifacts)
        if resolved is None:
            raise ValueError(
                f"mandatory reference is not registered: {mandatory_ref.target}"
            )
        role = mandatory_ref.normalized_role()
        key = (resolved, role)
        if key not in seen:
            refs.append(Ref(target=resolved, role=role))
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
    interface = Interface(commitments=list(dict.fromkeys(commitments)), refs=refs)
    unregistered = [
        drafts[cid]
        for cid in interface.commitments
        if cid in drafts and cid not in harness.commitments
    ]
    return interface, unregistered


def compile_interface(
    harness,
    problem,
    content: str,
    *,
    mandatory: MandatoryInterface | None = None,
    optional_refs: Iterable[tuple[str, RefRole | str]] = (),
) -> Interface:
    """Compile criteria, safe content commitments, and refs before identity.

    Single-phase spelling for callers that register unconditionally: drafts
    the interface, then registers the forbidden-case commitments at once.
    Gated callers use :func:`compile_interface_draft` and register only
    after admission.
    """
    interface, drafts = compile_interface_draft(
        harness, problem, content, mandatory=mandatory, optional_refs=optional_refs
    )
    for commitment in drafts:
        harness.register_commitment(commitment)
    return interface
