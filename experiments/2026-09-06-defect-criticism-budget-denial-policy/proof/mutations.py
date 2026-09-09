"""Mutation proof: each piece of the fix has a test that goes red without it."""

from __future__ import annotations

import subprocess
import sys

TESTS = "tests/test_criticism_budget_denial_policy.py"

MUTATIONS = [
    (
        "M1: the criticism road stops absorbing the refusal (P1 restored)",
        "src/deepreason/scheduler/scheduler.py",
        "            except WorkBudgetDenied as denial:\n"
        "                if budget_denial_exhausted(denial) or policy == POLICY_STOP:\n"
        "                    raise",
        "            except WorkBudgetDenied as denial:\n"
        "                if True or denial or policy == POLICY_STOP:\n"
        "                    raise",
    ),
    (
        "M2: a SPENT ceiling is absorbed too -- the law becomes configurable",
        "src/deepreason/scheduler/scheduler.py",
        "                if budget_denial_exhausted(denial) or policy == POLICY_STOP:",
        "                if denial is None or policy == POLICY_STOP:",
    ),
    (
        "M3: the policy is ignored -- every refusal drops, nothing shrinks",
        "src/deepreason/scheduler/scheduler.py",
        "                halves = split_batch(batch) if policy == POLICY_SHRINK else ()",
        "                halves = ()",
    ),
    (
        "M4: the pass no longer declares that money cut it short",
        "src/deepreason/scheduler/scheduler.py",
        "                OUTCOME_CUT_TOKEN_BUDGET\n                if budget_cut",
        "                OUTCOME_COMPLETE\n                if budget_cut",
    ),
    (
        "M5: the declaration guesses its targets again",
        "src/deepreason/scheduler/scheduler.py",
        "            targets=attacked,",
        "            targets=[],",
    ),
    (
        "M6: switching the gate to stop-the-run goes silent",
        "src/deepreason/scheduler/scheduler.py",
        "        self._record_criticism_budget_stop_warning(policy)",
        "        pass",
    ),
    (
        "M7: the versioned-source drop is lost -- every subject digest moves",
        "src/deepreason/run_manifest.py",
        '    data.pop("CRITICISM_BUDGET_DENIAL_POLICY", None)',
        "    pass",
    ),
    (
        "M8: an unknown policy id refuses instead of falling back",
        "src/deepreason/runtime/criticism_budget_policy.py",
        "    return DEFAULT_CRITICISM_BUDGET_POLICY, (requested or None)",
        '    raise ValueError("unknown criticism budget policy")',
    ),
]


def main() -> int:
    vacuous = 0
    for label, path, old, new in MUTATIONS:
        original = open(path).read()
        if old not in original:
            print(f"{label}\n    SKIPPED: anchor not found in {path}")
            vacuous += 1
            continue
        try:
            open(path, "w").write(original.replace(old, new, 1))
            done = subprocess.run(
                [sys.executable, "-m", "pytest", TESTS, "-q", "--no-header",
                 "-p", "no:cacheprovider"],
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
        for name in sorted(set(red)):
            print(f"    red: {name}")
        if not red:
            print("    VACUOUS: no test noticed this mutation")
            vacuous += 1
    return 1 if vacuous else 0


if __name__ == "__main__":
    raise SystemExit(main())
