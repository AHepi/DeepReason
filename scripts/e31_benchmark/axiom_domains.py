"""Generator of fresh axiomatic systems for E3.1 class 1 (contamination-impossible).

Given a seed this module deterministically emits:

(a) a random signature of fresh uninterpreted symbols (nonsense names built
    from seeded syllables — nothing about them existed before 2026);
(b) 4–7 axioms drawn from parameterized schema templates (associativity-like,
    absorption-like, graded interaction rules, ...) with randomized operator
    assignments and orientations, so the system is structurally varied rather
    than a renaming of a known algebra;
(c) a Lean 4 rendering of the axioms as a ``class`` with theorem-statement
    skeletons, plus a validated :class:`PinnedLeanRequest`
    (src/deepreason/workloads/formal.py) pinning toolchain, source digest and
    target theorems per the pinned-Lean conventions of
    src/deepreason/verification/lean.py;
(d) a machine enumerator of candidate theorem statements at graded depth,
    where depth = minimal derivation length estimated by the bounded
    forward-chaining prover in ``bounded_prover``.

Everything is deterministic from the seed (``random.Random`` string seeding
uses sha512 and is stable across platforms and processes).
"""

from __future__ import annotations

import keyword
import random
from dataclasses import dataclass, field
from typing import Any

from deepreason.canonical import sha256_hex
from deepreason.workloads.formal import PinnedLeanRequest

from e31_benchmark.bounded_prover import (
    Budget,
    app,
    const,
    deskolemize,
    difficulty_certificate,
    prove_equation,
    reachable_ball,
    term_size,
    term_str,
    term_to_json,
    term_vars,
    var,
)

GENERATOR_VERSION = "e31-axiom-domains-v1"

# Pinned per repo convention (tests/test_workload_formal.py and the verifier
# registry pin lean4@4.19.0).
LEAN_TOOLCHAIN_ID = "lean4@4.19.0"
# Lean's standard propositional axioms; a proof from the class hypotheses may
# use these but nothing else (no sorryAx by construction of the request).
LEAN_ALLOWED_AXIOMS = ("propext", "Classical.choice", "Quot.sound")

# Default certificate budgets.  B_SMALL is the "shallow layer" a lookup-like
# solver gets for free; B_LARGE is the build-time grading horizon.
B_SMALL = Budget(max_depth=1, max_nodes=200, max_term_size=13)
B_LARGE = Budget(max_depth=5, max_nodes=1500, max_term_size=13)
_COLLAPSE_BUDGET = Budget(max_depth=4, max_nodes=1200, max_term_size=12)

_ONSETS = ("br", "dr", "fr", "gl", "gr", "kr", "m", "n", "pl", "qu", "sk", "sn", "thr", "v", "z")
_MIDDLES = ("a", "e", "i", "o", "u", "au", "ei", "or", "ar", "ul")
_CODAS = ("k", "l", "m", "n", "p", "r", "sh", "th", "v", "x")
_RESERVED = frozenset(keyword.kwlist) | {
    "theorem", "class", "structure", "def", "fun", "forall", "exists", "open",
    "universe", "variable", "axiom", "lemma", "instance", "where", "sorry",
}


@dataclass(frozen=True)
class Signature:
    class_name: str
    binary_ops: tuple[str, ...]
    unary_ops: tuple[str, ...]
    constants: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "class_name": self.class_name,
            "binary_ops": list(self.binary_ops),
            "unary_ops": list(self.unary_ops),
            "constants": list(self.constants),
        }


@dataclass(frozen=True)
class TheoremTarget:
    lean_name: str
    lhs: Any  # Term
    rhs: Any  # Term
    depth: int
    certificate: dict[str, Any]

    @property
    def statement(self) -> str:
        variables = sorted(term_vars(self.lhs) | term_vars(self.rhs))
        quantifier = ("forall " + " ".join(variables) + ". ") if variables else ""
        return f"{quantifier}{term_str(self.lhs)} = {term_str(self.rhs)}"


