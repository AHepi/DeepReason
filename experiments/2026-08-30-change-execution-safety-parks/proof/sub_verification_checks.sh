#!/bin/sh
# Re-run every `check:` in docs/map/SUB-verification.md -- and only those --
# using docs_verify's OWN parser and its own execution shape (shell=True,
# cwd=REPO, 300s), one at a time in a single process.
#
# Why not `python tools/docs_verify.py`: it fans out four workers over 1200+
# checks, and CLAUDE.md / dr-drive-harness §5b forbid running it beside another
# worker-spawning instrument. A sibling lane was running its own docs_verify on
# this 4-CPU box throughout; this lane's full run was killed by its 20-minute
# timeout with no result. That is recorded in DELIVERY.md rather than hidden.
# The full run is the batch integration step's, on an idle box.
REPO=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$REPO"
python - <<'PY'
import subprocess, sys
sys.path.insert(0, "tools")
import docs_verify

doc = docs_verify.parse(docs_verify.MAP_DIR / "SUB-verification.md")
print(f"SUB-verification.md: {len(doc.checks)} checks, {len(doc.errors)} parse errors")
for number, problem in doc.errors:
    print(f"  ERR {number}: {problem}")
failed = 0
for number, cmd in doc.checks:
    proc = subprocess.run(
        cmd, shell=True, cwd=docs_verify.REPO, capture_output=True, text=True,
        timeout=300,
    )
    verdict = "PASS" if proc.returncode == 0 else "FAIL"
    failed += proc.returncode != 0
    print(f"  {verdict} :{number}  {cmd.splitlines()[0][:72]}")
    if proc.returncode != 0:
        print("        " + (proc.stderr or proc.stdout).strip().splitlines()[-1][:160])
print(f"SUB-verification.md: {failed} failed")
raise SystemExit(1 if failed else 0)
PY
