"""Block A-2's questions -- IDENTICAL text to Block A's
block_a_questions.py (copied verbatim, not imported, so this block's
directory stays self-contained). Seeds 1-3 match Block A's own
seed prefixes exactly (same distinguishing-sentence pattern); seeds
4-7 are NEW, added for the 4 extra CROSS-Q1-only attempts sizing the
V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY refusal rate (PREREG-A2.yaml).

Usage: python3 block_a2_questions.py get Q_IDX SEED_IDX
"""

import sys

QUESTIONS = {
    1: (
        "Argue for or against the claim that a panel of trained "
        "non-experts following an explicit checklist will, on average, "
        "produce more reliable judgments than a single domain expert "
        "relying on intuition, for tasks with objectively verifiable "
        "outcomes. Identify what evidence within a single evaluation "
        "would distinguish a genuine reliability gain from mere "
        "checklist compliance that happens to track the right answer."
    ),
    2: (
        "Argue for or against the claim that a decentralized network of "
        "small, independently operated services is more resilient to "
        "correlated failure than one large service with strictly more "
        "total internal redundancy. Identify what evidence would "
        "distinguish failure modes that are truly independent from "
        "failures that merely appear uncorrelated until a shared cause "
        "is found."
    ),
}

SEED_PREFIXES = {
    1: "This is the first-seed variant of the same question: ",
    2: "This is the second-seed variant of the same question: ",
    3: "This is the third-seed variant of the same question: ",
    4: "This is the fourth-seed variant of the same question: ",
    5: "This is the fifth-seed variant of the same question: ",
    6: "This is the sixth-seed variant of the same question: ",
    7: "This is the seventh-seed variant of the same question: ",
}


def get(q_idx: int, seed_idx: int) -> str:
    return SEED_PREFIXES[seed_idx] + QUESTIONS[q_idx]


if __name__ == "__main__":
    if sys.argv[1] == "get":
        print(get(int(sys.argv[2]), int(sys.argv[3])))
    else:
        raise SystemExit(f"unknown command {sys.argv[1]!r}")