@dataclass(frozen=True)
class AxiomDomain:
    seed: str
    attempt: int
    signature: Signature
    axioms: tuple[tuple[Any, Any], ...]  # ((lhs, rhs), ...)
    template_kinds: tuple[str, ...]
    collapse_check: dict[str, Any] = field(repr=False, default_factory=dict)

    def axiom_strings(self) -> list[str]:
        return [f"{term_str(lhs)} = {term_str(rhs)}" for lhs, rhs in self.axioms]


def _fresh_name(rng: random.Random, used: set[str], *, syllables: int = 2) -> str:
    while True:
        name = "".join(
            rng.choice(_ONSETS) + rng.choice(_MIDDLES) for _ in range(syllables)
        ) + rng.choice(_CODAS)
        if name in used or name in _RESERVED or len(name) < 4:
            continue
        used.add(name)
        return name


def _make_signature(rng: random.Random) -> Signature:
    used: set[str] = set()
    class_name = _fresh_name(rng, used, syllables=2).capitalize()
    binary_ops = tuple(_fresh_name(rng, used) for _ in range(2))
    unary_ops = tuple(_fresh_name(rng, used) for _ in range(rng.choice((1, 1, 2))))
    constants = tuple(_fresh_name(rng, used) for _ in range(rng.choice((1, 2))))
    return Signature(class_name, binary_ops, unary_ops, constants)


# --- parameterized axiom-schema templates -----------------------------------
# Each template draws its operators and orientation from the seeded rng, so
# two domains rarely share structure and none is a copy of a named algebra.

def _tpl_assoc_like(rng: random.Random, sig: Signature):
    """(x f y) f z = x f (y g z) — associativity twisted through a second op."""
    f = rng.choice(sig.binary_ops)
    g = rng.choice(sig.binary_ops)
    x, y, z = var("x"), var("y"), var("z")
    lhs = app(f, app(f, x, y), z)
    rhs = app(f, x, app(g, y, z))
    return "assoc_like", lhs, rhs


def _tpl_absorption_like(rng: random.Random, sig: Signature):
    """x f (x g y) = x (or the mirrored orientation)."""
    f = rng.choice(sig.binary_ops)
    g = rng.choice(sig.binary_ops)
    x, y = var("x"), var("y")
    if rng.random() < 0.5:
        lhs = app(f, x, app(g, x, y))
    else:
        lhs = app(f, app(g, y, x), x)
    return "absorption_like", lhs, x


def _tpl_unary_hom(rng: random.Random, sig: Signature):
    """u(x f y) = u(x') g u(y') — (anti)homomorphism across a graded op swap."""
    u = rng.choice(sig.unary_ops)
    f = rng.choice(sig.binary_ops)
    g = rng.choice(sig.binary_ops)
    x, y = var("x"), var("y")
    left, right = (x, y) if rng.random() < 0.5 else (y, x)
    lhs = app(u, app(f, x, y))
    rhs = app(g, app(u, left), app(u, right))
    return "unary_hom", lhs, rhs


def _tpl_unary_power(rng: random.Random, sig: Signature):
    """u(u(x)) = x | u(x)  or  x f x = u(x)."""
    u = rng.choice(sig.unary_ops)
    x = var("x")
    roll = rng.random()
    if roll < 0.4:
        return "unary_power", app(u, app(u, x)), x
    if roll < 0.7:
        return "unary_power", app(u, app(u, x)), app(u, x)
    f = rng.choice(sig.binary_ops)
    return "unary_power", app(f, x, x), app(u, x)


def _tpl_unit_like(rng: random.Random, sig: Signature):
    """x f e = x | u(x)   or   e f x = x — unit rules, possibly twisted."""
    f = rng.choice(sig.binary_ops)
    e = const(rng.choice(sig.constants))
    x = var("x")
    roll = rng.random()
    if roll < 0.4:
        return "unit_like", app(f, x, e), x
    if roll < 0.7:
        return "unit_like", app(f, e, x), x
    u = rng.choice(sig.unary_ops)
    return "unit_like", app(f, x, e), app(u, x)


