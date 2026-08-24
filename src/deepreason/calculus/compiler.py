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
from deepreason.calculus.claims import (
    DepartureDeclarationV1,
    DerivationManifestV1,
    FrameAssertionV1,
    PremiseAttributionV1,
    ProblemSubjectV1,
    ReachCertificateV1,
)
from deepreason.ontology import Interface, Ref
from deepreason.ontology.artifact import RefRole


def compile_interface(body) -> Interface:
    """Body -> Interface. Raises on a body this compiler has no rule for."""
    from deepreason.calculus.programs import (
        DEPARTURE_DECLARATION_COMMITMENT,
        DERIVATION_MANIFEST_COMMITMENT,
        FRAME_ASSERTION_COMMITMENT,
        PREMISE_ATTRIBUTION_COMMITMENT,
        PROBLEM_SUBJECT_COMMITMENT,
        REACH_CERTIFICATE_COMMITMENT,
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
        if body.citation_ref is not None:
            # DEPENDENCE, and the reason is R62's fourth layer: an attribution
            # that cites admitted evidence should lose its support when that
            # evidence record falls. The premise stays a MENTION either way —
            # this adds a support edge, it does not weaken the mention law.
            refs.append(Ref(target=body.citation_ref, role=RefRole.DEPENDENCE))
        if body.derivation_manifest_ref is not None:
            # The manifest IS load-bearing for the attribution: if what the
            # attribution was derived from falls, the attribution should lose
            # its support. That is a dependence.
            refs.append(
                Ref(target=body.derivation_manifest_ref, role=RefRole.DEPENDENCE)
            )
        return Interface(
            commitments=[PREMISE_ATTRIBUTION_COMMITMENT.id], refs=refs
        )
    if isinstance(body, FrameAssertionV1):
        refs = [
            # MENTION, and this single assignment IS the separation of the two
            # axes (Law 9.4). Because the assertion merely mentions its
            # subject, pass two does not drag it down when the subject is
            # refuted -- the wound does not touch the frame role.
            Ref(target=body.subject_ref, role=RefRole.MENTION),
        ]
        refs += [
            # DEPENDENCE on each reach record cited as the case: refuting the
            # case cuts the assertion's support, which is what makes
            # revocation need no rule of its own (S-10).
            Ref(target=case, role=RefRole.DEPENDENCE)
            for case in body.reach_case_refs
        ]
        refs += [
            # MENTION on an incumbent's wounds (Def 9.2). A dependence would
            # suspend the successor the moment a wound was reinstated away.
            Ref(target=wound, role=RefRole.MENTION)
            for wound in body.succeeded_wound_refs
        ]
        return Interface(commitments=[FRAME_ASSERTION_COMMITMENT.id], refs=refs)
    if isinstance(body, DepartureDeclarationV1):
        # TWO MENTIONS AND NOTHING ELSE, and this assignment IS L-4. A
        # dependence either way would give the declaration a support edge, and
        # pass two would then move a label because a departure was declared --
        # a penalty channel arriving through the graph rather than through a
        # rule anyone wrote. With two mentions there is no edge to carry one:
        # nothing scores departures because nothing CAN.
        #
        # The direction that looks safe is the one to refuse hardest. Depending
        # on the departing artifact would suspend the declaration the moment
        # the candidate was refuted, deleting the record of what it broke with
        # at exactly the moment a reader wants it.
        return Interface(
            commitments=[DEPARTURE_DECLARATION_COMMITMENT.id],
            refs=[
                Ref(target=body.subject_ref, role=RefRole.MENTION),
                Ref(target=body.departing_ref, role=RefRole.MENTION),
            ],
        )
    if isinstance(body, DerivationManifestV1):
        refs = [
            # MENTION on the subject, for the mention law's own reason: a
            # manifest that DEPENDED on the judgment it accounts for would be
            # suspended by pass two the moment that judgment's subject fell --
            # i.e. exactly when a reader wants the bill of materials.
            Ref(target=body.subject_ref, role=RefRole.MENTION),
        ]
        refs += [
            # DEPENDENCE, and this is the whole attackable half of proof debt:
            # `edges.py`'s evidence closure walks dependence lineage from the
            # validity node, so a certificate reached this way is an item a
            # critic can actually attack. Neither kernel checks nor axiom debt
            # gets an edge -- a kernel check is re-derived, and an axiom has no
            # attack surface by construction.
            Ref(target=certificate, role=RefRole.DEPENDENCE)
            for certificate in body.open_certificate_refs
        ]
        return Interface(commitments=[DERIVATION_MANIFEST_COMMITMENT.id], refs=refs)
    if isinstance(body, ReachCertificateV1):
        # MENTION on the subject and NOTHING else. A certificate is a frozen
        # READING of the record, not a claim resting on artifacts: a dependence
        # would suspend it by pass two at exactly the moment a promotion
        # criterion needed to read the input it froze. The subject is mentioned
        # for the mention law's own reason -- a wound to the subject must not
        # drag down the evidence about how far it reached.
        return Interface(
            commitments=[REACH_CERTIFICATE_COMMITMENT.id],
            refs=[Ref(target=body.subject_ref, role=RefRole.MENTION)],
        )
    raise claims.ClaimDecodeError(
        "claim-no-compiler-rule", type(body).__name__
    )
