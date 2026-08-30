#!/bin/sh
# E1-5. A differential run against the REAL system, which goes RED against the
# claim `resource_limits()["filesystem"] == "ephemeral scratch workdir"`.
#
# READ THIS BEFORE READING THE TRANSCRIPT. This is NOT a live escape. The
# language boundary refuses `open` and every other builtin at all five sandbox
# call sites (tests/test_sandbox_guard.py, the frame-walk tests), so nothing
# model-authored code can express reaches the filesystem. What is falsified is
# the STRING: it names a confinement the OS layer does not provide, so a reader
# who trusts the field over-estimates the boundary by exactly one layer.
#
# No src change is made here: P4's scope is tests and probes, and
# `verification/contained.py` is frozen surface 3. This is a finding, parked.
set -e
REPO=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$REPO"
PYTHONPATH="$REPO/src" python - <<'PY'
import subprocess, sys, tempfile, pathlib
from deepreason.verification.contained import ContainedSimulationBackend as Backend

backend = Backend(toolchain_id="t", maximum_wall_ms=20_000,
                  maximum_memory_bytes=512 * 1024 * 1024)
prefix = Backend.containment_prefix()
print("the prefix the backend actually applies :", prefix)
print("mount-namespace flag present            :", "--mount" in prefix)
print('resource_limits()["filesystem"]         :',
      repr(backend.resource_limits()["filesystem"]))

scratch = tempfile.mkdtemp(prefix="deepreason-jail-probe-")
outside = pathlib.Path(scratch).parent / "deepreason-jail-probe-marker"
probe = (
    "import json, os, pathlib, sys\n"
    "seen = pathlib.Path('/etc/hostname').read_text().strip()\n"
    "marker = pathlib.Path(sys.argv[1])\n"
    "marker.write_text('WRITTEN FROM INSIDE THE PREFIX')\n"
    "print(json.dumps({'cwd': os.getcwd(),"
    " 'read_/etc/hostname': seen,"
    " 'wrote_outside_scratch': str(marker),"
    " 'root_listing_visible': sorted(os.listdir('/'))[:6]}))\n"
)
result = subprocess.run(
    [*prefix, sys.executable, "-c", probe, str(outside)],
    cwd=scratch, capture_output=True, text=True, timeout=60, check=True,
)
print("\ninside the prefix, cwd=the scratch dir:")
print(" ", result.stdout.strip())
print("  the marker exists outside the scratch dir:", outside.exists())
print("  its contents                             :", outside.read_text())
outside.unlink()
pathlib.Path(scratch).rmdir()
print("\nVERDICT: the prefix carries --net only. `cwd` is the only confinement,")
print("and `cwd` is not a jail. The field over-claims by one layer.")
PY
