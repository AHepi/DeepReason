"""Block C's one fixed hard question (same text as Block A's Q1) and
two seed-distinguishing leading sentences. Kept as a standalone copy
(not imported cross-block) so this block's directory stays
self-contained per the operator's "one subdir per block" instruction.

Usage: python3 block_c_question.py get SEED_IDX   (SEED_IDX in {1,2})
"""

import sys

QUESTION = (
    "Argue for or against the claim that a panel of trained "
    "non-experts following an explicit checklist will, on average, "
    "produce more reliable judgments than a single domain expert "
    "relying on intuition, for tasks with objectively verifiable "
    "outcomes. Identify what evidence within a single evaluation "
    "would distinguish a genuine reliability gain from mere "
    "checklist compliance that happens to track the right answer."
)

SEED_PREFIXES = {
    1: "This is the first-seed variant of the same question: ",
    2: "This is the second-seed variant of the same question: ",
}


def get(seed_idx: int) -> str:
    return SEED_PREFIXES[seed_idx] + QUESTION


if __name__ == "__main__":
    if sys.argv[1] == "get":
        print(get(int(sys.argv[2])))
    else:
        raise SystemExit(f"unknown command {sys.argv[1]!r}")
