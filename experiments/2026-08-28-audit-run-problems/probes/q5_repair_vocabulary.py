#!/usr/bin/env python3
"""Q5/P8 proof -- the repair `mode` producer and its checker do not share a
vocabulary, and the record shows exactly the overlap.

PRODUCER  src/deepreason/llm/repair.py:1505
              mode: Literal["initial", "whole_object_syntax", "patch"]
          and repair.py:1612 emits mode="whole_object_syntax" on the
          syntax-repair leg.

CHECKER   src/deepreason/workflow/nonconjecture_recovery.py:1002
              _authority(mode in {"patch", "full"}, "repair mode is invalid")
          reached for EVERY repair-kind child recovered through
          atomic_recovery.py:71-74 and nonconjecture_recovery.py:1194.

The two sets intersect in {"patch"} alone. "full" is accepted by the checker
and emitted by nothing; "whole_object_syntax" is emitted constantly and
accepted by nothing. So the epoch-5 death is DETERMINISTIC on payload shape,
not stochastic: any whole_object_syntax repair child that reaches a recovery
path raises. What varies run to run is only whether a recovery path is taken.

This asserts both halves against the live source and against the committed
records, and exits non-zero if either stops holding.
"""
import json
import pathlib
import re
import sys
import typing

sys.path.insert(0, "src")

REPO = pathlib.Path(__file__).resolve().parents[3]
failures = []


def check(label, condition, detail=""):
    print(f"{'PASS' if condition else 'FAIL'}  {label}{(' -- ' + detail) if detail else ''}")
    if not condition:
        failures.append(label)


# --- producer vocabulary, read from the module's own annotation -------------
from deepreason.llm.repair import V6RepairTurn  # noqa: E402

hints = typing.get_type_hints(V6RepairTurn)
producer = set(typing.get_args(hints["mode"]))
check("producer Literal is exactly {initial, whole_object_syntax, patch}",
      producer == {"initial", "whole_object_syntax", "patch"}, str(sorted(producer)))

# --- checker vocabulary, read from the source line -------------------------
src = (REPO / "src/deepreason/workflow/nonconjecture_recovery.py").read_text()
match = re.search(r'mode in \{([^}]*)\}, "repair mode is invalid"', src)
checker = set(re.findall(r'"([^"]+)"', match.group(1))) if match else set()
check("checker set is exactly {patch, full}", checker == {"patch", "full"}, str(sorted(checker)))

check("the two vocabularies intersect in {'patch'} only",
      producer & checker == {"patch"}, str(sorted(producer & checker)))
check("'full' is accepted by the checker and emitted nowhere in src/",
      "full" in checker and not re.search(r'mode\s*=\s*"full"',
                                          "\n".join(p.read_text() for p in
                                                    (REPO / "src").rglob("*.py"))))
check("'whole_object_syntax' is emitted by the producer and rejected by the checker",
      "whole_object_syntax" in producer and "whole_object_syntax" not in checker)

# --- the committed records agree -------------------------------------------
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        data = json.loads(pathlib.Path(arg).read_text())
        for root in data:
            modes = {m.strip("'\"") for m in root["mode_values"]}
            check(f"{root['root'][:28]}: observed modes subset of the producer Literal",
                  modes <= producer, str(sorted(modes)))
            check(f"{root['root'][:28]}: every observed illegal mode is whole_object_syntax",
                  all(r["mode"] == "whole_object_syntax" for r in root["illegal_modes"]),
                  f"{len(root['illegal_modes'])} illegal of {root['repair_payloads']}")

print()
print("FAILURES:", failures or "none")
raise SystemExit(1 if failures else 0)
