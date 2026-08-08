"""O1a — grounded-vs-preferred semantics diff + attack-graph SCC
controversy inventory (SPEC.md S5/S6, GROUNDED_OVERLAY_PREPLAN.md Rung
O1). Read-only: opens roots only via overlay_common.open_root.

Algorithm (SPEC.md S5, derived from Dung 1995's own theorem that the
grounded extension is a subset of every complete extension): a
preferred extension can only ever DIFFER from the grounded extension G
on the nodes label0 leaves "suspended" — no attack edge crosses between
a label0-decided node and a suspended one (proved by label0's own
definition: a node attacked by G is "refuted", not "suspended"; a node
that attacked into G would force G to defend against it, which would
make that attacker itself "refuted", not "suspended"). So preferred
extensions are computed only over the suspended sub-framework, bounded
per weakly-connected component with a typed TOO_LARGE stop.
"""

import itertools
import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from overlay_common import corpus, open_root  # noqa: E402

from deepreason.adjudication.grounded import grounded_extension, label0  # noqa: E402

TOO_LARGE_COMPONENT_NODES = 16
MAX_EXTENSIONS_REPORTED = 8


def tarjan_scc(nodes: set, edges: set) -> list[set]:
    """Iterative Tarjan SCC (no recursion — root graphs may be large)."""
    adj: dict = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
    index_counter = itertools.count()
    indices: dict = {}
    lowlink: dict = {}
    on_stack: dict = {}
    stack: list = []
    sccs: list[set] = []

    for start in nodes:
        if start in indices:
            continue
        work = [(start, iter(adj[start]))]
        indices[start] = lowlink[start] = next(index_counter)
        stack.append(start)
        on_stack[start] = True
        while work:
            v, it = work[-1]
            advanced = False
            for w in it:
                if w not in indices:
                    indices[w] = lowlink[w] = next(index_counter)
                    stack.append(w)
                    on_stack[w] = True
                    work.append((w, iter(adj[w])))
                    advanced = True
                    break
                elif on_stack.get(w):
                    lowlink[v] = min(lowlink[v], indices[w])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[v])
            if lowlink[v] == indices[v]:
                comp = set()
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    comp.add(w)
                    if w == v:
                        break
                sccs.append(comp)
    return sccs


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


def admissible_and_preferred(nodes: list, edges: set):
    """Brute-force every subset of `nodes` (bounded by the caller's own
    TOO_LARGE gate); return the preferred (maximal admissible) sets."""
    attackers: dict = {n: {a for a, b in edges if b == n} for n in nodes}

    def conflict_free(s: frozenset) -> bool:
        return not any((a, b) in edges for a in s for b in s)

    def defended(s: frozenset, n) -> bool:
        return all(any((c, a) in edges and c in s for c in nodes) for a in attackers[n])

    def admissible(s: frozenset) -> bool:
        return conflict_free(s) and all(defended(s, n) for n in s)

    adm = []
    for r in range(len(nodes) + 1):
        for combo in itertools.combinations(nodes, r):
            s = frozenset(combo)
            if admissible(s):
                adm.append(s)
    preferred = [s for s in adm if not any(s < t for t in adm)]
    return preferred


def analyze_root(root: pathlib.Path) -> dict:
    harness = open_root(root)
    nodes = set(harness.state.artifacts)
    att = set(tuple(e) for e in harness.state.att)
    node_count, edge_count = len(nodes), len(att)  # PASTE before computing (guardrail)

    labels0 = label0(nodes, att)
    g = grounded_extension(nodes, att)

    sccs = tarjan_scc(nodes, att)
    scc_edge_count = lambda comp: sum(1 for a, b in att if a in comp and b in comp)  # noqa: E731
    controversy = [
        {"members": sorted(comp), "size": len(comp), "edges": scc_edge_count(comp)}
        for comp in sccs
        if (len(comp) > 1 or any((a, a) in att for a in comp))
        and any(labels0[a] == "suspended" for a in comp)
    ]

    undecided = {a for a in nodes if labels0[a] == "suspended"}
    undecided_att = {(a, b) for a, b in att if a in undecided and b in undecided}
    components = weakly_connected_components(undecided, undecided_att)

    component_reports = []
    skeptical_not_grounded: set = set()
    for comp in components:
        comp_edges = {(a, b) for a, b in undecided_att if a in comp and b in comp}
        report = {"nodes": len(comp), "edges": len(comp_edges)}
        if len(comp) > TOO_LARGE_COMPONENT_NODES:
            report["status"] = "TOO_LARGE"
            report["member_sample"] = sorted(comp)[:5]
        else:
            preferred = admissible_and_preferred(sorted(comp), comp_edges)
            report["status"] = "OK"
            report["preferred_extension_count"] = len(preferred)
            shown = preferred[:MAX_EXTENSIONS_REPORTED]
            report["preferred_extensions_sample"] = [sorted(p) for p in shown]
            if len(preferred) > MAX_EXTENSIONS_REPORTED:
                report["preferred_extensions_omitted"] = len(preferred) - MAX_EXTENSIONS_REPORTED
            if preferred:
                intersection = set(preferred[0])
                for p in preferred[1:]:
                    intersection &= set(p)
                skeptical_not_grounded |= intersection
        component_reports.append(report)

    return {
        "root": str(root),
        "node_count": node_count,
        "att_edge_count": edge_count,
        "controversy_sccs": controversy,
        "undecided_count": len(undecided),
        "components": component_reports,
        "skeptical_accepted_not_grounded": sorted(skeptical_not_grounded),
    }


def main():
    for root in corpus():
        try:
            result = analyze_root(root)
        except Exception as error:  # noqa: BLE001 - a per-root failure must not kill the sweep
            print(f"{root} ERROR {type(error).__name__}: {error}")
            continue
        print(
            f"{root} nodes={result['node_count']} att={result['att_edge_count']} "
            f"controversy_sccs={len(result['controversy_sccs'])} "
            f"undecided={result['undecided_count']} "
            f"components={len(result['components'])} "
            f"skeptical_not_grounded={len(result['skeptical_accepted_not_grounded'])}"
        )


if __name__ == "__main__":
    main()
