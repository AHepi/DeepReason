"""Mutation proof: each piece of the fix has a test that goes red without it.

Run from the repository root.  Each mutation is applied to a working copy of
one source file, the named tests are run, the file is restored, and the
verdict is printed.  A mutation that leaves every test green is a test that
proves nothing.
"""

from __future__ import annotations

import subprocess
import sys

TESTS = "tests/test_budget_exhausted_classification.py"

MUTATIONS = [
    (
        "M1: the cycle loop's arm no longer names the transactional denial",
        "src/deepreason/scheduler/scheduler.py",
        "except (TokenBudgetExceeded, WorkBudgetDenied) as e:",
        "except TokenBudgetExceeded as e:",
    ),
    (
        "M2: the guard is gone -- every denial is treated as a spent ceiling",
        "src/deepreason/scheduler/scheduler.py",
        "                if not budget_denial_exhausted(e):",
        "                if False:",
    ),
    (
        "M3: the rule says every refusal is a spent ceiling",
        "src/deepreason/llm/budget.py",
        "            error.budget_exhausted = int(booking) <= self.budget",
        "            error.budget_exhausted = True",
    ),
    (
        "M4: a refusal whose size cannot be established reads as spent",
        "src/deepreason/llm/budget.py",
        "            error.budget_exhausted = remaining is not None and remaining <= 0",
        "            error.budget_exhausted = True",
    ),
    (
        "M5: the denial stops carrying the meter's answer",
        "src/deepreason/workflow/transaction.py",
        "        self.budget_exhausted = bool(budget_exhausted)",
        "        self.budget_exhausted = False",
    ),
]


def main() -> int:
    failures = 0
    for label, path, old, new in MUTATIONS:
        original = open(path).read()
        if old not in original:
            print(f"{label}\n    SKIPPED: anchor not found in {path}")
            failures += 1
            continue
        try:
            open(path, "w").write(original.replace(old, new, 1))
            done = subprocess.run(
                [sys.executable, "-m", "pytest", TESTS, "-q", "--no-header", "-p",
                 "no:cacheprovider"],
                capture_output=True,
                text=True,
            )
        finally:
            open(path, "w").write(original)
        tail = [line for line in done.stdout.splitlines() if line.strip()][-1:]
        red = [
            line.split("::")[-1].split(" ")[0]
            for line in done.stdout.splitlines()
            if line.startswith("FAILED ")
        ]
        print(f"{label}\n    {tail[0] if tail else '(no output)'}")
        for name in red:
            print(f"    red: {name}")
        if not red:
            print("    VACUOUS: no test noticed this mutation")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
