"""Demarcation (spec §6) — replaces falsifiability.

    crit(a)   <=> interface.commitments != {}     (nonempty attack surface)
    mod(a)    <=> Pr_{a'~mu(.|a)}[a' !~=_B a] > 0 (nontrivial variation surface)
    active(a) <=> crit(a) and mod(a)

Empirical falsifiability = special case of crit where a commitment is
observation-valued. Skeleton discipline (§10.1) makes crit real: forbid
nothing => empty attack surface => fails demarcation.
"""


def crit(artifact) -> bool:
    raise NotImplementedError


def mod(artifact, variator) -> bool:
    raise NotImplementedError