def _tpl_graded_interaction(rng: random.Random, sig: Signature):
    """u(x) f y = u(x f y)  or  x g (x f y) = x f (x g y) — interaction rules."""
    f = rng.choice(sig.binary_ops)
    u = rng.choice(sig.unary_ops)
    x, y = var("x"), var("y")
    roll = rng.random()
    if roll < 0.5:
        lhs = app(f, app(u, x), y)
        rhs = app(u, app(f, x, y))
        return "graded_interaction", lhs, rhs
    g = rng.choice(sig.binary_ops)
    lhs = app(g, x, app(f, x, y))
    rhs = app(f, x, app(g, x, y))
    return "graded_interaction", lhs, rhs


def _tpl_commutation_like(rng: random.Random, sig: Signature):
    """x f y = y f x, sparsely used."""
    f = rng.choice(sig.binary_ops)
    x, y = var("x"), var("y")
    return "commutation_like", app(f, x, y), app(f, y, x)


_TEMPLATES = (
    _tpl_assoc_like,
    _tpl_absorption_like,
    _tpl_unary_hom,
    _tpl_unary_power,
    _tpl_unit_like,
    _tpl_graded_interaction,
    _tpl_commutation_like,
)


def _collapse_check(axioms: list[tuple[Any, Any]]) -> dict[str, Any]:
    """Reject degenerate systems in which two fresh constants become equal
    (everything provable, all targets shallow)."""

    outcome = prove_equation(axioms, var("x"), var("y"), _COLLAPSE_BUDGET)
    return {
        "probe": "forall x y. x = y",
        "budget": _COLLAPSE_BUDGET.to_json(),
        "outcome": outcome.to_json(),
        "collapsed": outcome.proved,
    }


def generate_domain(seed: int | str, *, max_attempts: int = 64) -> AxiomDomain:
    """Deterministically generate a fresh, non-collapsed axiom domain."""

    for attempt in range(max_attempts):
        rng = random.Random(f"{GENERATOR_VERSION}:{seed}:{attempt}")
        sig = _make_signature(rng)
        n_axioms = rng.randint(4, 7)
        axioms: list[tuple[Any, Any]] = []
        kinds: list[str] = []
        seen: set[str] = set()
        guard = 0
        while len(axioms) < n_axioms and guard < 200:
            guard += 1
            template = rng.choice(_TEMPLATES)
            kind, lhs, rhs = template(rng, sig)
            if lhs == rhs:
                continue
            if kind == "commutation_like" and "commutation_like" in kinds:
                continue  # keep commutation sparse
            key = f"{term_str(lhs)}={term_str(rhs)}"
            mirror = f"{term_str(rhs)}={term_str(lhs)}"
            if key in seen or mirror in seen:
                continue
            seen.add(key)
            axioms.append((lhs, rhs))
            kinds.append(kind)
        if len(axioms) < 4 or len(set(kinds)) < 3:
            continue
        collapse = _collapse_check(axioms)
        if collapse["collapsed"]:
            continue
        return AxiomDomain(
            seed=str(seed),
            attempt=attempt,
            signature=sig,
            axioms=tuple(axioms),
            template_kinds=tuple(kinds),
            collapse_check=collapse,
        )
    raise RuntimeError(f"no non-collapsed axiom domain found for seed {seed!r}")


# --- theorem-target enumerator ----------------------------------------------

def _term_pool(sig: Signature, *, max_size: int = 5) -> list[Any]:
    """All terms over {x, y}, the constants, and the signature ops up to
    ``max_size``, in deterministic (size, string) order."""

    atoms = [var("x"), var("y")] + [const(name) for name in sig.constants]
    by_size: dict[int, list[Any]] = {1: list(atoms)}
    for size in range(2, max_size + 1):
        terms: list[Any] = []
        for u in sig.unary_ops:
            for inner in by_size.get(size - 1, ()):
                terms.append(app(u, inner))
        for f in sig.binary_ops:
            for left_size in range(1, size - 1):
                right_size = size - 1 - left_size
                for left in by_size.get(left_size, ()):
                    for right in by_size.get(right_size, ()):
                        terms.append(app(f, left, right))
        by_size[size] = terms
    pool = [term for size in sorted(by_size) for term in by_size[size]]
    return sorted(set(pool), key=lambda t: (term_size(t), term_str(t)))


