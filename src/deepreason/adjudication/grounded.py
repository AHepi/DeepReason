"""Pass 1 — Dung grounded extension (spec §4).

    F(X) = { a in A : for all (b,a) in att, exists c in X with (c,b) in att }
    G    = least fixed point of F starting from the empty set

Unique, skeptical, polynomial (Kleene iteration of the monotone F).
Reinstatement (Lemma 3.1) falls out of this pass — derived, not a rule.
"""

from collections.abc import Iterable


def grounded_extension(nodes: set[str], att: Iterable[tuple[str, str]]) -> set[str]:
    attackers: dict[str, set[str]] = {n: set() for n in nodes}
    for x, target in att:
        if target in attackers:
            attackers[target].add(x)
    g: set[str] = set()
    while True:
        nxt = {a for a in nodes if all(g & attackers[b] for b in attackers[a])}
        if nxt == g:
            return g
        g = nxt


def label0(nodes: set[str], att: Iterable[tuple[str, str]]) -> dict[str, str]:
    """accepted if in G; refuted if attacked from G; else suspended."""
    att = set(att)
    g = grounded_extension(nodes, att)
    labels: dict[str, str] = {}
    for a in nodes:
        if a in g:
            labels[a] = "accepted"
        elif any((b, a) in att for b in g):
            labels[a] = "refuted"
        else:
            labels[a] = "suspended"
    return labels
