"""Block B's one fixed simulation-friendly question and ten
seed-distinguishing leading sentences (S6/_request_digest pattern).
Deliberately SIMPLER than the turmite/jolt family it is chosen from:
the 2026-08-09 research pass (see RESULTS.md) found NO simulation
proposal has ever reached COMPILED in this repo's history -- only
PROPOSED -> VALIDATED -> (GRANTED | DENIED). A trivial, flat-observable
task maximizes the chance of observing later funnel stages for the
first time, rather than re-measuring a structural ceiling with a hard
question. This is a recorded, reasoned DEVIATION from reusing
turmite/jolt verbatim (PREREG.yaml documents it as such).

Usage: python3 block_b_question.py get SEED_IDX   (SEED_IDX in 1..10)
"""

import sys

QUESTION = (
    "Argue for or against the claim that the following pseudorandom "
    "generator produces a FAIR distribution over six faces after "
    "10000 draws, where fair means every face count falls within two "
    "standard deviations of the uniform expectation (expectation "
    "10000/6, standard deviation sqrt(10000 * (1/6) * (5/6))). The "
    "generator: X_0 = 42; X_(n+1) = (1103515245 * X_n + 12345) mod "
    "2^31; die_n = 1 + (X_n mod 6), for n = 1 .. 10000. There is no "
    "closed-form shortcut for the exact counts at this horizon: the "
    "only way to know them is to run the exact recurrence and tally "
    "the results. File a typed sandboxed Python simulation "
    "(simulation_mode sandboxed_python_v1) implementing this exact "
    "recurrence and return the six face counts as flat, "
    "single-segment observables (count_1 through count_6) plus "
    "total. Before any tally is used as evidence, calibrate the "
    "implementation in the same channel: return the first ten "
    "(X_n, die_n) pairs so the recurrence and the face-mapping can be "
    "checked by hand against this specification."
)

SEED_PREFIXES = {
    i: f"This is the seed-{i} variant of the same question: " for i in range(1, 11)
}


def get(seed_idx: int) -> str:
    return SEED_PREFIXES[seed_idx] + QUESTION


if __name__ == "__main__":
    if sys.argv[1] == "get":
        print(get(int(sys.argv[2])))
    else:
        raise SystemExit(f"unknown command {sys.argv[1]!r}")
