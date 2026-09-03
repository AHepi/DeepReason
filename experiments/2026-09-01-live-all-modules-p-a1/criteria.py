"""P-A1's three subject criteria, frozen before any provider call.

These are ORDINARY ``predicate:`` commitments over the artifact's own bytes.
Nothing here registers a program, changes a threshold, or touches a frozen
surface.  They exist because the managed preparation service hardcodes
``criteria=()``: a run whose problems must carry subject-substantive
commitments has to enter through the manifest surface (the same single run
path -- ``deepreason run --run-manifest`` is a rendering shell over
``TextRunApplicationService.start_manifest_run``).

They are DELIBERATELY LEXICAL AND GENEROUS, and that is a scope statement,
not a weakness to apologise for.  A predicate over content bytes cannot
decide whether a proof sketch is CORRECT; it can only decide whether an
artifact has actually addressed the demand the operator's question makes.
The three demands are the question's own three clauses:

    1. a verdict on the limit of the consensus probability;
    2. a characterisation of the obstruction structures;
    3. a quantitative, falsifiable scaling law (or a proof sketch) for how
       their prevalence moves with n.

An artifact that answers only the first is a real artifact and is admitted;
it simply does not satisfy the other two.  That asymmetry is the point --
these are the commitments the harness's own machinery (hv variation, reach
sweeps, the coverage axis) prices, and a battery that every candidate passes
prices nothing.

A malformed ``predicate:`` is a REFUTATION, not an error: ``programs.evaluate``
catches every exception and returns ``fail``.  A typo here would refute every
artifact silently and the finished record would read exactly like "the models
could not construct anything".  ``preflight_pa1.py`` therefore runs a
discrimination table over these three BEFORE the ladder makes any provider
call, and refuses the launch if a criterion cannot separate an on-target
answer from an off-target one.
"""
from __future__ import annotations

from deepreason.ontology import Commitment

# --- 1. the limit verdict -------------------------------------------------
# An asymptotic frame AND a stated direction.  Either half alone is prose.
_ASYMPTOTIC_TERMS = (
    "as n", "n →", "n ->", "n→", "asymptotic", "in the limit",
    "large n", "n grows", "n → ∞", "n to infinity", "limiting",
)
_VERDICT_TERMS = (
    "tends to 1", "tends to 0", "tends to one", "tends to zero",
    "→ 1", "→ 0", "-> 1", "-> 0", "1 - o(1)", "o(1)",
    "bounded away", "strictly between", "bounded below", "constant strictly",
    "probability of consensus", "consensus probability",
    "with high probability", "whp", "vanishes", "approaches 1", "approaches 0",
)

# --- 2. the obstruction structure ----------------------------------------
# The question asks for the FINITE LOCALLY STABLE MIXED CONFIGURATIONS.  An
# artifact earns this by naming the structure, not by using the word
# "obstruction".
_OBSTRUCTION_TERMS = (
    "locally stable", "stable mixed", "frozen", "blocking", "absorbing",
    "fixed point", "trapped", "stuck", "obstruction", "deadlock",
    "no vertex", "every vertex", "each vertex", "majority of its",
    "two of its three", "2 of its 3", "agrees with", "same colour",
    "same color", "monochromatic", "induced subgraph", "cycle", "clique",
    "minority", "boundary",
)

# --- 3. the quantitative scaling law -------------------------------------
# A prevalence quantity AND a scaling form in n.  This is the clause a
# generic essay reliably misses.
_PREVALENCE_TERMS = (
    "expected number", "expected count", "prevalence", "density",
    "frequency", "number of such", "count of", "how many",
    "probability that", "fraction of",
)
_SCALING_TERMS = (
    "theta(", "Θ(", "omega(", "Ω(", "o(n", "Θ(n", "poisson",
    "linear in n", "proportional to n", "polynomial in n", "exponentially",
    "exp(", "e^", "n^", "log n", "sqrt(n)", "√n", "per vertex",
    "constant times n", "grows like", "scales like", "scales as",
    "independent of n", "converges to a poisson",
)


def _any_expr(terms: tuple[str, ...]) -> str:
    return f"any(t in content.lower() for t in {terms!r})"


def _atleast_expr(terms: tuple[str, ...], k: int) -> str:
    return f"sum(1 for t in {terms!r} if t in content.lower()) >= {k}"


CRITERIA = (
    Commitment(
        id="pa1-limit-verdict@v1",
        eval=(
            f"predicate:{_any_expr(_ASYMPTOTIC_TERMS)} and "
            f"{_any_expr(_VERDICT_TERMS)}"
        ),
    ),
    Commitment(
        id="pa1-obstruction-structure@v1",
        # TWO distinct structural terms, not one: "frozen" alone is a word an
        # artifact can use without characterising anything.
        eval=f"predicate:{_atleast_expr(_OBSTRUCTION_TERMS, 2)}",
    ),
    Commitment(
        id="pa1-scaling-law@v1",
        eval=(
            f"predicate:{_any_expr(_PREVALENCE_TERMS)} and "
            f"{_any_expr(_SCALING_TERMS)}"
        ),
    ),
)
