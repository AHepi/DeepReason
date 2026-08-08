"""O1c — floating-foundation clusters on the dependence graph
(SPEC.md S8, GROUNDED_OVERLAY_PREPLAN.md Rung O1). Read-only.

`dep` is a DAG by construction (harness.register_batch refuses a
registration whose materialized edges would cycle it — DR-SUB-
adjudication's own "Where to change what" row), so "self-supporting
cluster" here is a weakly-connected component of the accepted-only
dependence subgraph whose transitive closure never reaches a GROUND
artifact (SPEC.md A5: Provenance.role in {SEED, IMPORT, USER}) —
including the vacuous case of an isolated accepted artifact with no
outgoing dependence ref at all, trivially "supported" by
adjudication/support.py's own vacuous all([])==True, without ever
resting on evidence or admission.
"""

import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from overlay_common import corpus, open_root  # noqa: E402

from deepreason.ontology.artifact import ProvenanceRole  # noqa: E402
from deepreason.ontology.state import Status  # noqa: E402

GROUND_ROLES = {ProvenanceRole.SEED, ProvenanceRole.IMPORT, ProvenanceRole.USER}


def is_ground(harness, aid) -> bool:
    art = harness.state.artifacts.get(aid)
    return art is not None and art.provenance.role in GROUND_ROLES


def weakly_connected_components(nodes: set, edges: set) -> list[set]:
    undirected: dict = defaultdict(set)
    for a, b in edges:
        undirected[a].add(b)
        undirected[b].add(a)
    seen: set = set()
    components: list[set] = []
    for start in nodes:
        if start in seen:
            continue
        comp = {start}
        stack = [start]
        seen.add(start)
        while stack:
            n = stack.pop()
            for m in undirected[n]:
                if m not in seen:
                    seen.add(m)
                    comp.add(m)
                    stack.append(m)
        components.append(comp)
    return components


def reaches_ground(harness, start, forward_deps: dict) -> bool:
    """Walk the transitive dependence closure of `start` (dependent ->
    dependency direction); True iff any node reached is ground."""
    seen: set = set()
    stack = [start]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        if is_ground(harness, n):
            return True
        stack.extend(forward_deps.get(n, ()))
    return False


def analyze_root(root: pathlib.Path) -> dict:
    harness = open_root(root)
    accepted = {
        aid for aid, status in harness.state.status.items() if status == Status.ACCEPTED
    }
    dep_a = {(x, y) for x, y in harness.state.dep if x in accepted and y in accepted}
    forward_deps: dict = defaultdict(list)
    for x, y in dep_a:
        forward_deps[x].append(y)
    # Isolated accepted artifacts (zero dep edges either way) are their
    # own singleton component too — the vacuous floating case.
    connected_nodes = {n for edge in dep_a for n in edge}
    isolated = accepted - connected_nodes
    components = weakly_connected_components(accepted, dep_a) if dep_a else []
    components += [{n} for n in isolated]

    floating = []
    for comp in components:
        grounded_reach = any(reaches_ground(harness, member, forward_deps) for member in comp)
        if not grounded_reach:
            floating.append(
                {
                    "members": sorted(comp),
                    "size": len(comp),
                    "kind": "isolated" if len(comp) == 1 else "chain",
                }
            )

    return {
        "root": str(root),
        "accepted_count": len(accepted),
        "dep_a_edge_count": len(dep_a),
        "component_count": len(components),
        "floating_components": floating,
    }


def main():
    for root in corpus():
        try:
            result = analyze_root(root)
        except Exception as error:  # noqa: BLE001 - a per-root failure must not kill the sweep
            print(f"{root} ERROR {type(error).__name__}: {error}")
            continue
        print(
            f"{root} accepted={result['accepted_count']} "
            f"dep_edges={result['dep_a_edge_count']} "
            f"components={result['component_count']} "
            f"floating={len(result['floating_components'])}"
        )


if __name__ == "__main__":
    main()
