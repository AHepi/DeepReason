"""Shared perturbation machinery for the flip-rate batteries.

Labels are always recomputed through the COMMITTED adjudication functions —
``label0`` (Dung grounded extension, pass 1) and ``final_labels`` (support
cascade, pass 2) — never a reimplementation. Only the ``att`` relation handed
to them is perturbed, and only on an in-memory copy.

Two reachability cones are carried, because DeepReason's verdict is not a
Dung labelling:

  * ``att``  — the Dung cone. Baroni & Giacomin directionality bounds pass-1
    label changes to the nodes reachable from the perturbed edge's head along
    attack edges. This is the cone the Q3 note's `[INFERRED]` claim is about.
  * ``full`` — the att cone plus REVERSED ``dep`` edges. Pass 2 demotes a
    dependent when its premise falls, so status travels up the support DAG,
    which Dung's framework does not model at all.

Distances are measured from the perturbed edge's HEAD (distance 0). For an
edge ``(x, y)`` the head is ``y``: adding or deleting an edge INTO ``y``
cannot change any distance measured FROM ``y`` (the edge points the wrong
way to be used on such a path), so one base BFS per node serves every
perturbation of that root — this is why the batteries are exhaustive rather
than sampled.
"""

from collections import deque

from deepreason.adjudication.grounded import label0
from deepreason.adjudication.support import final_labels

PASS1 = ("accepted", "refuted", "suspended")


def labels_of(nodes, att, dep):
    """(pass-1 string labels, pass-2 Status values) — the committed path."""
    l0 = label0(nodes, att)
    return l0, {k: v.value for k, v in final_labels(l0, dep).items()}


def _bfs(source, adj):
    dist = {source: 0}
    q = deque([source])
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def cone_distances(nodes, att, dep):
    """Per-source distance maps for both cones, on the BASE graph."""
    att_adj: dict[str, list[str]] = {}
    for u, v in att:
        att_adj.setdefault(u, []).append(v)
    full_adj = {u: list(vs) for u, vs in att_adj.items()}
    for a, b in dep:  # a depends on b; a demotion travels b -> a
        full_adj.setdefault(b, []).append(a)
    return (
        {n: _bfs(n, att_adj) for n in nodes},
        {n: _bfs(n, full_adj) for n in nodes},
    )


def diff_case(base_l0, base_final, new_l0, new_final, head, d_att, d_full):
    """Classify one perturbation's flips.

    A pass-1 flip is a change in the grounded labelling itself. A pass-2 flip
    is a node whose Status moved while its pass-1 label did not — the support
    cascade, which is where DeepReason exceeds Dung.
    """
    flips = []
    for node, before in base_final.items():
        after = new_final[node]
        if after == before:
            continue
        p1 = base_l0[node] != new_l0[node]
        flips.append({
            "node": node,
            "before": before,
            "after": after,
            "pass": 1 if p1 else 2,
            "d_att": d_att[head].get(node),
            "d_full": d_full[head].get(node),
        })
    return flips
