"""Mutation table for SEAM-llm-x-verification.md's crossing check.

Every import FORM the seam's prose claims to pin ("nowhere, in any form,
absolute or relative"), planted one at a time in a scratch mirror of src/.
A form that leaves the check GREEN is a hole in the pin, not a passing test.

Run from anywhere; the repo root is derived from this file's own location so
the script survives the removal of the worktree it was written in.
"""
import ast
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools"))
import docs_verify  # noqa: E402

DOC = REPO / "docs/map/SEAM-llm-x-verification.md"
doc = docs_verify.parse_text(DOC.read_text(), DOC)
matches = [(line, cmd) for line, cmd in doc.checks if "crossings(" in cmd]
assert len(matches) == 1, [line for line, _ in doc.checks]
LINE, CMD = matches[0]
print(f"# repo            {REPO}")
print(f"# check           {DOC.name}:{LINE}, {len(CMD.splitlines())} lines, read through the document's own parser")

scratch = pathlib.Path(tempfile.mkdtemp(prefix="d1-forms-"))
shutil.copytree(REPO / "src", scratch / "src", ignore=shutil.ignore_patterns("__pycache__"))
print(f"# scratch mirror  {scratch}")


def run():
    return subprocess.run(CMD, shell=True, cwd=scratch, capture_output=True, text=True, timeout=300).returncode


def probe(label, relpath, text):
    target = scratch / relpath
    existed = target.exists()
    original = target.read_text() if existed else None
    target.write_text(text)
    rc = run()
    if existed:
        target.write_text(original)
    else:
        target.unlink()
    print(f"  {label:<62} rc={rc}  {'CAUGHT (red)' if rc else 'MISSED (green)'}")
    return rc


def local(body):
    """The same import, written where a real one usually appears: inside a function."""
    return f"def _probe():\n    {body}\n    return None\n"


print(f"\n  {'[unmutated scratch mirror]':<62} rc={run()}  (0 = GREEN, as it must be)")

print("\n== REVERSE: an llm/ module naming the verification side. The prose")
print("   claims this direction is empty IN ANY FORM; each row must be red. ==")
REVERSE = [
    ("R1  from deepreason.invariants import verify_root", "from deepreason.invariants import verify_root\n"),
    ("R2  from ..invariants import verify_root", "from ..invariants import verify_root\n"),
    ("R3  import deepreason.invariants", "import deepreason.invariants\n"),
    ("R4  from deepreason import invariants", "from deepreason import invariants\n"),
    ("R5  from .. import invariants", "from .. import invariants\n"),
    ("R6  from deepreason import verification", "from deepreason import verification\n"),
    ("R7  from .. import verification", "from .. import verification\n"),
    ("R8  from deepreason import signals_read", "from deepreason import signals_read\n"),
    ("R9  from deepreason.verification import report", "from deepreason.verification import report\n"),
    ("R10 from deepreason import invariants  [function-local]", local("from deepreason import invariants")),
    ("R11 from deepreason import invariants  [in a real llm/ file]", None),
]
results = {}
for label, body in REVERSE[:-1]:
    results[label] = probe(label, "src/deepreason/llm/_probe.py", body)
firewall = (scratch / "src/deepreason/llm/firewall.py").read_text()
results[REVERSE[-1][0]] = probe(
    REVERSE[-1][0], "src/deepreason/llm/firewall.py",
    firewall + "\n\n" + local("from deepreason import invariants"),
)

print("\n== FORWARD: an eighth crossing on the verification side. The set is")
print("   pinned EXACTLY, so each row must be red. ==")
FORWARD = [
    ("F1  from deepreason.llm.packs import build_pack", "from deepreason.llm.packs import build_pack\n"),
    ("F2  from deepreason import llm", "from deepreason import llm\n"),
    ("F3  import deepreason.llm.adapter", "import deepreason.llm.adapter\n"),
]
for label, body in FORWARD:
    results[label] = probe(label, "src/deepreason/verification/_probe.py", body)

print("\n== The module-level / function-local SPLIT. The body says 'one at module")
print("   level, five inside the functions' and INDEX.md's matrix scores 1. ==")
report = scratch / "src/deepreason/verification/report.py"
report_src = report.read_text()
assert "    from deepreason.llm.firewall import route_fingerprint\n" in report_src, "fixture moved"
results["S1  report.py crossing hoisted to MODULE level"] = probe(
    "S1  report.py crossing hoisted to MODULE level",
    "src/deepreason/verification/report.py",
    "from deepreason.llm.firewall import route_fingerprint\n"
    + report_src.replace("    from deepreason.llm.firewall import route_fingerprint\n", "", 1),
)
inv = scratch / "src/deepreason/invariants.py"
inv_src = inv.read_text()
assert "from deepreason.llm.firewall import route_fingerprint\n" in inv_src, "fixture moved"
results["S2  invariants.py crossing sunk to FUNCTION level"] = probe(
    "S2  invariants.py crossing sunk to FUNCTION level",
    "src/deepreason/invariants.py",
    inv_src.replace("from deepreason.llm.firewall import route_fingerprint\n", "", 1).replace(
        "def verify_root(",
        "def _sink_probe():\n    from deepreason.llm.firewall import route_fingerprint\n"
        "    return route_fingerprint\n\n\ndef verify_root(", 1),
)

missed = sorted(label for label, rc in results.items() if rc == 0)
print(f"\n  {'[scratch mirror restored]':<62} rc={run()}")
identical = subprocess.run(
    ["diff", "-rq", "--exclude=__pycache__", str(scratch / "src"), str(REPO / "src")],
    capture_output=True, text=True)
print(f"  scratch vs repo src/: {'IDENTICAL' if identical.returncode == 0 else identical.stdout}")
status = subprocess.run(["git", "status", "--short", "src", "tests"], cwd=REPO, capture_output=True, text=True)
print(f"  git status --short src tests: {status.stdout.strip() or '(clean)'}")
shutil.rmtree(scratch)
print(f"\n  {len(results)} forms planted, {len(missed)} MISSED: {missed or 'none'}")
sys.exit(1 if missed else 0)
