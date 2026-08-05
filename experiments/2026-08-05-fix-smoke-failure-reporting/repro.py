"""Reproduction for T2: the operational smoke discards its own failure evidence.

Three concealments, demonstrated without running the full smoke (which takes
~15 minutes): one behavioural, two structural over the source's AST.

Run:  python experiments/2026-08-05-fix-smoke-failure-reporting/repro.py
"""

import ast
import importlib.util
import io
import contextlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SMOKE = ROOT / "scripts" / "wheel_operational_smoke.py"
spec = importlib.util.spec_from_file_location("_smoke_t2", SMOKE)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)
tree = ast.parse(SMOKE.read_text())

fails = 0

# --- 1. child output on timeout -------------------------------------------
print("1. child stdout/stderr on TimeoutExpired")
captured = io.StringIO()
try:
    with contextlib.redirect_stderr(captured):
        smoke._run(
            [sys.executable, "-c",
             "import sys,time; print('CHILD-STDOUT-MARKER'); "
             "print('CHILD-STDERR-MARKER', file=sys.stderr); "
             "sys.stdout.flush(); sys.stderr.flush(); time.sleep(30)"],
            cwd=ROOT, env=None, stage=smoke.STAGE_QUALIFY, timeout=2,
        )
except smoke.OperationalSmokeFailure as error:
    surfaced = captured.getvalue()
    saw_out = "CHILD-STDOUT-MARKER" in surfaced
    saw_err = "CHILD-STDERR-MARKER" in surfaced
    print("   raised: failure_kind=%s timeout=%s" % (error.failure_kind, error.timeout))
    print("   child stdout surfaced: %s" % saw_out)
    print("   child stderr surfaced: %s" % saw_err)
    if not (saw_out and saw_err):
        print("   -> CONCEALED: the child said something and the instrument dropped it")
        fails += 1
    else:
        print("   -> reported")

# --- 2. assertion message --------------------------------------------------
print()
print("2. AssertionError message in the failure path")
handlers = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ExceptHandler)
    and isinstance(n.type, ast.Name) and n.type.id == "AssertionError"
]
concealing = [h for h in handlers if h.name is None]
print("   `except AssertionError` handlers: %d" % len(handlers))
print("   ...binding the exception to a name: %d" % (len(handlers) - len(concealing)))
if concealing:
    print("   -> CONCEALED: %d handler(s) discard the message and traceback"
          % len(concealing))
    fails += 1
else:
    print("   -> reported")

# --- 3. --keep on failure --------------------------------------------------
print()
print("3. --keep preserving the temp directory on failure")
src = SMOKE.read_text()
keep_only_on_success = "if succeeded and args.keep:" in src
print("   guard `if succeeded and args.keep:` present: %s" % keep_only_on_success)
if keep_only_on_success:
    print("   -> CONCEALED: the artifacts are deleted exactly when a failure needs them")
    fails += 1
else:
    print("   -> reported")

print()
print("VERDICT: %d of 3 concealments present" % fails)
