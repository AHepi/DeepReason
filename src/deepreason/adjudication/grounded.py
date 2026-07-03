"""Pass 1 — Dung grounded extension (spec §4).

    F(X) = { a in A : for all (b,a) in att, exists c in X with (c,b) in att }
    G    = least fixed point of F starting from the empty set

Unique, skeptical, polynomial. label0 in {accepted, refuted, suspended}.
Reinstatement (Lemma 3.1) falls out of this pass — it is derived, not a rule.
"""


def grounded_extension(nodes: set[str], att: list[tuple[str, str]]) -> set[str]:
    """Least fixed point of the characteristic function. TODO(P0)."""
    raise NotImplementedError


def label0(nodes: set[str], att: list[tuple[str, str]]) -> dict[str, str]:
    """accepted if in G; refuted if attacked from G; else suspended. TODO(P0)."""
    raise NotImplementedError
