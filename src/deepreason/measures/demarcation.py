"""Demarcation — the Formalization §12.2, which supersedes §6's `active`.

    crit(a)          <=> K_a != {}            (the attack surface is nonempty)
    load_k(a)        <=> some ROLE VARIANT of a gets a DIFFERENT verdict vector
                          over B^-HV          (the mechanism is load-bearing)
    demarcated_k(a)  <=> crit(a) and load_k(a)

Two readings, and neither is the other. `crit` asks what an artifact DECLARES
could count against it; `load` asks whether the thing it claims actually does
any work — whether changing its mechanism changes what the battery says. The
pair is what makes the criterion informative about PROSE: prose declares little
and a declaration alone proves nothing, so a criterion resting on `crit` alone
fells everything written in words.

`crit` is deliberately the WEAK form, `K_a != {}`, and not "carries a
substantive commitment". The earlier design put substantiveness in `crit` to
close the self-immunisation hole — an artifact attaching `json-wf` to buy
demarcation. §12.2 closes the same hole in the other half and closes it better:
an artifact carrying only a well-formedness check has a nonempty K, but its
role-variants all pass that check too, so their verdict vectors agree, `load`
is false, and it is not demarcated. Substantiveness is a property the battery
EXHIBITS under variation rather than one the interface asserts.

`B^-HV` is the evaluation battery with hardness-to-vary commitments removed, so
a demarcation reading never consumes its own output (§12.2's own stratification,
the same move `measures/hv.py` makes for HV over a battery containing itself).

The Boolean view changes no label. A failed criterion MAY generate a
demonstrative warrant, and that registration is the caller's move, made through
the ordinary warrant path.
"""

from deepreason.measures.hv import _equivalence_battery, is_hv_floor


def crit(artifact, commitments) -> bool:
    """§12.2 crit: is the attack surface nonempty?

    Unregistered ids do not count: a commitment the registry cannot resolve is
    an attack surface nobody can evaluate, which is not one.
    """
    return any(cid in commitments for cid in artifact.interface.commitments)


def evaluation_battery(harness, artifact) -> list[str]:
    """B^-HV: the CURRENT evaluation battery, minus hardness-to-vary commitments.

    Current, not own. The artifact's own evaluable commitments come first, then
    other registered evaluable commitments — the same shape `measures/hv.py`
    uses for equivalence, for the same recorded reason: cross-problem criteria
    are what give a variant room to differ from an all-passing original. Read
    as "own only", the battery of a prose premise is empty, no variant can
    differ from it, and `load` would be false for every claim written in words —
    which would collapse demarcation back onto its first reading and undo the
    very repair §12.2 exists to make.

    HV-type commitments are removed. Stratification, not tidiness: a
    demarcation reading that consumed a hardness-to-vary verdict would be
    reading its own output back in.
    """
    return [
        cid
        for cid in _equivalence_battery(harness, artifact)
        if not is_hv_floor(harness.commitments[cid])
    ]


def load(artifact, variator) -> bool:
    """§12.2 load_k: does some ROLE VARIANT get a different verdict vector?

    `variator` supplies both halves of the reading — the kernel that samples
    variants and the verdict-vector comparison that decides whether a variant
    says something different. They travel together because a variation surface
    is only nontrivial relative to what counts as the same claim; split across
    two callers, a rename starts counting as a variation.

    A SAMPLED predicate over k variants, never a proof. §12.1 requires the
    kernel be replay-deterministic, and offers two ways to get there: a total
    seeded function, or logging the generated variants explicitly. The sampler
    used here takes the second, so the record carries the variants the reading
    rested on.
    """
    text, variants = variator.sample(artifact)
    return any(variator.role_variant_differs(text, variant) for variant in variants)


def demarcated(artifact, commitments, variator) -> bool:
    """§12.2 demarcated_k(a) = crit(a) and load_k(a).

    Supersedes `active(a) = crit(a) and mod(a)` from the Computable Calculus §6
    (operator, 2026-08-15: the Formalization supersedes previous decisions). The
    shape is the same; what changed is that `crit` is the weak declaration test
    and `load` carries the substantive work.
    """
    return crit(artifact, commitments) and load(artifact, variator)
