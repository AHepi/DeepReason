"""Pass 2 — support cascade over the dep DAG (spec §4).

Process in topological order (dependencies before dependents). Refuting a
premise makes dependents ``suspended_unsupported``, NOT refuted — orphaned
!= false. Attacking a relation artifact refutes the relation while its
endpoints may stay accepted.
"""

from collections.abc import Iterable

from deepreason.adjudication.edges import toposort
from deepreason.ontology.state import Status


def final_labels(
    label0: dict[str, str],
    dep_edges: Iterable[tuple[str, str]],
) -> dict[str, Status]:
    nodes = set(label0)
    dep_edges = set(dep_edges)
    deps: dict[str, list[str]] = {n: [] for n in nodes}
    for a, b in dep_edges:
        deps[a].append(b)
    final: dict[str, Status] = {}
    for a in toposort(nodes, dep_edges):
        supported = all(final[b] == Status.ACCEPTED for b in deps[a])
        if label0[a] == "accepted" and supported:
            final[a] = Status.ACCEPTED
        elif label0[a] == "accepted":
            final[a] = Status.SUSPENDED_UNSUPPORTED
        elif label0[a] == "refuted":
            final[a] = Status.REFUTED
        else:
            final[a] = Status.SUSPENDED
    return final
