"""Run selected checker mutations in disposable local copies of the reference.

A detected mutant is a nonzero unittest result with actual test failures/errors,
not a syntax error or timeout. Reports are finite regression evidence only.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
MUTATIONS = [
    ("M01-failed-body-counts", [
        ("a.readiness == Check.PASS and bool(a.assessment)",
         "a.readiness != Check.UNKNOWN and bool(a.assessment)"),
        ("if a.readiness == Check.FAIL or bool(a.essential & outside)",
         "if False or bool(a.essential & outside)"),
    ]),
    ("M02-criticism-dependency-exemption", [
        ("and a.essential.issubset(inside) and attackers[a.id].issubset(outside)",
         "and (a.role == 'criticism' or a.essential.issubset(inside)) and attackers[a.id].issubset(outside)"),
        ("or bool(a.essential & outside)",
         "or (a.role != 'criticism' and bool(a.essential & outside))"),
    ]),
    ("M03-missing-activation-counts", [
        ("a.readiness == Check.PASS and bool(a.assessment)", "a.readiness == Check.PASS"),
    ]),
    ("M04-incompatible-history-allowed", [
        ("if any(len(alt & possible_past) > 1 for alt in self.alternatives):", "if False:"),
        ("if any(len(alt & selected) > 1 for alt in self.alternatives):", "if False:"),
    ]),
    ("M05-ungrounded-reference-allowed", [
        ("if ref.artifact not in allowed:", "if False:"),
    ]),
    ("M06-boundary-erased", [
        ("relevant = [c for c in cases if c.key == key]",
         "relevant = [c for c in cases if dict(c.key.__dict__, boundary=key.boundary) == key.__dict__]"),
    ]),
    ("M07-contribution-erased", [
        ('if k != "predicate")', 'if k not in ("predicate", "contribution"))'),
    ]),
    ("M08-empty-family-counts", [
        ("if not informative or not free_variant_cases:", "if not informative:"),
    ]),
    ("M09-nested-reference-ignored", [
        ("for item in value.values():\n            yield from references(item)",
         "for item in ():\n            yield from references(item)"),
    ]),
]


def run() -> list[dict]:
    original = (HERE / "reference_kernel.py").read_text()
    results = []
    for name, replacements in MUTATIONS:
        mutated = original
        for before, after in replacements:
            if mutated.count(before) != 1:
                raise RuntimeError(f"{name}: expected exactly one mutation site: {before!r}")
            mutated = mutated.replace(before, after, 1)
        compile(mutated, f"{name}.py", "exec")
        with tempfile.TemporaryDirectory(prefix="ois-mutant-") as folder:
            dest = Path(folder)
            (dest / "reference_kernel.py").write_text(mutated)
            for filename in ("test_reference_kernel.py", "fixtures.py"):
                shutil.copy2(HERE / filename, dest / filename)
            completed = subprocess.run([sys.executable, "-m", "unittest", "-v"], cwd=dest,
                capture_output=True, text=True, timeout=20)
        log = completed.stdout + completed.stderr
        failures = [line for line in log.splitlines() if line.startswith(("FAIL:", "ERROR:"))]
        detected = completed.returncode != 0 and bool(failures)
        results.append({"mutation": name, "detected": detected,
                        "returncode": completed.returncode, "failing_checks": failures})
    return results


if __name__ == "__main__":
    results = run()
    path = HERE / "mutation_results.json"
    path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Detected {sum(r['detected'] for r in results)}/{len(results)} selected mutations")
    if not all(r["detected"] for r in results):
        raise SystemExit(1)