def enumerate_targets(
    domain: AxiomDomain,
    *,
    small: Budget = B_SMALL,
    large: Budget = B_LARGE,
    n_seeds: int = 8,
    max_targets: int = 4,
    max_rhs_size: int = 11,
) -> list[TheoremTarget]:
    """Machine enumerator of candidate theorem statements at graded depth.

    Strategy: pick deterministic seed terms, compute their bounded reachable
    balls under the axioms, and read each reached term ``t`` at distance ``d``
    as the candidate equation ``seed = t`` with estimated minimal derivation
    length ``d``.  One target per available depth grade is selected (smallest
    statement wins, deterministically), then re-certified with independent
    small/large prover runs.
    """

    rng = random.Random(f"{GENERATOR_VERSION}:targets:{domain.seed}:{domain.attempt}")
    pool = [
        term
        for term in _term_pool(domain.signature)
        if term[0] == "f" and 3 <= term_size(term) <= 5 and term_vars(term)
    ]
    seeds = rng.sample(pool, min(n_seeds, len(pool))) if pool else []

    candidates: dict[int, list[tuple[Any, Any]]] = {}
    for source in seeds:
        distances, _truncated = reachable_ball(domain.axioms, source, large)
        for reached, depth in distances.items():
            if depth < 1:
                continue
            rhs = deskolemize(reached)
            if rhs == source or term_size(rhs) > max_rhs_size:
                continue
            if not term_vars(rhs) <= term_vars(source):
                continue  # keep statements closed over the seed's variables
            candidates.setdefault(depth, []).append((source, rhs))

    targets: list[TheoremTarget] = []
    for depth in sorted(candidates):
        if len(targets) >= max_targets:
            break
        best = min(
            candidates[depth],
            key=lambda pair: (
                term_size(pair[0]) + term_size(pair[1]),
                term_str(pair[0]),
                term_str(pair[1]),
            ),
        )
        lhs, rhs = best
        certificate = difficulty_certificate(
            domain.axioms, lhs, rhs, small=small, large=large
        )
        if not certificate["outcome_large"]["proved"]:
            continue  # ball truncation artifact; never emit an uncertified target
        graded_depth = certificate["depth"]
        targets.append(
            TheoremTarget(
                lean_name=f"{domain.signature.class_name.lower()}_d{graded_depth}"
                f"_t{len(targets) + 1}",
                lhs=lhs,
                rhs=rhs,
                depth=graded_depth,
                certificate=certificate,
            )
        )
    return targets


# --- Lean 4 rendering ---------------------------------------------------------

def _lean_term(term: Any) -> str:
    if term[0] in ("v", "c"):
        return term[1]
    rendered = [term[1]]
    for argument in term[2]:
        text = _lean_term(argument)
        rendered.append(f"({text})" if argument[0] == "f" else text)
    return " ".join(rendered)


def _binder_vars(lhs: Any, rhs: Any) -> list[str]:
    return sorted(term_vars(lhs) | term_vars(rhs))


