"""Block A's two fixed hard questions and three seed-distinguishing
leading sentences (PREREG.yaml). Seed variation follows the S6 pattern
(RESULTS.md Failure #3): `_request_digest` hashes question text
verbatim and does not see seat bindings, so a distinguishing leading
sentence is what mints a fresh run identity per seed while leaving the
argued claim itself unchanged.

Usage: python3 block_a_questions.py get Q_IDX SEED_IDX   (Q_IDX, SEED_IDX in {1,2,3} as applicable)
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
}


def get(q_idx: int, seed_idx: int) -> str:
    return SEED_PREFIXES[seed_idx] + QUESTIONS[q_idx]


if __name__ == "__main__":
    if sys.argv[1] == "get":
        print(get(int(sys.argv[2]), int(sys.argv[3])))
    else:
        raise SystemExit(f"unknown command {sys.argv[1]!r}")
