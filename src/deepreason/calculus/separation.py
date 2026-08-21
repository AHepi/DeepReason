"""Frame-separation — Definitions 7.1/7.2 of the Formalization, and R64.

The mention law is NECESSARY BUT NOT SUFFICIENT for wound persistence. An
assertion that merely mentions its subject can still share an adjudication
component with it, and then a new attack on the subject reaches the assertion
through pre-existing paths and moves its label indirectly. Definition 7.2 is
the graph condition that closes that door.

Mention edges need no filtering out of Q_L: `build_dep` emits `dep` from
`RefRole.DEPENDENCE` and from nothing else, so the recorded graph already
excludes them. Nothing here is stored -- components are recomputed from
replayed state on every call, like every other mark in this codebase (C4).

SCOPE BOUNDARY (v2 calculus program, Rung 3b). Full frame assertions do not
exist until Rung 4: `poietic.frame-assertion.v1` stays declared-and-unbuilt,
there is no standing view, and there is no scope predicate. This module is the
predicate and the enforcement over the graph shapes current machinery can
build, so Rung 4's frame layer meets an invariant that already refuses. The
consequence, stated so it is not later read as an omission: `consultability`
has no caller in `src/` at this rung. Wiring it is Rung 4's, and applying it to
the premise channel's own consultation predicate is a separate open question
(`experiments/2026-08-21-change-rung3b-frame-separation/PARKED.md` P1).
"""

from __future__ import annotations

from dataclasses import dataclass

FRAME_NOT_SEPARATED = "frame-not-separated"
FRAME_ENDPOINT_UNREGISTERED = "frame-endpoint-unregistered"


@dataclass(frozen=True)
class Consultability:
    """R64's answer, and everything it is permitted to be.

    A failed engineering invariant is a reason to STOP TRUSTING a frame, never
    a reason to invent a defeat for it: a manufactured refutation would put a
    verdict nobody argued onto the graph, making the record lie about
    epistemics in order to report a bug. So the whole consequence of a
    violation is this value -- no attack edge, no warrant, no label change.

    `code` is branched on by value, never by message text, exactly as
    `ClaimDecodeError.code` is in this package.
    """

    consultable: bool
    code: str | None = None
    detail: tuple[str, ...] = ()


def _components(nodes, edges) -> dict[str, frozenset[str]]:
    """Undirected connected components. A node with no incident edge maps to
    the singleton `{node}` -- Definition 7.1 builds Q_L from the edge relation
    and leaves isolated vertices undiscussed, and the singleton is the only
    reading on which an empty graph is separated rather than an error."""
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for left, right in edges:
        adjacency.setdefault(left, set()).add(right)
        adjacency.setdefault(right, set()).add(left)
    found: dict[str, frozenset[str]] = {}
    for start in sorted(adjacency):
        if start in found:
            continue
        group: set[str] = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in group:
                continue
            group.add(node)
            stack.extend(adjacency[node] - group)
        component = frozenset(group)
        found.update(dict.fromkeys(group, component))
    return found


def _state_components(harness, *extra: str) -> dict[str, frozenset[str]]:
    return _components(
        set(harness.state.artifacts) | set(extra),
        list(harness.state.att) + list(harness.state.dep),
    )


def adjudication_component(harness, node: str) -> frozenset[str]:
    """Comp_L(x) -- Definition 7.1: the connected component of x in the graph
    obtained from att u dep by forgetting edge directions."""
    return _state_components(harness, node)[node]


def frame_separated(harness, assertion: str, subject: str) -> bool:
    """Definition 7.2: Comp_L(f) n Comp_L(b) = {}."""
    components = _state_components(harness, assertion, subject)
    return not components[assertion] & components[subject]


def consultability(harness, assertion: str, subject: str) -> Consultability:
    """R64. Derived, read-only, and the only consequence a violation has."""
    missing = tuple(
        sorted(n for n in (assertion, subject) if n not in harness.state.artifacts)
    )
    if missing:
        # "We could not check" must never look like "we checked and it was
        # fine": the literal component reading would call an assertion whose
        # subject does not exist separated, and therefore consultable.
        return Consultability(False, FRAME_ENDPOINT_UNREGISTERED, missing)
    components = _state_components(harness)
    shared = components[assertion] & components[subject]
    if shared:
        return Consultability(False, FRAME_NOT_SEPARATED, tuple(sorted(shared)))
    return Consultability(True)
