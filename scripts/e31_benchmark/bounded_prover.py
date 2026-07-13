"""Deterministic bounded forward-chaining prover over generated axiom systems.

Pure Python, no LLM, no randomness, hard step limits (E3.1 class 1
"nontriviality certified by failure of a bounded brute-force prover").

Terms are immutable tuples:

    ("v", name)              pattern variable (binds to any term)
    ("c", name)              uninterpreted constant (includes skolemized
                             target variables, spelled "#<var>")
    ("f", op, (arg, ...))    operator application

An axiom is a pair ``(lhs, rhs)`` of terms read as a universally quantified
equation.  The prover treats every axiom as a rewrite rule in each
variable-safe orientation and runs breadth-first search from the skolemized
left-hand side of the target equation, looking for the skolemized right-hand
side.  All search is bounded by an explicit :class:`Budget` (BFS depth,
expanded-node count, term size).

Definitions used by the benchmark:

- **depth** of a proved target = length of the shortest rewrite chain found
  (the minimal-derivation-length estimate used for grading; exact within the
  budget whenever the search was not truncated);
- **difficulty certificate**: a target is *nontrivial* iff the prover fails
  at ``B_small`` but a derivation exists at ``B_large``; both outcomes are
  recorded verbatim.

Soundness: every step applies an axiom instance at a subterm position, so a
"proved" outcome always corresponds to a genuine equational derivation (the
derivation chain is returned and replayable).  Completeness is deliberately
bounded — that boundedness is the instrument.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

Term = tuple  # ("v", name) | ("c", name) | ("f", op, (args...))

_SKOLEM_PREFIX = "#"


def var(name: str) -> Term:
    return ("v", name)


def const(name: str) -> Term:
    return ("c", name)


def app(op: str, *args: Term) -> Term:
    return ("f", op, tuple(args))


def term_size(term: Term) -> int:
    if term[0] in ("v", "c"):
        return 1
    return 1 + sum(term_size(argument) for argument in term[2])


def term_str(term: Term) -> str:
    if term[0] in ("v", "c"):
        return term[1]
    return term[1] + "(" + ", ".join(term_str(argument) for argument in term[2]) + ")"


def term_vars(term: Term) -> set[str]:
    if term[0] == "v":
        return {term[1]}
    if term[0] == "c":
        return set()
    names: set[str] = set()
    for argument in term[2]:
        names |= term_vars(argument)
    return names


def skolemize(term: Term) -> Term:
    """Freeze the target's free variables as fresh constants (sound: proving
    the equation over free constants proves the universal closure)."""
    if term[0] == "v":
        return ("c", _SKOLEM_PREFIX + term[1])
    if term[0] == "c":
        return term
    return ("f", term[1], tuple(skolemize(argument) for argument in term[2]))


def deskolemize(term: Term) -> Term:
    if term[0] == "c" and term[1].startswith(_SKOLEM_PREFIX):
        return ("v", term[1][len(_SKOLEM_PREFIX):])
    if term[0] in ("v", "c"):
        return term
    return ("f", term[1], tuple(deskolemize(argument) for argument in term[2]))


def term_to_json(term: Term) -> Any:
    if term[0] in ("v", "c"):
        return [term[0], term[1]]
    return ["f", term[1], [term_to_json(argument) for argument in term[2]]]


def term_from_json(payload: Any) -> Term:
    kind = payload[0]
    if kind in ("v", "c"):
        return (kind, payload[1])
    if kind != "f":
        raise ValueError(f"unknown term tag {kind!r}")
    return ("f", payload[1], tuple(term_from_json(item) for item in payload[2]))


def match(pattern: Term, term: Term, subst: dict[str, Term]) -> dict[str, Term] | None:
    if pattern[0] == "v":
        bound = subst.get(pattern[1])
        if bound is None:
            extended = dict(subst)
            extended[pattern[1]] = term
            return extended
        return subst if bound == term else None
    if pattern[0] == "c":
        return subst if term == pattern else None
    if term[0] != "f" or term[1] != pattern[1] or len(term[2]) != len(pattern[2]):
        return None
    for sub_pattern, argument in zip(pattern[2], term[2]):
        result = match(sub_pattern, argument, subst)
        if result is None:
            return None
        subst = result
    return subst


def substitute(pattern: Term, subst: dict[str, Term]) -> Term:
    if pattern[0] == "v":
        return subst[pattern[1]]
    if pattern[0] == "c":
        return pattern
    return ("f", pattern[1], tuple(substitute(argument, subst) for argument in pattern[2]))


@dataclass(frozen=True)
class Budget:
    """Hard limits; the prover never exceeds any of them."""

    max_depth: int
    max_nodes: int
    max_term_size: int

    def __post_init__(self) -> None:
        if self.max_depth <= 0 or self.max_nodes <= 0 or self.max_term_size <= 0:
            raise ValueError("prover budgets must be positive and finite")

    def to_json(self) -> dict[str, int]:
        return {
            "max_depth": self.max_depth,
            "max_nodes": self.max_nodes,
            "max_term_size": self.max_term_size,
        }


@dataclass(frozen=True)
class ProofOutcome:
    proved: bool
    depth: int | None
    nodes_expanded: int
    truncated: bool  # a bound (nodes/depth/term-size frontier) cut the search
    derivation: tuple[str, ...] | None  # term chain, source ... target

    def to_json(self) -> dict[str, Any]:
        return {
            "proved": self.proved,
            "depth": self.depth,
            "nodes_expanded": self.nodes_expanded,
            "truncated": self.truncated,
            "derivation": list(self.derivation) if self.derivation is not None else None,
        }


def prepare_rules(axioms: list[tuple[Term, Term]]) -> list[tuple[Term, Term]]:
    """Compile axioms into variable-safe rewrite orientations.

    An orientation ``p -> q`` is admitted only when ``vars(q) <= vars(p)``;
    the reverse of an absorption-like axiom would otherwise have to invent a
    binding for the dropped variable.
    """

    rules: list[tuple[Term, Term]] = []
    seen: set[tuple[Term, Term]] = set()
    for lhs, rhs in axioms:
        for source, target in ((lhs, rhs), (rhs, lhs)):
            if source[0] == "v":
                continue  # a bare-variable pattern rewrites everything to anything
            if not term_vars(target) <= term_vars(source):
                continue
            if (source, target) in seen or source == target:
                continue
            seen.add((source, target))
            rules.append((source, target))
    return rules


def _successors(term: Term, rules: list[tuple[Term, Term]], max_term_size: int) -> list[Term]:
    out: list[Term] = []

    def rebuild_root(new: Term) -> Term:
        return new

    def visit(node: Term, rebuild) -> None:
        for pattern, replacement in rules:
            subst = match(pattern, node, {})
            if subst is not None:
                candidate = rebuild(substitute(replacement, subst))
                if term_size(candidate) <= max_term_size:
                    out.append(candidate)
        if node[0] == "f":
            for index, argument in enumerate(node[2]):
                def rebuild_child(new: Term, index=index, node=node, rebuild=rebuild) -> Term:
                    return rebuild(
                        ("f", node[1], node[2][:index] + (new,) + node[2][index + 1:])
                    )

                visit(argument, rebuild_child)

    visit(term, rebuild_root)
    return sorted(set(out))


def _search(
    axioms: list[tuple[Term, Term]],
    source: Term,
    budget: Budget,
    target: Term | None,
) -> tuple[dict[Term, int], dict[Term, Term], int, bool, Term | None]:
    """Shared BFS core: distances, parents, nodes expanded, truncated, hit."""

    rules = prepare_rules(axioms)
    distances: dict[Term, int] = {source: 0}
    parents: dict[Term, Term] = {}
    frontier: list[Term] = [source]
    nodes_expanded = 0
    truncated = False
    depth = 0
    while frontier and depth < budget.max_depth:
        depth += 1
        next_frontier: list[Term] = []
        for node in frontier:
            if nodes_expanded >= budget.max_nodes:
                truncated = True
                return distances, parents, nodes_expanded, truncated, None
            nodes_expanded += 1
            for successor in _successors(node, rules, budget.max_term_size):
                if successor in distances:
                    continue
                distances[successor] = depth
                parents[successor] = node
                if target is not None and successor == target:
                    return distances, parents, nodes_expanded, truncated, successor
                next_frontier.append(successor)
        frontier = next_frontier
    if frontier:
        truncated = True  # the depth bound cut a live frontier
    return distances, parents, nodes_expanded, truncated, None


def _chain(source: Term, target: Term, parents: dict[Term, Term]) -> tuple[str, ...]:
    chain = [target]
    while chain[-1] != source:
        chain.append(parents[chain[-1]])
    return tuple(term_str(node) for node in reversed(chain))


def prove_equation(
    axioms: list[tuple[Term, Term]],
    lhs: Term,
    rhs: Term,
    budget: Budget,
) -> ProofOutcome:
    """Bounded proof search for the universal equation ``lhs = rhs``."""

    source = skolemize(lhs)
    target = skolemize(rhs)
    if source == target:
        return ProofOutcome(True, 0, 0, False, (term_str(source),))
    distances, parents, nodes, truncated, hit = _search(axioms, source, budget, target)
    if hit is not None:
        return ProofOutcome(True, distances[hit], nodes, truncated, _chain(source, hit, parents))
    return ProofOutcome(False, None, nodes, truncated, None)


def reachable_ball(
    axioms: list[tuple[Term, Term]],
    source: Term,
    budget: Budget,
) -> tuple[dict[Term, int], bool]:
    """Every term reachable from ``skolemize(source)`` with its minimal
    rewrite distance, plus whether any bound truncated the search (if not,
    distances are exact minimal derivation lengths within the term-size cap).
    """

    distances, _parents, _nodes, truncated, _hit = _search(
        axioms, skolemize(source), budget, None
    )
    return distances, truncated


def difficulty_certificate(
    axioms: list[tuple[Term, Term]],
    lhs: Term,
    rhs: Term,
    *,
    small: Budget,
    large: Budget,
) -> dict[str, Any]:
    """Certificate: nontrivial iff the prover fails at ``small`` but a
    derivation exists at ``large``.  Both runs are recorded verbatim."""

    outcome_small = prove_equation(axioms, lhs, rhs, small)
    outcome_large = prove_equation(axioms, lhs, rhs, large)
    return {
        "schema": "e31-difficulty-certificate-v1",
        "statement": f"forall vars: {term_str(lhs)} = {term_str(rhs)}",
        "lhs": term_to_json(lhs),
        "rhs": term_to_json(rhs),
        "budget_small": small.to_json(),
        "budget_large": large.to_json(),
        "outcome_small": outcome_small.to_json(),
        "outcome_large": outcome_large.to_json(),
        "nontrivial": (not outcome_small.proved) and outcome_large.proved,
        "depth": outcome_large.depth,
    }
