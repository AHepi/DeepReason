"""E3.1 ground-truth novelty benchmark builders (docs/EXPERIMENT_PROGRAM_2026-07.md).

Deterministic, zero-LLM generators for the benchmark's contamination-resistance
classes plus the sealed-holdout wiring:

- ``axiom_domains``  — fresh axiomatic systems pinned in Lean 4, with a
  machine enumerator of depth-graded theorem targets;
- ``bounded_prover`` — the bounded forward-chaining equational prover that
  produces difficulty certificates and grades depth;
- ``constructions`` — randomized program-checkable construction problems with
  trusted checkers and brute-force solvability certificates;
- ``sealed``        — sealed-holdout blobs + manifest per harness-spec-v1.3
  §10.5/§14;
- ``build_demo``    — end-to-end demo benchmark builder.

Everything is deterministic from a seed: same seed, same bytes.  The LLM
difficulty-calibration baselines and the experiment prereg are deliberately
NOT here; they come later (see the program doc, E3.1 "difficulty certificate"
clause b).
"""

from e31_benchmark.bounded_prover import (  # noqa: F401
    Budget,
    ProofOutcome,
    app,
    const,
    difficulty_certificate,
    prove_equation,
    reachable_ball,
    term_str,
    var,
)
