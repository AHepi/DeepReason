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
    """§6 mod: is there anything here that could have been otherwise?

    ``variator`` supplies BOTH halves of Def 3.6 — the kernel µ(·|a) that
    samples neighbours and the equivalence relation ≈_B that decides whether a
    neighbour is a different claim or the same claim reworded. They travel
    together because a variation surface is only nontrivial RELATIVE to what
    counts as the same explanation; splitting them across two callers is how a
    rename starts counting as a variation.

    A sampled predicate, not a proof: no edits sampled means no evidence of a
    variation surface, which is reported as False rather than dressed up as a
    finding. Whoever acts on it owes the record the sample it rested on.
    """
    text, edits = variator.sample(artifact)
    return any(not variator.equivalent(text, edit) for edit in edits)


def active(artifact, commitments, variator) -> bool:
    """§6 active(a) <=> crit(a) and mod(a) — the demarcation criterion whole.

    The two halves are independent readings and that is the point: `crit`
    reads the declared attack surface, `mod` reads whether the content varies
    into anything different. A claim can fail one and pass the other, and only
    a claim that fails BOTH forbids nothing under either reading.
    """
    return crit(artifact, commitments) and mod(artifact, variator)