def render_lean(domain: AxiomDomain, targets: list[TheoremTarget]) -> str:
    """Lean 4 source: the axioms as a ``class`` plus theorem-statement
    skeletons.  The skeletons carry ``sorry`` placeholders and are therefore
    NOT kernel-valid as emitted; the pinned request (``allow_sorry = false``)
    is what a solving run must satisfy after replacing each placeholder."""

    sig = domain.signature
    lines: list[str] = [
        "/-",
        f"E3.1 synthetic axiom domain ({GENERATOR_VERSION}).",
        f"seed={domain.seed} attempt={domain.attempt}",
        "Freshly generated uninterpreted symbols; the system is not intended to",
        "model any prior algebra.  Statement skeletons end in `sorry`; the",
        "pinned verification request forbids sorry, so a submission must",
        "replace every placeholder with a proof from the class hypotheses.",
        "-/",
        "",
        "universe u",
        "",
        f"class {sig.class_name} (α : Type u) where",
    ]
    for name in sig.binary_ops:
        lines.append(f"  {name} : α → α → α")
    for name in sig.unary_ops:
        lines.append(f"  {name} : α → α")
    for name in sig.constants:
        lines.append(f"  {name} : α")
    for index, (lhs, rhs) in enumerate(domain.axioms, start=1):
        binders = " ".join(_binder_vars(lhs, rhs))
        quantifier = f"∀ ({binders} : α), " if binders else ""
        lines.append(
            f"  ax{index} : {quantifier}{_lean_term(lhs)} = {_lean_term(rhs)}"
        )
    lines += ["", f"open {sig.class_name}", ""]
    for target in targets:
        binders = " ".join(_binder_vars(target.lhs, target.rhs))
        binder_clause = f" ({binders} : α)" if binders else ""
        lines.append(f"/-- depth-{target.depth} target (certificate sealed). -/")
        lines.append(
            f"theorem {target.lean_name} {{α : Type u}} [{sig.class_name} α]"
            f"{binder_clause} :"
        )
        lines.append(
            f"    {_lean_term(target.lhs)} = {_lean_term(target.rhs)} := by"
        )
        lines.append("  sorry -- E31-SKELETON: replace with a proof")
        lines.append("")
    return "\n".join(lines)


def pinned_request(lean_source: bytes, targets: list[TheoremTarget]) -> PinnedLeanRequest:
    """Pinned-Lean request template for the skeleton source.

    ``source_ref`` pins the exact skeleton bytes a solver starts from; a
    submission replaces the placeholders and is verified under a request that
    is identical except for its recomputed ``source_ref``.
    """

    return PinnedLeanRequest(
        toolchain_id=LEAN_TOOLCHAIN_ID,
        source_ref=sha256_hex(lean_source),
        target_theorems=[target.lean_name for target in targets],
        allowed_axioms=list(LEAN_ALLOWED_AXIOMS),
        max_heartbeats=400_000,
        max_rec_depth=1_000,
    )


def domain_public_json(domain: AxiomDomain, targets: list[TheoremTarget]) -> dict[str, Any]:
    """Problem-facing description: axioms + graded statements, no certificates,
    no derivations (those are sealed)."""

    return {
        "schema": "e31-axiom-problem-v1",
        "generator_version": GENERATOR_VERSION,
        "seed": domain.seed,
        "attempt": domain.attempt,
        "signature": domain.signature.to_json(),
        "axioms": domain.axiom_strings(),
        "template_kinds": list(domain.template_kinds),
        "targets": [
            {
                "lean_name": target.lean_name,
                "statement": target.statement,
                "depth_grade": target.depth,
            }
            for target in targets
        ],
    }


def domain_sealed_certificate(
    domain: AxiomDomain, targets: list[TheoremTarget]
) -> dict[str, Any]:
    """Answer key: full difficulty certificates including derivations, plus
    the collapse-check receipt.  Sealed; revealed only post-hoc."""

    return {
        "schema": "e31-axiom-certificate-v1",
        "generator_version": GENERATOR_VERSION,
        "seed": domain.seed,
        "attempt": domain.attempt,
        "collapse_check": domain.collapse_check,
        "axioms": [
            {"lhs": term_to_json(lhs), "rhs": term_to_json(rhs)}
            for lhs, rhs in domain.axioms
        ],
        "targets": [
            {
                "lean_name": target.lean_name,
                "statement": target.statement,
                "depth": target.depth,
                "certificate": target.certificate,
            }
            for target in targets
        ],
    }
