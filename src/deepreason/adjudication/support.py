"""Pass 2 — support cascade over the dep DAG (spec §4).

Process in topological order (dependencies before dependents). Refuting a
premise makes dependents ``suspended_unsupported``, NOT refuted — orphaned
!= false. Attacking a relation artifact refutes the relation while its
endpoints may stay accepted.
"""

from deepreason.ontology.state import Status


def final_labels(
    label0: dict[str, str],
    dep: list[tuple[str, str]],
) -> dict[str, Status]:
    """Two-pass final labels; recompute after every registration. TODO(P0)."""
    raise NotImplementedError
