"""att/dep construction from interfaces (spec §1, §2).

- Each carried warrant => attack edge (carrier -> warrant.target).
- Each ``dependence`` ref => support edge (this -> target); dep must stay a
  DAG — a registration whose materialized edges would create a cycle is
  rejected (see harness).
- Validity-node closure: any attacker of a warrant's validity_node attacks
  the warrant — encoded as an attack on the warrant's carrier, which
  disables the carrier's attack edge in grounded semantics.
- Closure extension (case law, §1/§10.3): the nu of a rubric-derived warrant
  mentions the standard it applied; every registered attacker of that
  standard attacks the nu. Refute a standard => every nu citing it is
  attacked => every warrant under it falls => targets reinstate, all in
  pass 1.
- Source-artifact closure (proposed properties): a commitment minted from a
  PROPOSED artifact (e.g. an LLM-conjectured property checker) declares it
  as budget.extra["source_artifact"]; every attacker of that artifact
  attacks the nu of every warrant under the commitment. Refute the property
  => every verdict it produced falls => its victims reinstate. This is what
  makes LLM-proposed ground truth accountable: the verdicts stand exactly as
  long as their source does. (Generator credit is deliberately NOT load-
  bearing — a generator only chose where to look, so it is a MENTION on the
  nu with no closure.)

Edges materialize only when both endpoints are registered: refs/targets may
dangle (import/merge order, §14) and take effect when the target appears.
"""

import heapq
from collections.abc import Iterable

from deepreason.ontology.artifact import Artifact, RefRole
from deepreason.ontology.commitment import Commitment
from deepreason.ontology.warrant import Warrant


class DependenceCycleError(ValueError):
    """A dependence ref would make dep cyclic (forbidden, §1)."""


def build_dep(artifacts: dict[str, Artifact]) -> set[tuple[str, str]]:
    """Support edges (dependent -> dependency) from dependence refs."""
    edges: set[tuple[str, str]] = set()
    for a in artifacts.values():
        for ref in a.interface.refs:
            if ref.role == RefRole.DEPENDENCE and ref.target in artifacts:
                edges.add((a.id, ref.target))
    return edges


def toposort(nodes: set[str], dep_edges: Iterable[tuple[str, str]]) -> list[str]:
    """Dependencies-before-dependents order; deterministic (lexicographic
    tie-break); raises DependenceCycleError if dep is not a DAG."""
    deps: dict[str, set[str]] = {n: set() for n in nodes}
    rdeps: dict[str, set[str]] = {n: set() for n in nodes}
    for a, b in dep_edges:
        deps[a].add(b)
        rdeps[b].add(a)
    remaining = {n: len(deps[n]) for n in nodes}
    heap = sorted(n for n in nodes if remaining[n] == 0)
    heapq.heapify(heap)
    order: list[str] = []
    while heap:
        n = heapq.heappop(heap)
        order.append(n)
        for m in sorted(rdeps[n]):
            remaining[m] -= 1
            if remaining[m] == 0:
                heapq.heappush(heap, m)
    if len(order) != len(nodes):
        cyclic = sorted(n for n in nodes if remaining[n] > 0)
        raise DependenceCycleError(f"dep contains a cycle through: {cyclic}")
    return order


def build_att(
    artifacts: dict[str, Artifact],
    warrants: dict[str, Warrant],
    commitments: dict[str, Commitment],
) -> set[tuple[str, str]]:
    """Attack edges (attacker -> target) including both closure rules.

    Computed as a fixpoint: the case-law extension adds attackers of a
    standard as attackers of every nu citing it, which the validity-node
    closure then lifts onto the warrants' carriers.
    """
    att: set[tuple[str, str]] = set()
    carriers: dict[str, str] = {}  # warrant id -> carrier artifact id
    for a in artifacts.values():
        for wid in a.warrants:
            w = warrants.get(wid)
            if w is None:
                continue
            carriers[wid] = a.id
            if w.target in artifacts:
                att.add((a.id, w.target))

    changed = True
    while changed:
        changed = False
        for wid, carrier in carriers.items():
            w = warrants[wid]
            nu = w.validity_node
            # Case-law extension: attackers of the mentioned standard attack nu.
            kappa = commitments.get(w.commitment) if w.commitment else None
            if kappa is not None and kappa.eval.startswith("rubric:"):
                nu_artifact = artifacts.get(nu)
                if nu_artifact is not None:
                    standards = {
                        r.target
                        for r in nu_artifact.interface.refs
                        if r.role == RefRole.MENTION and r.target in artifacts
                    }
                    for x, target in list(att):
                        if target in standards and (x, nu) not in att:
                            att.add((x, nu))
                            changed = True
            # Source-artifact closure: attackers of the declared source
            # (a proposed property checker) attack the nu — refuting the
            # property collapses every verdict minted from it.
            if kappa is not None and kappa.budget.extra.get("source_artifact"):
                source = kappa.budget.extra["source_artifact"]
                if source in artifacts:
                    for x, target in list(att):
                        if target == source and (x, nu) not in att:
                            att.add((x, nu))
                            changed = True
            # Validity-node closure: attackers of nu attack the carrier.
            for x, target in list(att):
                if target == nu and (x, carrier) not in att:
                    att.add((x, carrier))
                    changed = True
    return att
