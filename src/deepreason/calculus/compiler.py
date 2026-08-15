"""The ONLY place a claim body becomes an `Interface`.

The reason this is one function and not a method on each body: ref roles are
SEMANTICS, and a model that proposes a body must never be able to propose what
its endpoints mean. `mention`, `dependence` and `evidence` decide whether an
attack propagates, whether pass two suspends the claim, and whether an attacker
of the evidence is lifted onto a validity node. A body says WHAT it relates;
the controller says HOW.

The generic synthesizer is deliberately not reused: it compiles every connected
endpoint as `DEPENDENCE`, which is exactly wrong for an attribution and is why
the advice says to add dedicated authoring operations rather than teach the
synthesizer to guess.
"""

from __future__ import annotations

from deepreason.calculus import claims
from deepreason.calculus.claims import PremiseAttributionV1, ProblemSubjectV1
from deepreason.ontology import Interface, Ref
from deepreason.ontology.artifact import RefRole


def compile_interface(body) -> Interface:
    """Body -> Interface. Raises on a body this compiler has no rule for."""
    from deepreason.calculus.programs import (
        PREMISE_ATTRIBUTION_COMMITMENT,
        PROBLEM_SUBJECT_COMMITMENT,
    )

    if isinstance(body, ProblemSubjectV1):
        # No refs at all. A problem subject speaks FOR its problem and rests on
        # nothing: giving it a dependence would let an unrelated fall suspend
        # the one artifact through which the problem can be criticised.
        return Interface(commitments=[PROBLEM_SUBJECT_COMMITMENT.id], refs=[])
    if isinstance(body, PremiseAttributionV1):
        refs = [
            Ref(target=body.problem_subject_ref, role=RefRole.MENTION),
            # MENTION, never DEPENDENCE. Law 9.4': if the attribution depended
            # on the premise, pass two would suspend it the moment the premise
            # fell, erasing the relation that identifies the orphan.
            Ref(target=body.premise_ref, role=RefRole.MENTION),
        ]
        if body.derivation_manifest_ref is not None:
            # The manifest IS load-bearing for the attribution: if what the
            # attribution was derived from falls, the attribution should lose
            # its support. That is a dependence, and the only one here.
            refs.append(
                Ref(target=body.derivation_manifest_ref, role=RefRole.DEPENDENCE)
            )
        return Interface(
            commitments=[PREMISE_ATTRIBUTION_COMMITMENT.id], refs=refs
        )
    raise claims.ClaimDecodeError(
        "claim-no-compiler-rule", type(body).__name__
    )
