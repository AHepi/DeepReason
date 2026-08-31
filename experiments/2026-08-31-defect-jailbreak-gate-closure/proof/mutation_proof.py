"""Do the new tests and map checks actually go RED when the gate is removed?

A test that passes before AND after the change it claims to guard is decoration.
This mutates the shipped gate four ways and records what each mutation kills.
Every mutation is reverted with `git checkout --` before the next one; the
script refuses to start on a dirty tree so a failure can never eat real work.

    python experiments/2026-08-31-defect-jailbreak-gate-closure/proof/mutation_proof.py

Writes mutation_proof.json beside itself.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "mutation_proof.json"

CONTINUATION = "src/deepreason/runtime/continuation.py"
APPLY = "src/deepreason/amendment/apply.py"

# The map checks this tranche wrote or rewrote, verbatim as the documents carry
# them, so the proof exercises the shipped text and not a paraphrase.
TRIPWIRE = (
    "python -c \"import pathlib; "
    "c=pathlib.Path('src/deepreason/runtime/continuation.py').read_text(); "
    "a=pathlib.Path('src/deepreason/amendment/apply.py').read_text(); "
    "assert 'CONTINUE_RECORD_NOT_VERIFIED' in c and 'record_verification_refusal' in c "
    "and 'AMEND_RECORD_NOT_VERIFIED' in a, 'the integrity gate was removed from a verb'\""
)
CODE_COUNT = (
    "python -c 'import re,pathlib; d=pathlib.Path(\"src/deepreason/amendment\"); "
    "codes=set(); [codes.update(re.findall(r\"AmendmentError\\(\\s*\\\"([A-Z][A-Z_]+)\\\"\", "
    "(d/n).read_text())) for n in (\"apply.py\",\"state.py\",\"models.py\")]; "
    "assert len(codes)==23, sorted(codes)'"
)
GATE_TESTS = (
    "python -m pytest tests/test_jailbreak_gate.py -q -p no:randomly "
    "-k 'continue_refuses or amend_refuses or writes_nothing'"
)

MUTATIONS = [
    {
        "name": "neutralise the gate (always allow)",
        "file": CONTINUATION,
        "find": "    if not checks:\n        return None",
        "replace": "    if True:\n        return None",
        "expect_red": ["gate_tests", "behaviour"],
    },
    {
        "name": "drop continue's call site",
        "file": CONTINUATION,
        "find": '    refusal = record_verification_refusal(root_path)\n'
                '    if refusal is not None:\n'
                '        raise ValueError(f"CONTINUE_RECORD_NOT_VERIFIED: {refusal}")\n',
        "replace": "",
        "expect_red": ["tripwire", "gate_tests"],
    },
    {
        "name": "drop amend's call site",
        "file": APPLY,
        "find": '    refusal = record_verification_refusal(root)\n'
                '    if refusal is not None:\n'
                '        raise AmendmentError("AMEND_RECORD_NOT_VERIFIED", refusal)\n',
        "replace": "",
        "expect_red": ["tripwire", "code_count", "gate_tests"],
    },
    {
        "name": "widen the channel filter to every violation",
        "file": CONTINUATION,
        "find": "            if str(item.get(\"check\")) in _SECURITY_CHECKS",
        "replace": "            if True",
        "expect_red": ["collision_guard"],
    },
]


def run(command: str) -> bool:
    done = subprocess.run(
        command, shell=True, cwd=REPO, capture_output=True, text=True
    )
    return done.returncode == 0


def behaviour_still_refuses() -> bool:
    """Does the shipped acceptance predicate still refuse the forged root?"""

    return run(
        "python -m pytest tests/test_jailbreak_gate.py -q -p no:randomly "
        "-k 'continue_refuses'"
    )


def collision_guard_holds() -> bool:
    return run(
        "python -m pytest tests/test_jailbreak_gate.py"
        "::test_a_record_that_is_merely_incomplete_still_passes_the_gate "
        "-q -p no:randomly"
    )


def main() -> int:
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", CONTINUATION, APPLY],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.strip()
    if dirty:
        print(f"REFUSING: gate sources are dirty:\n{dirty}")
        return 2

    payload: dict = {"baseline": {}, "mutations": []}
    payload["baseline"] = {
        "tripwire": run(TRIPWIRE),
        "code_count": run(CODE_COUNT),
        "gate_tests": run(GATE_TESTS),
        "collision_guard": collision_guard_holds(),
    }
    print(f"baseline (all must be True): {payload['baseline']}")

    for mutation in MUTATIONS:
        target = REPO / mutation["file"]
        source = target.read_text()
        if mutation["find"] not in source:
            row = {"name": mutation["name"], "error": "anchor not found"}
            payload["mutations"].append(row)
            print(f"!! {mutation['name']}: anchor not found")
            continue
        target.write_text(source.replace(mutation["find"], mutation["replace"], 1))
        try:
            observed = {
                "tripwire": run(TRIPWIRE),
                "code_count": run(CODE_COUNT),
                "gate_tests": run(GATE_TESTS),
                "collision_guard": collision_guard_holds(),
                "behaviour": behaviour_still_refuses(),
            }
        finally:
            subprocess.run(
                ["git", "checkout", "--", mutation["file"]], cwd=REPO, check=True
            )
        killed = sorted(name for name, ok in observed.items() if not ok)
        row = {
            "name": mutation["name"],
            "file": mutation["file"],
            "observed_green": observed,
            "killed": killed,
            "expected_killed_at_least": sorted(mutation["expect_red"]),
            "detected": bool(killed),
        }
        payload["mutations"].append(row)
        print(f"-- {mutation['name']}")
        print(f"   killed: {killed or 'NOTHING -- the guards are decoration'}")

    payload["every_mutation_detected"] = all(
        row.get("detected") for row in payload["mutations"]
    )
    payload["baseline_all_green"] = all(payload["baseline"].values())
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"baseline_all_green: {payload['baseline_all_green']}")
    print(f"every_mutation_detected: {payload['every_mutation_detected']}")
    print(f"written: {OUT}")
    return 0 if payload["every_mutation_detected"] and payload["baseline_all_green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
