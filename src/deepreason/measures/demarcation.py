"""Demarcation (spec §6) — replaces falsifiability.

    crit(a)   <=> a carries a SUBSTANTIVE commitment (nonempty attack surface)
    mod(a)    <=> Pr_{a'~mu(.|a)}[a' !~=_B a] > 0 (nontrivial variation surface)
    active(a) <=> crit(a) and mod(a)

Empirical falsifiability = special case of crit where a commitment is
observation-valued. Skeleton discipline (§10.1) makes crit real: forbid
nothing => empty attack surface => fails demarcation.

`interface.commitments != {}` is NOT the criterion, though the spec's shorthand
reads that way. A structural well-formedness program (`json-wf`, `skeleton_wf`,
`presupposition_wf`) passes for anything well formed and forbids nothing about
the subject, so counting it would let any artifact buy demarcation for the price
of a JSON check — the self-immunisation shape `rules/warrants.py::
formally_backed` already refuses for prose immunity, and `measures/reach.py`
already refuses for reach. One predicate, `reach._substantive`, decides all
three.
"""

from deepreason.measures.reach import _substantive


def crit(artifact, commitments) -> bool:
    """§6 crit: does this artifact forbid anything?

    ``commitments`` is the registry, because an interface holds commitment IDS
    and substantiveness is a property of the resolved Commitment. An id the
    registry does not know contributes nothing: an attack surface nobody can
    evaluate is not an attack surface.
    """
    return any(
        (kappa := commitments.get(cid)) is not None and _substantive(kappa)
        for cid in artifact.interface.commitments
    )


def mod(artifact, variator) -> bool:
    raise NotImplementedError
